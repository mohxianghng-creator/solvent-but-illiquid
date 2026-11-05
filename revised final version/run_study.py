"""V4 predeclared tuning, simultaneous cash selection and independent evaluation."""
import os
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1'
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from dataclasses import asdict,replace
import json,time,sys
import numpy as np
import pandas as pd
from scipy.stats import binomtest
from liquidity_model import *
R=ROOT/'results'

def worker(arg):
    ss,cash,policy,p=arg
    return [simulate(s,cash,policy,p) for s in ss]


def evaluate_parallel(pool,ss,cash,policy,p):
    jobs=[(ss[i:i+40],cash,policy,p) for i in range(0,len(ss),40)]
    rows=[]
    for result in pool.map(worker,jobs):rows.extend(result)
    return pd.DataFrame(rows)


def save(rows,name):
    d=rows if isinstance(rows,pd.DataFrame) else pd.DataFrame(rows)
    d.to_csv(R/name,index=False,float_format='%.11g');return d


def align_pairs(a, b):
    """Match scenarios by identity; never let row order define a paired experiment."""
    required = {'path_id', 'failure', 'economic_cost'}
    for frame in (a, b):
        if not required.issubset(frame.columns) or frame.empty:
            raise ValueError('Paired comparison requires nonempty path results')
        if frame.path_id.isna().any() or frame.path_id.duplicated().any():
            raise ValueError('Paired path IDs must be nonmissing and unique')
        if not frame.failure.isin([0, 1]).all() or not np.isfinite(frame.economic_cost).all():
            raise ValueError('Invalid paired outcomes')
    if set(a.path_id) != set(b.path_id):
        raise ValueError('Paired comparisons require identical path IDs')
    return (a.sort_values('path_id').reset_index(drop=True),
            b.sort_values('path_id').reset_index(drop=True))


def paired(a,b,seed=144):
    a, b = align_pairs(a, b)
    diff=a.failure.to_numpy()-b.failure.to_numpy();cost=a.economic_cost.to_numpy()-b.economic_cost.to_numpy()
    rng=np.random.default_rng(seed);rates=[];costs=[]
    for _ in range(2000):
        ii=rng.integers(0,len(a),len(a));rates.append(diff[ii].mean());costs.append(cost[ii].mean())
    x=int(((a.failure==1)&(b.failure==0)).sum());y=int(((a.failure==0)&(b.failure==1)).sum())
    return dict(difference_pp=100*diff.mean(),ci95_low_pp=100*np.quantile(rates,.025),ci95_high_pp=100*np.quantile(rates,.975),
        rule_only_failures=x,mpc_only_failures=y,exact_p=float(binomtest(x,x+y,.5).pvalue) if x+y else 1.,
        mean_cost_difference=cost.mean(),cost_ci95_low=np.quantile(costs,.025),cost_ci95_high=np.quantile(costs,.975))


