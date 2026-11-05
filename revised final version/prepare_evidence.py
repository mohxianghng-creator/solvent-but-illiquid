"""Prepare attributed public facts and grouped transfer diagnostics, with censored amounts."""
from pathlib import Path
import json,hashlib,csv,urllib.request
from datetime import date
import numpy as np
import pandas as pd
from scipy.optimize import least_squares
ROOT=Path(__file__).resolve().parent
TOWER='https://www.tower.co.nz/wp-content/uploads/2025/11/FINAL-FY25-TWR-Annual-Report.pdf'

def prepare():
    old=pd.read_csv(ROOT/'data/nz2023_original_snapshots.csv')
    rows=[]
    for r in old.itertuples():
        rows.append(dict(group='nz_weather_2023',event=r.event,start=r.event_start,date=r.snapshot_date,
            paid_lower=r.paid_nzd,paid_upper=r.paid_nzd,reported_cost=r.estimated_cost_at_snapshot_nzd,
            reference=r.reference_cost_dec2023_nzd,currency='NZD',precision=r.date_precision,
            source=r.source_url,quality='Attributed official table; April exact PDF directly retrieved and verified in v4' if r.snapshot_date=='2023-04-01' else 'Attributed official page table'))
    extra=[
      ('kaikoura_2016','kaikoura','2016-11-14','2017-06-30',522067833,522067833,1876800143,2270000000,'NZD','explicit_as_of','https://www.icnz.org.nz/industry/media-releases/private-insurers-paid-out-0-5-billion-kaikoura-earthquake-claims/','exact table; private-insurer perimeter excludes separately EQC-managed/offshore claims'),
      ('kaikoura_2016','kaikoura','2016-11-14','2017-11-30',1000000000,np.nan,np.nan,2270000000,'NZD','explicit_as_of','https://www.icnz.org.nz/industry/media-releases/settlements-reached-for-82-of-kaikoura-claims/','more-than paid amount; 82 percent is COUNT and is not a payment fraction'),
      ('au_flood_2022','east_coast_flood','2022-02-26','2022-05-03',575000000,585000000,3350000000,5650000000,'AUD','publication_proxy','https://insurancecouncil.com.au/resource/updated-data-shows-2022-flood-was-australias-costliest/','580m rounded; reference Nov estimated cost is lower/rounded, not ultimate'),
      ('au_flood_2022','east_coast_flood','2022-02-26','2022-06-28',1450000000,1550000000,4800000000,5650000000,'AUD','publication_proxy','https://insurancecouncil.com.au/resource/2022-flood-now-third-costliest-natural-disaster-ever/','1.5b rounded; multi-wave February-March event'),
      ('au_flood_2022','east_coast_flood','2022-02-26','2022-07-29',2000000000,np.nan,5134000000,5650000000,'AUD','publication_proxy','https://insurancecouncil.com.au/resource/2-billion-in-flood-payments-already-made-by-insurers/','more than 2b is a lower bound'),
      ('au_flood_2022','east_coast_flood','2022-02-26','2022-11-30',3535000000,3545000000,5650000000,5650000000,'AUD','publication_proxy','https://insurancecouncil.com.au/resource/three-year-weather-bill-reaches-12-3-billion/','3.54b rounded; reference reported as more than 5.65b')]
    fields=['group','event','start','date','paid_lower','paid_upper','reported_cost','reference','currency','precision','source','quality']
    for item in extra: rows.append(dict(zip(fields,item)))
    d=pd.DataFrame(rows)
    d['weeks']=(pd.to_datetime(d.date)-pd.to_datetime(d.start)).dt.days/7
    d['lower_fraction']=d.paid_lower/d.reference
    d['upper_fraction']=d.paid_upper/d.reference
    d.to_csv(ROOT/'data/payment_evidence.csv',index=False)
    def fit(frame):
        t=frame.weeks.to_numpy(); lo=frame.lower_fraction.to_numpy(); hi=frame.upper_fraction.fillna(1.).to_numpy()
        def resid(theta):
            scale,shape=np.exp(theta); pred=1-np.exp(-(t/scale)**shape)
            return np.maximum(lo-pred,0)+np.minimum(hi-pred,0)
        result=least_squares(resid,np.log([35,1.4]),bounds=(np.log([5,.3]),np.log([200,3.])))
        return dict(scale_weeks=float(np.exp(result.x[0])),shape=float(np.exp(result.x[1])))
    main=fit(d[d.group=='nz_weather_2023']) # Predeclared main timing: v3 NZ weather group only.
    checks=[]
    for group in d.group.unique():
        train=d[d.group!=group]; held=d[d.group==group]; p=fit(train)
        for row in held.itertuples():
            pred=1-np.exp(-(row.weeks/p['scale_weeks'])**p['shape'])
            hi=1. if pd.isna(row.upper_fraction) else row.upper_fraction
            distance=max(row.lower_fraction-pred,0,pred-hi)
            checks.append(dict(held_group=group,event=row.event,weeks=row.weeks,predicted=pred,
                 observed_lower=row.lower_fraction,observed_upper=hi,interval_error=distance,
                 training_groups=';'.join(sorted(train.group.unique())),**p))
    pd.DataFrame(checks).to_csv(ROOT/'results/group_heldout_payment_checks.csv',index=False)
    params={'main':main,'groups':{g:fit(d[d.group==g]) for g in ['nz_weather_2023','au_flood_2022']},
        'external_kaikoura':'Held-out support/transfer test; not fit as a two-parameter family from one exact point',
        'warning':'Retrospective reference denominators and aggregation/perimeter differences; not prospective insurer validation'}
    (ROOT/'data/timing_parameters.json').write_text(json.dumps(params,indent=2),encoding='utf-8')
    # Official report facts. All monetary figures below NZD MILLIONS, not source $000.
    financial=[
      dict(year=2025,cash=71.047,investments=389.225,restricted_png=3.7,restricted_solomon=3.8,
        lic=118.373,lic_3m=51.934,lic_3to6m=22.267,lic_6to12m=20.574,
        premiums_received=593.413,claims_and_service_paid=331.406,recoveries_received=25.197,
        operating_net=143.762,investing_net=-46.954,financing_net=-102.841,fx=1.690,
        opening_cash=75.390,deposit_rate=.0256,interest_income=16.418,total_investment_income=19.769),
      dict(year=2024,cash=75.390,investments=367.506,restricted_png=7.4,restricted_solomon=3.3,
        lic=135.527,lic_3m=62.412,lic_3to6m=25.556,lic_6to12m=22.201,
        premiums_received=560.514,claims_and_service_paid=386.791,recoveries_received=91.551,
        operating_net=145.187,investing_net=-116.568,financing_net=-16.473,fx=-2.067,
        opening_cash=65.311,deposit_rate=.0424,interest_income=17.767,total_investment_income=21.800)]
    f=pd.DataFrame(financial)
    f['fixed_interest']=[389.191,367.472]
    f['excluded_property']=f.investments-f.fixed_interest
    f['cash_bridge_residual']=f.opening_cash+f.operating_net+f.investing_net+f.financing_net+f.fx-f.cash
    f['liquid_pool']=f.cash+f.fixed_interest; f['restricted']=f.restricted_png+f.restricted_solomon
    f['accessible_cash_pct_pool']=100*(f.cash-f.restricted)/f.liquid_pool
    f['restricted_pct_pool']=100*f.restricted/f.liquid_pool
    f['lic13_pct_pool']=100*f.lic_3m/f.liquid_pool
    f['lic52_pct_pool']=100*(f.lic_3m+f.lic_3to6m+f.lic_6to12m)/f.liquid_pool
    f['source']=TOWER; f['printed_pages']='43,45,62,68,80; PDF pages +2'
    f.to_csv(ROOT/'data/tower_financial_evidence.csv',index=False)
    base=f[f.year==2025].iloc[0]; prev=f[f.year==2024].iloc[0]
    interest_proxy=base.interest_income/((base.liquid_pool+prev.liquid_pool)/2)
    # Source maturity table is DISCOUNTED. Approximate midpoint undiscounting is an
    # explicit scenario conversion, not an inferred actuarial yield curve.
    pv=np.array([51.934,22.267,20.574,14.419,4.780,3.328,1.257])
    mid=np.array([.125,.375,.75,1.5,2.5,3.5,4.5])
    nominal=pv*(1+interest_proxy)**mid
    model=dict(restricted=base.restricted_pct_pool,disclosed_accessible_cash=base.accessible_cash_pct_pool,
        initial_tp=100*nominal.sum()/base.liquid_pool,background13=100*nominal[0]/base.liquid_pool,
        background26=100*nominal[:2].sum()/base.liquid_pool,background52=100*nominal[:3].sum()/base.liquid_pool,
        source_discounted_lic=100*base.lic/base.liquid_pool,discount_conversion_rate=interest_proxy,excluded_negative_pv_bucket=-.186,
        cash_rate=base.deposit_rate,interest_proxy=interest_proxy,baseline_yield_spread=interest_proxy-base.deposit_rate,
        facility=0.,facility_reason='No facility inferred from this annual report; absence of disclosure is not proof of absence.',
        disclaimer='Scoped liquidity-pool anchors, not a replica, recommendation or validation of Tower internal policy.')
    (ROOT/'data/company_anchors.json').write_text(json.dumps(model,indent=2),encoding='utf-8')
    print('11 snapshots / 4 event labels / 3 related-event groups; Tower 2 comparative years reconciled.')
    print(json.dumps(model,indent=2))
if __name__=='__main__': prepare()
