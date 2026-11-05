"""V4 daily liquidity-pool engine: partial information and a shared economic objective.
No insurer replica, regulatory capital model, or calibrated default probability.
"""
from __future__ import annotations
from dataclasses import dataclass,replace,fields
from pathlib import Path
import json
from functools import lru_cache
import numpy as np
import pandas as pd
from scipy.optimize import linprog
from scipy.stats import norm,beta
ROOT=Path(__file__).resolve().parent
DAYS_YEAR=260
TOL=1e-5

@dataclass(frozen=True)
class Params:
    days:int=65
    restricted:float=1.63
    background_ultimate:float=26.5
    background13:float=11.4
    background26:float=16.4
    background52:float=21.
    cash_rate:float=.0256
    yield_spread:float=.01076
    liquid_share:float=.7
    liquid_spread:float=.0002
    less_liquid_spread:float=.003
    liquid_daily_cap:float=1.
    less_daily_cap:float=.4
    settlement_days:int=2
    facility:float=0.
    advance:float=.35
    funding_rate:float=.075
    commitment_rate:float=.002
    median_loss:float=30.
    loss_log_sd:float=.45
    report_sd:float=.55
    timing_scale:float=35.83
    timing_shape:float=1.72
    timing_concentration:float=180.
    facility_draw_until:int=65
    liquid_income:bool=True # Aggregate cash-income proxy; no-coupon-cash sensitivity is required.

@dataclass(frozen=True)
class PathData:
    path_id:int
    ultimate:float
    catastrophe_due:np.ndarray
    reports:np.ndarray
    recovery:np.ndarray
    true_recovery:float

@dataclass(frozen=True)
class Policy:
    kind:str
    horizon:int=5
    quantile:float=.9
    order:str='liquid_first'

@dataclass(frozen=True)
class Observation:
    day:int
    cash:float
    liquid:float
    less_liquid:float
    debt:float
    pending:tuple[float,...]
    arrears:float
    due_today:float
    posterior_mu:float
    posterior_var:float
    cumulative_cat_announced:float
    forecast:tuple[float,...]


def default_params():
    a=json.loads((ROOT/'data/company_anchors.json').read_text())
    t=json.loads((ROOT/'data/timing_parameters.json').read_text())['main']
    return Params(restricted=a['restricted'],background_ultimate=a['initial_tp'],background13=a['background13'],
        background26=a['background26'],background52=a['background52'],cash_rate=a['cash_rate'],
        yield_spread=a['baseline_yield_spread'],timing_scale=t['scale_weeks'],timing_shape=t['shape'])


def validate(p):
    """Reject invalid configurations before randomness, accounting or optimisation."""
    for field in fields(p):
        value = getattr(p, field.name)
        if field.name == 'liquid_income':
            if not isinstance(value, (bool, np.bool_)):
                raise ValueError('liquid_income must be boolean')
        elif not np.isscalar(value) or not np.isfinite(value):
            raise ValueError(f'{field.name} must be finite')
    for name in ('days', 'settlement_days', 'facility_draw_until'):
        value = getattr(p, name)
        if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)):
            raise ValueError(f'{name} must be an integer')
    if p.days < 1 or min(p.settlement_days, p.facility_draw_until) < 0:
        raise ValueError('Invalid horizon/lag')
    if not 0 <= p.restricted < 100 or not 0 <= p.liquid_share <= 1:
        raise ValueError('Invalid pool allocation')
    if min(p.cash_rate, p.facility, p.funding_rate, p.commitment_rate) < 0 or p.cash_rate+p.yield_spread < 0:
        raise ValueError('Invalid rates/costs')
    if not 0 <= p.liquid_spread < 1 or not 0 <= p.less_liquid_spread < 1:
        raise ValueError('Execution spreads must lie in [0,1)')
    if not 0 < p.advance < 1-p.liquid_spread:
        raise ValueError('Invalid advance')
    if min(p.liquid_daily_cap, p.less_daily_cap) < 0:
        raise ValueError('Invalid capacity')
    if min(p.report_sd, p.loss_log_sd, p.median_loss, p.timing_scale, p.timing_shape, p.timing_concentration) <= 0:
        raise ValueError('Uncertainty scales and median loss must be positive')
    if not 0 <= p.background13 <= p.background26 <= p.background52 <= p.background_ultimate:
        raise ValueError('Runoff inconsistent')