def main(train_n=1000,test_n=3000,tune_n=250,diag_n=300,workers=4):
    start=time.time();p=default_params();anchor=json.loads((ROOT/'data/company_anchors.json').read_text())
    grid=sorted(set([0.,.25,.5,1.,2.,4.,8.,12.,20.,40.,80.,100-p.restricted,anchor['disclosed_accessible_cash']]))
    config=dict(version='4.0',params=asdict(p),train_n=train_n,test_n=test_n,tune_n=tune_n,diagnostic_n=diag_n,
        tuning_seed=202610410,training_seed=202610411,test_seed=202610412,cash_grid=grid,workers=workers,
        objective='Cash drag + unsettled-receipt drag + execution + accrued finance + commitment; reliability is a constraint',
        data_role='Official aggregate events and company liquidity-pool anchors; not a Tower replica',
        design='Event-conditional preparedness, same observed information/resources; Gaussian report-only filter',
        minimum_execution_horizon='Forward families use max(tuned horizon, settlement lag + 1), truncated at experiment end; myopic diagnostic exempt',
        python=sys.version)
    (R/'run_config.json').write_text(json.dumps(config,indent=2),encoding='utf-8')
    tune=generate(tune_n,202610410,p);train=generate(train_n,202610411,p);test=generate(test_n,202610412,p)
    policies={};tuning=[];allpaths=[];screens=[];summaries=[];selected={};common={}
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for kind in ['rule','mpc']:
            trials=[]
            for H in [3,5,10]:
                for q in [.5,.9,.99]:
                    policy=Policy(kind,H,q)
                    d=evaluate_parallel(pool,tune,2.,policy,p);a=aggregate(d)
                    tuning.append(dict(**asdict(policy),**a));trials.append((a['failure_events'],a['mean_cost'],H,q))
                    print('Tune',kind,H,q,a['failure_events'],a['mean_cost'],flush=True)
            _,_,H,q=min(trials);policies[kind]=Policy(kind,H,q)
        save(tuning,'policy_tuning.csv')
        (R/'locked_policies.json').write_text(json.dumps({k:asdict(v) for k,v in policies.items()},indent=2),encoding='utf-8')
        family=len(grid)*len(policies);alpha=.05/family
        config['simultaneous_training_alpha_per_candidate']=alpha
        for name,policy in policies.items():
            print('Cash screen',name,asdict(policy),flush=True)
            candidates=[]
            for cash in grid:
                d=evaluate_parallel(pool,train,cash,policy,p);a=aggregate(d)
                upper=100*upper_bound(a['failure_events'],len(d),alpha)
                screens.append(dict(policy_name=name,cash=cash,simultaneous_upper_pct=upper,eligible=int(upper<=1.),**a))
                candidates.append((upper<=1.,a['mean_cost'],cash))
                print(' ',name,cash,a['failure_events'],a['mean_cost'],upper,flush=True)
            eligible=[x for x in candidates if x[0]]
            if not eligible:
                summaries.append(dict(policy_name=name,selected_cash=np.nan,status='No candidate passes training screen'))
            else:
                _,_,cash=min(eligible,key=lambda x:(x[1],x[2]))
                d=evaluate_parallel(pool,test,cash,policy,p);d['evaluation']='training_selected';d['policy_name']=name
                allpaths.append(d);selected[name]=d
                summaries.append(dict(policy_name=name,selected_cash=cash,status='Training constraint passed; test not used to select',**aggregate(d)))
            d=evaluate_parallel(pool,test,2.,policy,p);d['evaluation']='common_cash2';d['policy_name']=name
            allpaths.append(d);common[name]=d
        save(screens,'training_cash_screen.csv');save(summaries,'selected_policy_comparison.csv')
        save([dict(policy_name=k,cash=2.,**aggregate(v)) for k,v in common.items()],'common_cash_comparison.csv')
        save(pd.concat(allpaths,ignore_index=True),'test_paths.csv')
        contrasts=[dict(evaluation='common_cash2',**paired(common['rule'],common['mpc']))]
        if len(selected)==2:contrasts.append(dict(evaluation='training_selected',**paired(selected['rule'],selected['mpc'])))
        order=np.argsort([x['exact_p'] for x in contrasts]);running=0.
        for rank,i in enumerate(order):running=max(running,min(1.,contrasts[i]['exact_p']*(len(order)-rank)));contrasts[i]['holm_p']=running
        save(contrasts,'paired_comparisons.csv')
        # Show disclosed cash as a descriptive comparator, not company policy assessment.
        descriptive=[]
        for kind,policy in policies.items():
            d=evaluate_parallel(pool,test[:diag_n],anchor['disclosed_accessible_cash'],policy,p)
            descriptive.append(dict(policy_name=kind,cash=anchor['disclosed_accessible_cash'],**aggregate(d)))
        save(descriptive,'disclosed_cash_anchor.csv')
        print('Robustness',flush=True);rows=[]
        cases=[('settlement_0',replace(p,settlement_days=0),None),('settlement_1',replace(p,settlement_days=1),None),
          ('settlement_5',replace(p,settlement_days=5),None),('yield_spread_0.5pp',replace(p,yield_spread=.005),None),
          ('yield_spread_2pp',replace(p,yield_spread=.02),None),('capacity_half',replace(p,liquid_daily_cap=.5,less_daily_cap=.2),None),
          ('hypothetical_facility3',replace(p,facility=3.),None),('cash_fungible',replace(p,restricted=0.),None),
          ('report_bias_down30logpct',p,-.3),('report_noise_high',replace(p,report_sd=.9),None)]
        timing=json.loads((ROOT/'data/timing_parameters.json').read_text())['groups']['au_flood_2022']
        cases.append(('au_flood_timing',replace(p,timing_scale=timing['scale_weeks'],timing_shape=timing['shape']),None))
        for label,pp,bias in cases:
            ss=generate(diag_n,202610500,pp,report_bias=bias or 0.)
            for kind,policy in policies.items():
                # Same common cash; no stress-specific retuning or cherry-picked cash.
                d=evaluate_parallel(pool,ss,2.,policy,pp)
                rows.append(dict(scenario=label,policy_name=kind,cash=2.,**aggregate(d)))
        save(rows,'robustness.csv')
        print('52-week continuation',flush=True)
        pp=replace(p,days=260,facility_draw_until=65);ss=generate(diag_n,202610600,pp);tail=[];tailpaths=[]
        for kind,policy in policies.items():
            d=evaluate_parallel(pool,ss,2.,policy,pp);d['policy_name']=kind;tailpaths.append(d)
            tail.append(dict(policy_name=kind,cash=2.,core13_failure_pct=100*d.core13_failure.mean(),
                mean_terminal_tp=d.terminal_tp.mean(),mean_terminal_debt=d.terminal_debt.mean(),
                mean_terminal_arrears=d.terminal_claim_arrears.mean(),**aggregate(d)))
        save(tail,'continuation52.csv');save(pd.concat(tailpaths,ignore_index=True),'continuation_paths.csv')
        # Exogenous timing closure sensitivity: past own-model results remain unchanged.
        timing_checks=[]
        for label,pp in [('base',p),('loss_median60',replace(p,median_loss=60.)),('timing_double_speed',replace(p,timing_scale=p.timing_scale/2))]:
            ss=generate(diag_n,202610700,pp)
            for kind,policy in policies.items():
                d=evaluate_parallel(pool,ss,2.,policy,pp)
                timing_checks.append(dict(scenario=label,policy_name=kind,**aggregate(d)))
        save(timing_checks,'severity_timing_stress.csv')
        # Representative path mechanically selected by largest ultimate among first 30 test paths.
        s=max(test[:30],key=lambda x:x.ultimate)
        for kind,policy in policies.items():
            log=[];simulate(s,2.,policy,p,trace=log);save(log,'ledger_'+kind+'.csv')
    config['elapsed_seconds']=time.time()-start
    (R/'run_config.json').write_text(json.dumps(config,indent=2),encoding='utf-8')
    print('DONE',config['elapsed_seconds'],flush=True)
    print(pd.DataFrame(summaries).to_string(index=False))
if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--train',type=int,default=1000);ap.add_argument('--test',type=int,default=3000)
    ap.add_argument('--tune',type=int,default=250);ap.add_argument('--diagnostic',type=int,default=300);ap.add_argument('--workers',type=int,default=4)
    a=ap.parse_args();main(a.train,a.test,a.tune,a.diagnostic,a.workers)
