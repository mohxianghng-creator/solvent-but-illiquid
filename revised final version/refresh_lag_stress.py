"""Release stress correction: effective planning horizon must include settlement."""
import json
from dataclasses import replace
from concurrent.futures import ProcessPoolExecutor
import pandas as pd
from liquidity_model import *
from run_study import evaluate_parallel
if __name__=='__main__':
    cfg=json.loads((ROOT/'results/run_config.json').read_text());p=replace(default_params(),settlement_days=5)
    locked=json.loads((ROOT/'results/locked_policies.json').read_text());ss=generate(cfg['diagnostic_n'],202610500,p);rows=[]
    previous=pd.read_csv(ROOT/'results/robustness.csv');previous[previous.scenario=='settlement_5'].to_csv(ROOT/'work/development_lag5_before_horizon_guard.csv',index=False)
    with ProcessPoolExecutor(max_workers=4) as pool:
        for name,values in locked.items():
            d=evaluate_parallel(pool,ss,2.,Policy(**values),p)
            rows.append(dict(scenario='settlement_5',policy_name=name,cash=2.,**aggregate(d)))
    pd.concat([previous[previous.scenario!='settlement_5'],pd.DataFrame(rows)],ignore_index=True).to_csv(ROOT/'results/robustness.csv',index=False)
    print(pd.DataFrame(rows)[['policy_name','failure_pct','mean_cost']].to_string(index=False))