def validate_path(s, p):
    """NaN is allowed only as the explicit missing-report marker."""
    for name in ('catastrophe_due', 'reports', 'recovery'):
        arr = np.asarray(getattr(s, name), dtype=float)
        if arr.shape != (p.days,):
            raise ValueError(f'{name}: expected one-dimensional horizon {p.days}')
        if name == 'reports':
            if np.isinf(arr).any():
                raise ValueError('reports may contain finite values or NaN, not infinity')
        elif not np.isfinite(arr).all() or (arr < 0).any():
            raise ValueError(f'{name} must be finite and nonnegative')
    for name in ('ultimate', 'true_recovery'):
        value = getattr(s, name)
        if not np.isfinite(value) or value < 0:
            raise ValueError(f'{name} must be finite and nonnegative')
    if np.sum(s.catastrophe_due) > s.ultimate + 1e-7:
        raise ValueError('Scheduled catastrophe payments exceed ultimate')
    if np.sum(s.recovery) > s.true_recovery + 1e-7:
        raise ValueError('Scheduled recoveries exceed recovery asset')


def validate_policy(policy):
    if policy.kind not in ('rule', 'mpc', 'myopic'):
        raise ValueError('Unknown policy kind')
    if policy.order not in ('liquid_first', 'credit_first'):
        raise ValueError('Unknown sale order')
    if isinstance(policy.horizon, (bool, np.bool_)) or not isinstance(policy.horizon, (int, np.integer)) or policy.horizon < 1:
        raise ValueError('Policy horizon must be a positive integer')
    if not np.isfinite(policy.quantile) or not 0 < policy.quantile < 1:
        raise ValueError('Policy quantile must lie in (0,1)')


@lru_cache(maxsize=256)
def background_due(p,days=None):
    n=p.days if days is None else days
    t=np.arange(n+1)
    curve=np.interp(t,[0,65,130,260,520],[0,p.background13,p.background26,p.background52,p.background_ultimate])
    out=np.diff(curve);out.setflags(write=False);return out


def cdf(day,p):
    return 1-np.exp(-(np.maximum(np.asarray(day,dtype=float),0)/5/p.timing_scale)**p.timing_shape)


def generate(n,seed,p,report_bias=0.):
    validate(p); out=[]
    # Independent per-path and driver streams prevent a different horizon from moving future reports/loss draws.
    for j in range(n):
        streams=[np.random.default_rng(np.random.SeedSequence([seed,j,k])) for k in range(4)]
        loss=float(streams[0].lognormal(np.log(p.median_loss),p.loss_log_sd))
        # Always draw a 260-business-day path plus ultimate tail; primary and continuation have exact prefixes.
        nfull=max(260,p.days); w=np.r_[np.diff(cdf(np.arange(nfull+1),p)),1-cdf(nfull,p)]
        allocation=streams[1].dirichlet(np.maximum(w,1e-12)*p.timing_concentration)
        reports=np.full(nfull,np.nan)
        report_dates=np.arange(0,nfull,5)
        reports[report_dates]=np.log(loss)+report_bias+streams[2].normal(0,p.report_sd,len(report_dates))
        recovery=min(18.,.6*max(loss-12.,0))
        recovery_day=int(streams[3].choice([44,64,129])) # Hypothetical lag mixture, not fitted to annual cash totals.
        rec=np.zeros(nfull); rec[recovery_day]=recovery
        out.append(PathData(j,loss,loss*allocation[:p.days],reports[:p.days],rec[:p.days],recovery))
    return out


@lru_cache(maxsize=16)
def z_quantile(q):return float(norm.ppf(q))

