"""Same-engine, same-cost exact deterministic benchmarks; perfect information is labelled."""
from dataclasses import replace
from pathlib import Path
import numpy as np
import pandas as pd
from liquidity_model import *

def solve_exact_path(due,cash0,p):
    # Only this labelled numerical benchmark receives the true whole demand vector.
    g=(100-p.restricted-cash0)*p.liquid_share;c=(100-p.restricted-cash0)*(1-p.liquid_share)
    income=cash0*p.cash_rate/260+(g+c)*(p.cash_rate+p.yield_spread)/260
    o=Observation(0,cash0+income,g,c,0.,tuple(np.zeros(p.days)),0.,due[0],np.log(p.median_loss),p.loss_log_sd**2,0.,tuple(due))
    action,plan,info=plan_lp(o,p,True)
    scenario=PathData(0,float(sum(due)),np.asarray(due),np.full(p.days,np.nan),np.zeros(p.days),0.)
    def replay(obs,params):
        row=plan.iloc[obs.day]
        return (row.sg,row.sc,row.borrow,row.repay)
    log=[];actual=simulate(scenario,cash0,Policy('mpc',p.days),p,trace=log,controller=replay)
    trace=pd.DataFrame(log)
    # Excluded constants: today's cash carry and the common restricted-cash carry.
    restricted_cost=p.restricted*p.yield_spread/260*sum((1+p.cash_rate/260)**j for j in range(p.days))
    constant=cash0*p.yield_spread/260+restricted_cost
    reconstructed=info['economic_objective']+constant
    return plan,actual,trace,dict(**info,lp_cost_plus_constants=reconstructed,
        cost_replay_residual=actual['economic_cost']-reconstructed,
        max_cash_plan_replay_difference=float(np.max(np.abs(plan.cash.to_numpy()-trace.closing_cash.to_numpy()))),
        actual_arrears_sum=float(trace.arrears.sum()))

def main():
    p=replace(default_params(),days=12,background13=0.,background26=0.,background52=0.,background_ultimate=0.)
    rng=np.random.default_rng(9173);rows=[]
    for j in range(12):
        due=rng.gamma(.8,.6,p.days);due[:2]*=.1
        plan,actual,trace,info=solve_exact_path(due,2.,p)
        rows.append(dict(case=j,perfect_information=True,model='same v4 engine and economic objective',**info,
            payment_failure=actual['failure'],actual_cost=actual['economic_cost']))
        if j==0:
            plan.to_csv(ROOT/'results/exact_benchmark_plan.csv',index=False)
            trace.to_csv(ROOT/'results/exact_benchmark_replay.csv',index=False)
        if abs(info['cost_replay_residual'])>1e-6 or info['max_cash_plan_replay_difference']>1e-6:
            raise AssertionError('Same-model objective / flow mismatch')
    pd.DataFrame(rows).to_csv(ROOT/'results/same_model_exact_benchmark.csv',index=False)
    print('12 same-model perfect-information LPs replayed in actual engine; objective and cash agree.')
if __name__=='__main__':main()
