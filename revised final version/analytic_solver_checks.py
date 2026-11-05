"""Reproducible guarded H3 analytic-action / original LP comparison."""
from dataclasses import replace
import numpy as np
import pandas as pd
from liquidity_model import *
def main():
    rng=np.random.default_rng(338);rows=[]
    for k in range(120):
        p=replace(default_params(),liquid_income=bool(k%2))
        f=tuple(rng.uniform(0,3,3));pending=(0.,float(rng.uniform(0,.5)),float(rng.uniform(0,.5)))
        o=Observation(4,float(rng.uniform(0,4)),float(rng.uniform(.1,15)),float(rng.uniform(.1,8)),0.,pending,float(rng.uniform(0,.5)),f[0],3.,.2,1.,f)
        x=np.array(analytic_three_day(o,p));y=np.array(plan_lp(o,p))
        error=np.max(np.abs(x-y));rows.append(dict(case=k,max_action_difference=error,analytic_liquid=x[0],lp_liquid=y[0],analytic_less=x[1],lp_less=y[1],liquid_income=p.liquid_income))
        if error>1e-6:raise AssertionError((k,error,x,y))
    pd.DataFrame(rows).to_csv(ROOT/'results/analytic_h3_lp_checks.csv',index=False)
    print('120 guarded analytic actions match original two-phase LP; max difference',max(x['max_action_difference'] for x in rows))
if __name__=='__main__':main()