def posterior_update(mu,var,report,sd):
    if np.isfinite(report):
        newvar=1/(1/var+1/sd**2); mu=newvar*(mu/var+report/sd**2); var=newvar
    return float(mu),float(var)


@lru_cache(maxsize=16384)
def future_envelope(scale,shape,kappa,today,h,q):
    days=np.arange(today+1,today+h+1)
    F=lambda d:1-np.exp(-(np.maximum(np.asarray(d,dtype=float),0)/5/scale)**shape)
    now=float(F(today+1));end=F(days+1)
    alpha=np.maximum(kappa*(end-now),1e-12)
    remaining=np.maximum(kappa*(1-end),1e-12)
    cumulative=beta.ppf(q,alpha,remaining)
    cumulative=np.maximum.accumulate(np.clip(cumulative,0,1))
    return tuple(np.diff(np.r_[0.,cumulative]))


def forecast(mu,var,cumulative_cat,today,p,h,q):
    # Both loss uncertainty and conditional Dirichlet timing uncertainty are priced.
    # Applying q to each is a conservative component envelope, not an exact joint q quantile.
    gross=max(cumulative_cat,float(np.exp(mu+z_quantile(q)*np.sqrt(var))))
    remaining=max(0.,gross-cumulative_cat)
    h=min(h,max(0,p.days-today-1))
    increment=np.array(future_envelope(p.timing_scale,p.timing_shape,p.timing_concentration,today,h,q))
    future=remaining*increment
    if h:future+=background_due(p)[today+1:today+h+1]
    return future


def greedy_action(o,p,policy):
    H=len(o.forecast)
    # Includes current known demands, arrears, forecast future and all dated pending receipts.
    # Conservatively allow future bond coupons after maximum possible within-window sales.
    surviving=max(0.,o.liquid-H*p.liquid_daily_cap)+max(0.,o.less_liquid-H*p.less_daily_cap)
    income_lower=np.r_[0.,np.full(max(0,H-1),surviving*(p.cash_rate+p.yield_spread)/DAYS_YEAR if p.liquid_income else 0.)]
    prefix=np.cumsum(o.forecast)-np.cumsum(np.array(o.pending[:H]))-np.cumsum(income_lower)
    required=max(0.,o.arrears+max(prefix,default=0.)-o.cash)
    sg=sc=b=0.
    if o.day+p.settlement_days>=p.days:return (0.,0.,0.,0.)
    for source in (('b','g','c') if policy.order=='credit_first' else ('g','c','b')):
        if source=='g':
            cap=min(p.liquid_daily_cap,max(0.,o.liquid-(o.debt+b)/p.advance))
            sg=min(cap,required/(1-p.liquid_spread)); required=max(0.,required-sg*(1-p.liquid_spread))
        elif source=='c':
            sc=min(p.less_daily_cap,o.less_liquid,required/(1-p.less_liquid_spread));required=max(0.,required-sc*(1-p.less_liquid_spread))
        elif o.day<p.facility_draw_until:
            b=min(required,max(0.,min(p.facility,p.advance*(o.liquid-sg))-o.debt));required-=b
    # Do not use a delayed sale to erase today's shortfall in the accounting engine.
    desired_repay=min(o.debt,max(0.,o.cash-o.arrears-max(prefix,default=0.)))
    return (sg,sc,b,desired_repay)


FIELDS=('cash','g','c','debt','sg','sc','borrow','repay','paid','arrears')

