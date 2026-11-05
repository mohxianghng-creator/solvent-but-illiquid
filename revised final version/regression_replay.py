"""Replay a declared deterministic subset of frozen out-of-sample paths.

This is a software regression check, not a fresh holdout or empirical validation.
Includes ordinary and adverse/discordant paths; never retunes the policies.
"""
import argparse
from dataclasses import asdict
import json
import numpy as np
import pandas as pd
from liquidity_model import ROOT, Params, Policy, default_params, generate, simulate


def replay():
    cfg=json.loads((ROOT/'results/run_config.json').read_text())
    if asdict(default_params()) != cfg['params']:
        raise ValueError('Current inputs differ from frozen experiment; rerun research explicitly')
    p=Params(**cfg['params'])
    policies=json.loads((ROOT/'results/locked_policies.json').read_text())
    frozen=pd.read_csv(ROOT/'results/test_paths.csv')
    scenarios=generate(cfg['test_n'],cfg['test_seed'],p)
    metrics=['failure','claim_failure','debt_failure','economic_cost','end_own_funds',
             'terminal_claim_arrears','distinct_late_claim','terminal_debt']
    rows=[]
    for (evaluation,name),frame in frozen.groupby(['evaluation','policy_name']):
        ids=set(frame.path_id.sort_values().iloc[[0,1,-1]].astype(int))
        ids.update(frame.loc[frame.failure==1,'path_id'].head(3).astype(int))
        # The most costly and largest late-payment paths exercise accounting tails.
        ids.add(int(frame.loc[frame.economic_cost.idxmax(),'path_id']))
        ids.add(int(frame.loc[frame.distinct_late_claim.idxmax(),'path_id']))
        for path_id in sorted(ids):
            expected=frame.loc[frame.path_id==path_id].iloc[0]
            actual=simulate(scenarios[path_id],float(expected.cash0),Policy(**policies[name]),p)
            errors={m:abs(actual[m]-float(expected[m])) for m in metrics}
            passed=all(np.isclose(actual[m],expected[m],atol=5e-9,rtol=1e-9) for m in metrics)
            rows.append(dict(evaluation=evaluation,policy_name=name,path_id=path_id,
                failure=actual['failure'],max_absolute_difference=max(errors.values()),passed=passed))
            if not passed:
                raise AssertionError(f'Frozen replay changed: {evaluation} {name} path {path_id}: {errors}')
    return pd.DataFrame(rows)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true',help='Verify without replacing published replay evidence')
    args=parser.parse_args()
    result=replay()
    if not args.check: result.to_csv(ROOT/'results/regression_replay.csv',index=False)
    print(f'{len(result)} frozen path replays passed; max difference={result.max_absolute_difference.max():.3g}')
