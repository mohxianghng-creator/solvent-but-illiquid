"""Verify the public model/results package; raw-source assurance is an explicit extra mode."""
import argparse, json, subprocess, sys, os
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--with-sources',action='store_true',help='Require all frozen sources and execute their semantic/hash checks')
    args=ap.parse_args()
    os.environ['PYTHONDONTWRITEBYTECODE']='1'
    work=ROOT/'work';work.mkdir(exist_ok=True)
    def run(*command,log=None):
        result=subprocess.run([sys.executable,'-B',*command],cwd=ROOT,text=True,capture_output=True)
        if log:(work/log).write_text(result.stdout+result.stderr,encoding='utf-8')
        print(result.stdout,end='')
        if result.returncode:
            print(result.stderr);raise SystemExit(result.returncode)
    run('release_integrity.py')
    if args.with_sources:run('audit_real_data.py','--check')
    run('-m','unittest','discover','-p','test*.py','-v',log='tests.log')
    print((work/'tests.log').read_text(encoding='utf-8').split('----------------------------------------------------------------------')[-1].strip())
    run('regression_replay.py','--check')
    import numpy as np
    import pandas as pd
    from liquidity_model import aggregate,upper_bound,default_params
    from dataclasses import asdict
    cfg=json.loads((ROOT/'results/run_config.json').read_text())
    if cfg['params']!=asdict(default_params()):raise ValueError('Source mapping differs from experiment')
    paths=pd.read_csv(ROOT/'results/test_paths.csv')
    for evaluation,filename in [('training_selected','selected_policy_comparison.csv'),('common_cash2','common_cash_comparison.csv')]:
        saved=pd.read_csv(ROOT/'results'/filename)
        for row in saved.itertuples():
            frame=paths[(paths.evaluation==evaluation)&(paths.policy_name==row.policy_name)]
            if frame.path_id.duplicated().any() or len(frame)!=cfg['test_n']:raise ValueError('Invalid scenario identities')
            actual=aggregate(frame)
            for name in ['failure_events','failure_pct','upper95_pct','mean_cost']:
                if not np.isclose(actual[name],getattr(row,name),rtol=1e-8,atol=1e-8):raise ValueError(f'Summary mismatch: {name}')
    screen=pd.read_csv(ROOT/'results/training_cash_screen.csv')
    bounds=np.array([100*upper_bound(int(r.failure_events),int(r.n),.05/len(screen)) for r in screen.itertuples()])
    if not np.allclose(bounds,screen.simultaneous_upper_pct,rtol=1e-8,atol=1e-8):raise ValueError('Training bounds differ')
    if not np.array_equal(screen.eligible.to_numpy(),(bounds<=1).astype(int)):raise ValueError('Training classifications differ')
    for row in pd.read_csv(ROOT/'results/selected_policy_comparison.csv').itertuples():
        candidates=screen[(screen.policy_name==row.policy_name)&(screen.eligible==1)].sort_values(['mean_cost','cash'])
        if not np.isclose(candidates.iloc[0].cash,row.selected_cash):raise ValueError('Training-selected cash differs')
    components=['execution_cost','cash_opportunity_cost','pending_opportunity_cost','funding_cost','commitment_cost']
    if not np.allclose(paths.economic_cost,paths[components].sum(axis=1),atol=1e-8):raise ValueError('Cost reconciliation failed')
    print('Published summaries, simultaneous training screen, selected cash and cost arithmetic agree.')
    run('release_integrity.py')
    print('PASS: '+('model/results and full cached primary-source audit' if args.with_sources else 'model/results package; primary-source audit NOT requested (two source tests skip if cache absent)'))

if __name__=='__main__':main()