def plan_lp(o,p,return_plan=False):
    H=len(o.forecast); n=H*len(FIELDS); ix=lambda t,f:t*len(FIELDS)+FIELDS.index(f)
    eq=[]; er=[]; ub=[]; ur=[]; bounds=[(0,None)]*n
    safety=np.zeros(n); economics=np.zeros(n)
    r_cash=p.cash_rate/DAYS_YEAR if p.liquid_income else 0.; r_bond=(p.cash_rate+p.yield_spread)/DAYS_YEAR if p.liquid_income else 0.; r_debt=p.funding_rate/DAYS_YEAR
    r_asset_economic=(p.cash_rate+p.yield_spread)/DAYS_YEAR
    for t in range(H):
        def state_eq(terms,state,initial):
            row=np.zeros(n)
            for f,v in terms.items():row[ix(t,f)]+=v
            if t:row[ix(t-1,state)]-=1; rhs=0.
            else:rhs=initial
            return row,rhs
        row,rhs=state_eq({'cash':1,'borrow':-1,'repay':1,'paid':1},'cash',o.cash)
        # o.cash already contains today's income/settlements; forecast accrual starts TOMORROW.
        if t:
            row[ix(t-1,'cash')]-=r_cash
            row[ix(t-1,'g')]-=r_bond;row[ix(t-1,'c')]-=r_bond
        # Pending trade receipts are dated, not free same-day proceeds.
        if t>=p.settlement_days:
            row[ix(t-p.settlement_days,'sg')]-=(1-p.liquid_spread)*(1+r_cash if t>0 and p.settlement_days>0 else 1)
            row[ix(t-p.settlement_days,'sc')]-=(1-p.less_liquid_spread)*(1+r_cash if t>0 and p.settlement_days>0 else 1)
        rhs+=(o.pending[t] if t<len(o.pending) else 0.)*(1+r_cash if t>0 else 1)
        eq.append(row);er.append(rhs)
        for state,sale,initial in [('g','sg',o.liquid),('c','sc',o.less_liquid)]:
            row,rhs=state_eq({state:1,sale:1},state,initial);eq.append(row);er.append(rhs)
        row,rhs=state_eq({'debt':1,'borrow':-1,'repay':1},'debt',o.debt)
        if t:row[ix(t-1,'debt')]-=r_debt
        eq.append(row);er.append(rhs)
        row,rhs=state_eq({'arrears':1,'paid':1},'arrears',o.arrears)
        eq.append(row);er.append(rhs+o.forecast[t])
        row=np.zeros(n);row[ix(t,'debt')]=1;row[ix(t,'g')]=-p.advance;ub.append(row);ur.append(0.)
        bounds[ix(t,'debt')]=(0,max(p.facility,o.debt))
        bounds[ix(t,'sg')]=(0,p.liquid_daily_cap if o.day+t+p.settlement_days<p.days else 0.)
        bounds[ix(t,'sc')]=(0,p.less_daily_cap if o.day+t+p.settlement_days<p.days else 0.)
        bounds[ix(t,'borrow')]=(0,p.facility if o.day+t<p.facility_draw_until else 0.)
        # Same conservative collateral convention as the actual engine: do not sell old pledged units first.
        row=np.zeros(n);row[ix(t,'sg')]=1;row[ix(t,'borrow')]=1/p.advance
        if t:row[ix(t-1,'debt')]=(1+r_debt)/p.advance;row[ix(t-1,'g')]=-1;rhs=0.
        else:rhs=o.liquid-o.debt/p.advance
        ub.append(row);ur.append(max(0.,rhs) if not t else rhs)
        safety[ix(t,'arrears')]=1.
        economics[ix(t,'sg')]=p.liquid_spread+(1-p.liquid_spread)*r_asset_economic*max(0,p.settlement_days-1)
        economics[ix(t,'sc')]=p.less_liquid_spread+(1-p.less_liquid_spread)*r_asset_economic*max(0,p.settlement_days-1)
        if p.settlement_days>0 and t+p.settlement_days<H:
            economics[ix(t,'sg')]+=(1-p.liquid_spread)*p.yield_spread/DAYS_YEAR
            economics[ix(t,'sc')]+=(1-p.less_liquid_spread)*p.yield_spread/DAYS_YEAR
        if t:
            economics[ix(t-1,'cash')]+=p.yield_spread/DAYS_YEAR
            economics[ix(t-1,'debt')]+=r_debt
    # All revolving principal callable at the experiment horizon. No off-horizon free borrowing.
    if o.day+H==p.days:safety[ix(H-1,'debt')]=1.
    else:economics[ix(H-1,'debt')]+=r_debt*(p.days-o.day-H)
    kwargs=dict(A_eq=np.array(eq),b_eq=np.array(er),A_ub=np.array(ub),b_ub=np.array(ur),bounds=bounds,method='highs')
    phase1=linprog(safety,**kwargs)
    if not phase1.success:raise RuntimeError('Safety LP: '+phase1.message)
    kwargs['A_ub']=np.vstack([kwargs['A_ub'],safety]);kwargs['b_ub']=np.r_[kwargs['b_ub'],phase1.fun+1e-9]
    phase2=linprog(economics,**kwargs)
    if not phase2.success:raise RuntimeError('Economic LP: '+phase2.message)
    first_raw=[max(0.,float(phase2.x[ix(0,x)])) for x in ('sg','sc','borrow','repay')]
    # A revolving LP can have algebraically cancelling gross draw/repay pairs.
    # Execute NET flows: a paper refinancing round trip does not create new capacity.
    cancelled=min(first_raw[2],first_raw[3]);first_raw[2]-=cancelled;first_raw[3]-=cancelled
    first=tuple(first_raw)
    if return_plan:
        return first,pd.DataFrame([{f:phase2.x[ix(t,f)] for f in FIELDS} for t in range(H)]),dict(safety_optimum=phase1.fun,economic_objective=phase2.fun,
            equality_residual=float(np.max(np.abs(kwargs['A_eq']@phase2.x-kwargs['b_eq']))))
    return first


