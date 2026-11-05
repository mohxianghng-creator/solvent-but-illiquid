"""Extra falsification checks: filter/forecast coverage, concealed severity drift and discount mapping."""
from dataclasses import replace
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import json
import numpy as np
import pandas as pd
from liquidity_model import *

def coverage_one(arg):
    s,p,policy=arg;obs=[];a=simulate(s,2.,policy,p,observer=obs)
    bg=background_due(p);windows=[];prefix_windows=[]
    for o in obs:
        h=len(o.forecast)-1
        if h:
            actual_daily=s.catastrophe_due[o.day+1:o.day+1+h]+bg[o.day+1:o.day+1+h]
            actual=actual_daily.sum();predicted=sum(o.forecast[1:]);windows.append(actual<=predicted+1e-10)
            prefix_windows.append(bool(np.all(np.cumsum(actual_daily)<=np.cumsum(o.forecast[1:])+1e-10)))
    return dict(path_id=s.path_id,coverage=np.mean(windows),all_prefix_window_coverage=np.mean(prefix_windows),any_window_breach=int(not all(windows)),any_prefix_breach=int(not all(prefix_windows)),posterior_coverage=a['posterior_90_coverage'],lp_fallbacks=a['lp_fallbacks'])

def main(n=300):
    p=default_params();locked=json.loads((ROOT/'results/locked_policies.json').read_text());policies={k:Policy(**v) for k,v in locked.items()}
    rows=[];parts=[];rng=np.random.default_rng(36618)
    ss=generate(n,202610810,p)
    with ProcessPoolExecutor(max_workers=4) as pool:
        for name,policy in policies.items():
            d=pd.DataFrame(pool.map(coverage_one,[(s,p,policy) for s in ss],chunksize=15));d['policy_name']=name;parts.append(d)
            boot=np.array([d.coverage.to_numpy()[rng.integers(0,len(d),len(d))].mean() for _ in range(2000)])
            rows.append(dict(policy_name=name,paths=n,forecast_horizon=policy.horizon,component_quantile=policy.quantile,
                mean_window_coverage=d.coverage.mean(),path_cluster_ci95_low=np.quantile(boot,.025),path_cluster_ci95_high=np.quantile(boot,.975),
                report_posterior_90_coverage=d.posterior_coverage.mean(),mean_all_prefix_window_coverage=d.all_prefix_window_coverage.mean(),
                paths_with_any_window_breach_pct=100*d.any_window_breach.mean(),paths_with_any_prefix_breach_pct=100*d.any_prefix_breach.mean(),
                any_prefix_breach_upper95_pct=100*upper_bound(int(d.any_prefix_breach.sum()),len(d))))
        pd.DataFrame(rows).to_csv(ROOT/'results/forecast_coverage.csv',index=False)
        pd.concat(parts,ignore_index=True).to_csv(ROOT/'results/forecast_coverage_paths.csv',index=False)
    # Unlike the known high-severity case, the controller keeps its BASE prior here.
    diagnostics=[]
    for label,policy in [('fixed_myopic',Policy('myopic',1,.5)),('fixed_buffer5_q90',Policy('rule',5,.9))]:
        z=evaluate(ss,2.,policy,p);diagnostics.append(dict(diagnostic_rule=label,cash=2.,**aggregate(z)))
    pd.DataFrame(diagnostics).to_csv(ROOT/'results/fixed_rule_diagnostics.csv',index=False)
    hidden=generate(n,202610811,replace(p,median_loss=60.))
    stress=[]
    for name,policy in policies.items():
        d=evaluate(hidden,2.,policy,p)
        stress.append(dict(scenario='hidden_loss_prior_drift_30_to60',policy_name=name,**aggregate(d)))
    pd.DataFrame(stress).to_csv(ROOT/'results/hidden_prior_stress.csv',index=False)
    extra=[]
    for label,pp in [('income_accrued_not_available',replace(p,liquid_income=False)),('less_bucket_untradeable',replace(p,less_daily_cap=0.)),('liquid_capacity_double',replace(p,liquid_daily_cap=2.))]:
        ss=generate(n,202610812,pp)
        for name,policy in policies.items():
            d=evaluate(ss,2.,policy,pp)
            extra.append(dict(scenario=label,policy_name=name,**aggregate(d)))
    pd.DataFrame(extra).to_csv(ROOT/'results/availability_sensitivities.csv',index=False)
    hidden_timing=[]
    for concentration in [45.,720.]:
        truth=generate(n,202610813,replace(p,timing_concentration=concentration))
        for name,policy in policies.items():
            d=evaluate(truth,2.,policy,p)
            hidden_timing.append(dict(truth_timing_concentration=concentration,controller_timing_concentration=p.timing_concentration,policy_name=name,**aggregate(d)))
    pd.DataFrame(hidden_timing).to_csv(ROOT/'results/hidden_timing_stress.csv',index=False)
    family=len(json.loads((ROOT/'results/run_config.json').read_text())['cash_grid'])*2
    sizes=[]
    for target in [.01,.005,.001]:
        sizes.append(dict(failure_target=target,candidate_family=family,zero_event_training_n_required=int(np.ceil(np.log(.05/family)/np.log(1-target))),
           zero_event_single_test_n_required=int(np.ceil(np.log(.05)/np.log(1-target))),model_error_covered=False))
    pd.DataFrame(sizes).to_csv(ROOT/'results/risk_sample_size_requirements.csv',index=False)


    # Discount conversion uncertainty: keep source PV facts intact and report nominal transformations.
    pv=np.array([51.934,22.267,20.574,14.419,4.780,3.328,1.257]);mid=np.array([.125,.375,.75,1.5,2.5,3.5,4.5])
    denom=460.238;rows=[]
    for rate in [0.,.0256,.03635920717528513,.05]:
        nominal=pv*(1+rate)**mid
        rows.append(dict(scenario_conversion_rate=rate,nominal_background_ultimate=100*nominal.sum()/denom,
                        nominal_13weeks=100*nominal[0]/denom,nominal_52weeks=100*nominal[:3].sum()/denom,
                        excluded_negative_pv_bucket=-.186,not_an_IFRS_reserve_reconstruction=True))
    pd.DataFrame(rows).to_csv(ROOT/'results/discount_mapping_sensitivity.csv',index=False)
    # Economic endpoint sanity without claims: do not force an interior answer.
    endpoint=[]
    for spread in [-.005,0.,.005,.02]:
        pp=replace(p,yield_spread=spread,background_ultimate=0.,background13=0.,background26=0.,background52=0.)
        scenario=PathData(0,0.,np.zeros(pp.days),np.full(pp.days,np.nan),np.zeros(pp.days),0.)
        for cash in [0.,2.,20.,100-pp.restricted]:
            result=simulate(scenario,cash,Policy('rule'),pp,controller=lambda o,p:(0.,0.,0.,0.))
            endpoint.append(dict(yield_spread=spread,cash=cash,economic_cost=result['economic_cost']))
    pd.DataFrame(endpoint).to_csv(ROOT/'results/economic_endpoint_sanity.csv',index=False)
    print('Forecast coverage uses path clusters, not falsely independent daily windows. Hidden-prior stress retained.')
if __name__=='__main__':main()
