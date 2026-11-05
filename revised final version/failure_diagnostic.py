"""Mechanically choose first paired discordant path, replay and inspect forecast revision."""
from dataclasses import asdict
import json
import pandas as pd
from liquidity_model import *
def main():
    cfg=json.loads((ROOT/'results/run_config.json').read_text());p=Params(**cfg['params'])
    locked=json.loads((ROOT/'results/locked_policies.json').read_text());policies={k:Policy(**v) for k,v in locked.items()}
    d=pd.read_csv(ROOT/'results/test_paths.csv');rows=[]
    for evaluation in ['common_cash2','training_selected']:
        g=d[d.evaluation==evaluation];wide=g.pivot(index='path_id',columns='policy_name',values='failure')
        ids=wide.index[(wide.mpc==1)&(wide.rule==0)]
        if len(ids)==0:continue
        path_id=int(min(ids));scenario=generate(path_id+1,cfg['test_seed'],p)[path_id]
        for name,policy in policies.items():
            cash=float(g[g.policy_name==name].cash0.iloc[0]);log=[];observations=[]
            a=simulate(scenario,cash,policy,p,trace=log,observer=observations)
            trace=pd.DataFrame(log);trace.to_csv(ROOT/'results'/f'discordant_{evaluation}_{name}.csv',index=False)
            failed=trace.index[trace.arrears>TOL]
            first=int(failed[0]) if len(failed) else -1
            row=dict(evaluation=evaluation,selection='First sorted path ID where MPC fails and rule does not; descriptive post-test diagnosis only',policy_name=name,cash=cash,first_arrears_day=first,**a)
            if first>=p.settlement_days and first>=0:
                decision_day=first-p.settlement_days;old=observations[decision_day];now=observations[first]
                row.update(last_settlement_decision_day=decision_day,forecast_for_failure_day=old.forecast[p.settlement_days],actual_demand_on_failure_day=now.due_today,
                           current_posterior_mean=np.exp(now.posterior_mu+now.posterior_var/2),earlier_posterior_mean=np.exp(old.posterior_mu+old.posterior_var/2),
                           earlier_cash=old.cash,earlier_pending=sum(old.pending),arrears_at_first_failure=trace.loc[first,'arrears'])
            rows.append(row)
    pd.DataFrame(rows).to_csv(ROOT/'results/discordant_failure_diagnostics.csv',index=False)
    print(pd.DataFrame(rows)[['evaluation','path_id','policy_name','first_arrears_day']].to_string(index=False))
if __name__=='__main__':main()