def analytic_three_day(o,p):
    """Exact first action for H<=3, lag2, no debt/line and ordered execution costs.
    All nonzero sales settle only on the final planning day. Lower-spread sales
    dominate higher-spread sales in both cash proceeds and lost coupon per net unit.
    AR0 is fixed; extra sales can only reduce AR2 until zero, with negligible
    positive earlier coupon loss. Return the smallest liquid-first funding amount.
    This is a local LP special case, not a global stochastic-control theorem.
    """
    H=len(o.forecast)
    if H<3:return (0.,0.,0.,0.)
    rc=p.cash_rate/260 if p.liquid_income else 0.
    rb=(p.cash_rate+p.yield_spread)/260 if p.liquid_income else 0.
    cash=max(0.,o.cash-o.arrears-o.forecast[0]);old_ar=max(0.,o.arrears+o.forecast[0]-o.cash)
    gcap=min(p.liquid_daily_cap,o.liquid);ccap=min(p.less_daily_cap,o.less_liquid)
    def final_ar(sg,sc):
        income=(o.liquid+o.less_liquid-sg-sc)*rb
        available=cash*(1+rc)+income+o.pending[1]*(1+rc)
        need=old_ar+o.forecast[1]
        ar=max(0.,need-available);c1=max(0.,available-need)
        net=sg*(1-p.liquid_spread)+sc*(1-p.less_liquid_spread)
        available=c1*(1+rc)+income+(o.pending[2]+net)*(1+rc)
        return max(0.,ar+o.forecast[2]-available)
    if final_ar(0.,0.)<=1e-12:return (0.,0.,0.,0.)
    if final_ar(gcap,0.)<=1e-12:
        lo=0.;hi=gcap
        for _ in range(38):
            mid=(lo+hi)/2
            if final_ar(mid,0.)>1e-12:lo=mid
            else:hi=mid
        return (hi,0.,0.,0.)
    if final_ar(gcap,ccap)>1e-12:return (gcap,ccap,0.,0.)
    lo=0.;hi=ccap
    for _ in range(38):
        mid=(lo+hi)/2
        if final_ar(gcap,mid)>1e-12:lo=mid
        else:hi=mid
    return (gcap,hi,0.,0.)


