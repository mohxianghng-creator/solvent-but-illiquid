"""Reported-estimate reserve P&L bridge from OBSERVED trace data, separate from latent truth."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from liquidity_model import default_params
ROOT=Path(__file__).resolve().parent

def bridge(trace,p):
    estimate0=p.median_loss*np.exp(.5*p.loss_log_sd**2)
    recover=lambda x:min(18.,.6*max(x-12.,0.))
    tp_prev=p.background_ultimate+estimate0;ri_prev=recover(estimate0)
    of_flow=100-tp_prev+ri_prev-p.facility*p.commitment_rate*p.days/260
    paid=received=0.;rows=[]
    from liquidity_model import background_due
    bgcum=np.cumsum(background_due(p))
    for row in trace.itertuples():
        t=int(row.day);paid+=row.paid_claim;received+=row.recovery
        # Total cumulative demands = paid + outstanding arrears. No hidden ultimate read.
        observed_cat=max(0.,paid+row.arrears-bgcum[t])
        estimate=max(row.posterior_mean,observed_cat)
        tp=p.background_ultimate+estimate-paid
        ri=max(0.,recover(estimate)-received)
        reserve_revision=tp-(tp_prev-row.paid_claim)
        recoverable_revision=ri-(ri_prev-row.recovery)
        of_flow+=getattr(row,'earned_income',row.income+row.restricted_income)-row.interest_accrued-row.execution_fee-reserve_revision+recoverable_revision
        of_balance=row.closing_cash+row.restricted_cash+row.liquid+row.less_liquid+row.pending_receipts+getattr(row,'income_receivable',0.)+ri-tp-row.debt
        rows.append(dict(day=t,observed_cumulative_cat=observed_cat,reported_loss_estimate=estimate,
           estimated_tp=tp,estimated_ri=ri,reserve_revision=reserve_revision,recoverable_revision=recoverable_revision,
           estimated_own_funds=of_balance,estimated_own_funds_flow=of_flow,residual=of_balance-of_flow))
        tp_prev=tp;ri_prev=ri
    return pd.DataFrame(rows)

if __name__=='__main__':
    p=default_params();rows=[]
    for name in ['rule','mpc']:
        d=bridge(pd.read_csv(ROOT/'results'/f'ledger_{name}.csv'),p);d['policy_name']=name;rows.append(d)
        if d.residual.abs().max()>1e-6:raise AssertionError('Reported estimate bridge failed')
    pd.concat(rows,ignore_index=True).to_csv(ROOT/'results/reported_reserve_bridge.csv',index=False)
    print('Report-estimate reserve and recoverable revisions reconcile without using latent ultimate.')