def choose(o,p,policy,diagnostics):
    if policy.kind=='myopic':return greedy_action(o,p,replace(policy,horizon=1))
    if policy.kind=='rule':return greedy_action(o,p,policy)
    if policy.kind!='mpc':raise ValueError(policy.kind)
    # No action is economical when current cash and dated receipts cover the entire lookahead.
    balances=o.cash+np.cumsum(o.pending[:len(o.forecast)])-o.arrears-np.cumsum(o.forecast)
    if len(balances) and balances.min()>=-1e-9 and o.debt<=1e-10 and p.yield_spread>=0:
        diagnostics['analytic_no_trade']+=1;return (0.,0.,0.,0.)
    if (len(o.forecast)<=3 and p.settlement_days==2 and p.facility==0 and o.debt<=1e-12
        and p.liquid_spread<=p.less_liquid_spread and p.yield_spread>=0 and p.cash_rate+p.yield_spread<.2
        and 1-p.less_liquid_spread>10*(p.cash_rate+p.yield_spread)/260 and abs(o.pending[0])<1e-12):
        diagnostics['analytic_h3']=diagnostics.get('analytic_h3',0)+1
        return analytic_three_day(o,p)
    diagnostics['lp_calls']+=1
    try:return plan_lp(o,p)
    except RuntimeError:
        diagnostics['lp_fallbacks']+=1
        return greedy_action(o,p,replace(policy,kind='rule'))


def simulate(s,cash0,policy,p,trace=None,observer=None,controller=None):
    validate(p)
    validate_policy(policy)
    validate_path(s, p)
    if not np.isfinite(cash0) or not 0<=cash0<=100-p.restricted:raise ValueError('Cash exceeds accessible asset budget')
    if len(s.catastrophe_due)!=p.days:raise ValueError('Scenario horizon mismatch')
    cash=float(cash0);restricted=p.restricted
    liquid=(100-restricted-cash)*p.liquid_share;less=(100-restricted-cash)*(1-p.liquid_share)
    income_receivable=0.
    debt=0.;queue=np.zeros(p.days+p.settlement_days+2);arrears=0.;cumcat=0.;paid_total=0.
    true_tp=p.background_ultimate+s.ultimate;ri=s.true_recovery
    own_flow=100-true_tp+ri
    mu=np.log(p.median_loss);var=p.loss_log_sd**2
    bg=background_due(p);cost_exec=cost_carry=cost_pending=cost_funding=0.
    initial_fee=p.facility*p.commitment_rate*p.days/DAYS_YEAR
    # Commitment fee is paid and expensed at inception, even if the facility is unused.
    cash-=initial_fee;own_flow-=initial_fee
    if cash<-1e-8:raise ValueError('Cash cannot cover committed facility fee')
    failure=False;claim_failure=False;debt_failure=False;late_unique=exposure=0.
    min_truth_of=own_flow;ledger_max=0.;cash_res_max=0.;max_collateral_gap=0.;max_post_var=0.
    diag={'lp_calls':0,'lp_fallbacks':0,'analytic_no_trade':0,'analytic_h3':0}
    errors=[];covered=[];core13={}
    for t in range(p.days):
        old_cash=cash;old_liquid=liquid;old_less=less;old_restricted=restricted;old_debt=debt;old_pending=queue.sum()
        settlement=queue[t];queue[t]=0.;cash+=settlement
        recovery=float(s.recovery[t]);cash+=recovery;ri-=recovery
        pending_open=float(queue.sum())
        # Actual economic opportunity costs: cash spread plus zero-yield pending receipts.
        carry=(cash+restricted)*p.yield_spread/DAYS_YEAR
        pending_drag=pending_open*(p.cash_rate+p.yield_spread)/DAYS_YEAR
        income=cash*p.cash_rate/DAYS_YEAR+(liquid+less)*(p.cash_rate+p.yield_spread)/DAYS_YEAR
        restricted_income=restricted*p.cash_rate/DAYS_YEAR
        earned_total=income+restricted_income
        if p.liquid_income:cash+=income;restricted+=restricted_income
        else:income_receivable+=earned_total;income=0.;restricted_income=0.
        interest=debt*p.funding_rate/DAYS_YEAR;debt+=interest
        cost_carry+=carry;cost_pending+=pending_drag;cost_funding+=interest
        mu,var=posterior_update(mu,var,float(s.reports[t]),p.report_sd)
        cat_due=float(s.catastrophe_due[t]);cumcat+=cat_due
        due=cat_due+bg[t]
        # A planning family must see a trade settle; preserve deliberately myopic diagnostic.
        effective_horizon=policy.horizon if policy.kind=='myopic' else max(policy.horizon,p.settlement_days+1)
        H=min(effective_horizon,p.days-t)
        future=forecast(mu,var,cumcat,t,p,max(0,H-1),policy.quantile)
        f=tuple([due]+future.tolist())
        pend=tuple(float(queue[t+k]) for k in range(H))
        o=Observation(t,cash,liquid,less,debt,pend,arrears,due,mu,var,cumcat,f)
        if observer is not None:observer.append(o)
        action=controller(o,p) if controller else choose(o,p,policy,diag)
        action = np.asarray(action, dtype=float)
        if action.shape not in ((3,), (4,)) or not np.isfinite(action).all() or (action < -1e-9).any():
            raise ValueError('Controller action must contain 3 or 4 finite nonnegative amounts')
        if t + p.settlement_days >= p.days and np.any(action[:2] > 1e-9):
            raise ValueError('Sale would settle outside the experiment horizon')
        sg,sc,b=action[:3]; desired_repay=max(0.,float(action[3])) if len(action)>3 else 0.
        sg=max(0.,float(sg));sc=max(0.,float(sc));b=max(0.,float(b))
        if sg>min(p.liquid_daily_cap,max(0.,liquid-debt/p.advance))+1e-6 or sc>min(p.less_daily_cap,less)+1e-6:
            raise AssertionError('Sale violates capacity/encumbrance')
        if b>max(0.,min(p.facility,p.advance*(liquid-sg))-debt)+1e-6:raise AssertionError('Unsupported draw')
        fee=sg*p.liquid_spread+sc*p.less_liquid_spread
        net=sg+sc-fee;liquid-=sg;less-=sc
        cash+=b;debt+=b
        if p.settlement_days==0:cash+=net
        else:queue[t+p.settlement_days]+=net
        cost_exec+=fee
        old_paid=min(max(cash,0.),arrears);cash-=old_paid
        new_paid=min(max(cash,0.),due);cash-=new_paid
        paid=old_paid+new_paid;new_late=due-new_paid
        arrears+=due-paid;paid_total+=paid;true_tp-=paid
        # Revolving line is callable on base breach and fully repayable at final day.
        principal_due=debt if t==p.days-1 else max(0.,debt-min(p.facility,p.advance*liquid))
        principal_paid=min(max(cash,0.),debt,max(principal_due,desired_repay));cash-=principal_paid;debt-=principal_paid
        unmet_debt=max(0.,principal_due-principal_paid)
        gap=max(0.,debt-min(p.facility,p.advance*liquid));max_collateral_gap=max(max_collateral_gap,gap)
        cf=arrears>TOL;df=unmet_debt>TOL
        failure|=cf or df;claim_failure|=cf;debt_failure|=df
        late_unique+=new_late;exposure+=arrears+unmet_debt
        of=cash+restricted+liquid+less+queue.sum()+income_receivable+ri-true_tp-debt
        own_flow+=earned_total-interest-fee
        cr=cash-(old_cash+settlement+recovery+income+b+(net if p.settlement_days==0 else 0)-paid-principal_paid)
        residual=of-own_flow
        ledger_max=max(ledger_max,abs(residual));cash_res_max=max(cash_res_max,abs(cr))
        if max(abs(cr),abs(residual))>1e-6:raise AssertionError('Independent flow ledger failure')
        if min(cash,restricted,liquid,less,true_tp,ri,debt)<-1e-6:raise AssertionError('Negative stock')
        min_truth_of=min(min_truth_of,of)
        est=np.exp(mu+.5*var);lo=np.exp(mu+(-1.6448536269514722)*np.sqrt(var));hi=np.exp(mu+1.6448536269514722*np.sqrt(var))
        errors.append(est-s.ultimate);covered.append(lo<=s.ultimate<=hi)
        if trace is not None:
            trace.append(dict(day=t,opening_cash=old_cash,settlement=settlement,recovery=recovery,income=income,
                restricted_income=restricted_income,earned_income=earned_total,income_receivable=income_receivable,liquid_sale=sg,less_sale=sc,new_draw=b,execution_fee=fee,
                paid_claim=paid,principal_paid=principal_paid,interest_accrued=interest,closing_cash=cash,
                restricted_cash=restricted,liquid=liquid,less_liquid=less,pending_receipts=queue.sum(),debt=debt,
                arrears=arrears,new_late_claim=new_late,true_tp=true_tp,ri=ri,true_own_funds=of,
                flow_own_funds=own_flow,cash_residual=cr,own_funds_residual=residual,
                posterior_mean=est,posterior_sd_log=np.sqrt(var),true_ultimate_for_validation_only=s.ultimate,
                cash_opportunity_cost=carry,pending_opportunity_cost=pending_drag))
        if t==64:core13={'core13_failure':int(failure),'core13_cost':cost_exec+cost_carry+cost_pending+cost_funding+initial_fee}
    return dict(path_id=s.path_id,cash0=cash0,policy=policy.kind,horizon=policy.horizon,quantile=policy.quantile,
        failure=int(failure),claim_failure=int(claim_failure),debt_failure=int(debt_failure),
        economic_cost=cost_exec+cost_carry+cost_pending+cost_funding+initial_fee,
        execution_cost=cost_exec,cash_opportunity_cost=cost_carry,pending_opportunity_cost=cost_pending,
        funding_cost=cost_funding,commitment_cost=initial_fee,distinct_late_claim=late_unique,
        arrears_amount_days=exposure,terminal_claim_arrears=arrears,end_cash=cash,end_restricted=restricted,
        terminal_tp=true_tp,terminal_ri=ri,terminal_debt=debt,terminal_pending=queue.sum(),terminal_income_receivable=income_receivable,
        true_min_of=min_truth_of,truth_insolvent=int(min_truth_of<0),end_own_funds=of,
        max_ledger_residual=ledger_max,max_cash_residual=cash_res_max,max_collateral_gap=max_collateral_gap,
        posterior_rmse=float(np.sqrt(np.mean(np.array(errors)**2))),posterior_90_coverage=np.mean(covered),
        **diag,**core13)


def evaluate(ss,cash,policy,p):return pd.DataFrame([simulate(s,cash,policy,p) for s in ss])


def upper_bound(k,n,alpha=.05):
    return 1. if k==n else float(beta.ppf(1-alpha,k+1,n-k))


def aggregate(d):
    return dict(n=len(d),failure_pct=100*d.failure.mean(),failure_events=int(d.failure.sum()),
       upper95_pct=100*upper_bound(int(d.failure.sum()),len(d)),mean_cost=d.economic_cost.mean(),
       mean_execution=d.execution_cost.mean(),mean_cash_drag=d.cash_opportunity_cost.mean(),
       mean_pending_drag=d.pending_opportunity_cost.mean(),mean_funding=d.funding_cost.mean(),
       mean_late_claim=d.distinct_late_claim.mean(),truth_insolvency_pct=100*d.truth_insolvent.mean(),
       max_ledger_residual=d.max_ledger_residual.max(),max_cash_residual=d.max_cash_residual.max(),
       lp_calls=int(d.lp_calls.sum()),lp_fallbacks=int(d.lp_fallbacks.sum()),analytic_h3=int(d.analytic_h3.sum()) if 'analytic_h3' in d else 0,
       posterior_rmse=d.posterior_rmse.mean(),posterior_90_coverage=d.posterior_90_coverage.mean())
