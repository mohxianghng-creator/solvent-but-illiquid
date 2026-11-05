import unittest
from dataclasses import replace
import numpy as np
from liquidity_model import *

class EconomicTests(unittest.TestCase):
    def neutral(self,**kwargs):return replace(default_params(),days=8,cash_rate=0.,yield_spread=0.,**kwargs)
    def deterministic(self,p,due=None):
        arr=np.zeros(p.days) if due is None else np.array(due,dtype=float)
        return PathData(0,arr.sum(),arr,np.full(p.days,np.nan),np.zeros(p.days),0.)
    def test_company_cash_bridge(self):
        f=pd.read_csv(ROOT/'data/tower_financial_evidence.csv')
        self.assertLess(f.cash_bridge_residual.abs().max(),1e-9)
    def test_restricted_cash_excluded(self):
        p=default_params()
        with self.assertRaises(ValueError):simulate(generate(1,3,p)[0],100,Policy('rule'),p)
    def test_cost_components_reconcile(self):
        p=default_params();a=simulate(generate(1,42,p)[0],2,Policy('mpc'),p)
        self.assertAlmostEqual(a['economic_cost'],sum(a[x] for x in ['execution_cost','cash_opportunity_cost','pending_opportunity_cost','funding_cost','commitment_cost']))
    def test_independent_flow_identity(self):
        p=default_params()
        for s in generate(10,44,p):
            for policy in [Policy('myopic',1),Policy('rule',5),Policy('mpc',5)]:
                a=simulate(s,2,policy,p)
                self.assertLess(a['max_ledger_residual'],1e-6);self.assertLess(a['max_cash_residual'],1e-6)
    def test_pending_proceeds_not_immediate_cash(self):
        p=self.neutral(settlement_days=2)
        p=replace(p,background13=0.,background26=0.,background52=0.,background_ultimate=0.)
        log=[];s=self.deterministic(p,[1,0,0,0,0,0,0,0])
        action=lambda o,p:(1.,0.,0.,0.) if o.day==0 else (0.,0.,0.,0.)
        a=simulate(s,0,Policy('rule'),p,trace=log,controller=action)
        self.assertAlmostEqual(log[0]['paid_claim'],0.)
        self.assertAlmostEqual(log[1]['paid_claim'],0.)
        self.assertGreater(log[2]['paid_claim'],0.)
        self.assertEqual(a['failure'],1)
    def test_sale_reduces_holdings_at_trade_time(self):
        p=self.neutral();log=[]
        simulate(self.deterministic(p),2,Policy('rule'),p,trace=log,controller=lambda o,p:(.2,0.,0.,0.) if o.day==0 else (0.,0.,0.,0.))
        self.assertAlmostEqual(log[0]['liquid_sale'],.2)
        self.assertGreater(log[0]['pending_receipts'],0.)
    def test_no_degenerate_capital_penalty_in_cost(self):
        p=default_params();s=generate(1,33,p)[0]
        a=simulate(s,2,Policy('rule'),p)
        self.assertNotIn('capital_penalty',a)
    def test_all_cash_has_positive_carry(self):
        p=default_params();a=simulate(generate(1,3,p)[0],100-p.restricted,Policy('rule'),p)
        self.assertGreater(a['cash_opportunity_cost'],.01);self.assertEqual(a['execution_cost'],0.)
    def test_neutral_settlement_preserves_own_funds(self):
        p=replace(self.neutral(),background13=0.,background26=0.,background52=0.,background_ultimate=0.)
        a=simulate(self.deterministic(p,[1]+[0]*7),2,Policy('rule'),p)
        self.assertAlmostEqual(a['end_own_funds'],99.)
    def test_unique_late_not_duration(self):
        p=replace(self.neutral(),background13=0.,background26=0.,background52=0.,background_ultimate=0.)
        s=self.deterministic(p,[1]+[0]*7)
        a=simulate(s,0,Policy('rule'),p,controller=lambda o,p:(0.,0.,0.,0.))
        self.assertAlmostEqual(a['distinct_late_claim'],1.)
        self.assertAlmostEqual(a['arrears_amount_days'],8.)

class ForecastTests(unittest.TestCase):
    def test_posterior_closed_form(self):
        m,v=posterior_update(0.,1.,2.,1.)
        self.assertAlmostEqual(m,1.);self.assertAlmostEqual(v,.5)
    def test_missing_report_no_information(self):
        self.assertEqual(posterior_update(1.,.2,float('nan'),.5),(1.,.2))
    def test_quantile_forecast_order(self):
        p=default_params();a=forecast(np.log(30),.3,3.,5,p,10,.5);b=forecast(np.log(30),.3,3.,5,p,10,.99)
        self.assertTrue(np.all(np.cumsum(b)>=np.cumsum(a)))
    def test_known_demands_floor(self):
        p=default_params();f=forecast(np.log(1),.01,100.,1,p,3,.5)
        np.testing.assert_allclose(f,background_due(p)[2:5])
    def test_future_reports_and_dues_do_not_change_current_observation(self):
        p=default_params();s=generate(1,20,p)[0]
        reports=s.reports.copy();reports[10:]=np.log(1000)
        dues=s.catastrophe_due.copy();dues[10:]*=.5
        other=replace(s,reports=reports,catastrophe_due=dues)
        a=[];b=[]
        simulate(s,2,Policy('mpc'),p,observer=a);simulate(other,2,Policy('mpc'),p,observer=b)
        self.assertEqual(a[:10],b[:10])
    def test_hidden_truth_not_controller_field(self):
        self.assertNotIn('ultimate',Observation.__dataclass_fields__)
        self.assertNotIn('recovery',Observation.__dataclass_fields__)
    def test_scenario_prefix_horizon_invariance(self):
        p=default_params();a=generate(2,67,p);b=generate(2,67,replace(p,days=260))
        for x,y in zip(a,b):
            np.testing.assert_array_equal(x.catastrophe_due,y.catastrophe_due[:65]);np.testing.assert_array_equal(x.reports,y.reports[:65])
    def test_parameter_validation(self):
        with self.assertRaises(ValueError):validate(replace(default_params(),yield_spread=-1.))

class PlannerTests(unittest.TestCase):
    def obs(self,**kwargs):
        values=dict(day=0,cash=2.,liquid=30.,less_liquid=10.,debt=0.,pending=(0.,)*5,arrears=0.,due_today=.3,
             posterior_mu=np.log(30),posterior_var=.2,cumulative_cat_announced=1.,forecast=(.3,)*5)
        values.update(kwargs);return Observation(**values)
    def test_lp_feasible_and_no_free_settlement(self):
        p=default_params();o=self.obs(cash=0.)
        action,plan,info=plan_lp(o,p,True)
        self.assertGreater(plan.arrears.iloc[0],0.)
        self.assertLess(info['equality_residual'],1e-7)
        self.assertEqual(action[2],0.)
    def test_safety_lexicographic(self):
        p=default_params();o=self.obs()
        _,plan,info=plan_lp(o,p,True)
        self.assertLess(info['safety_optimum'],1e-7)
        self.assertLess(plan.arrears.sum(),1e-7)
    def test_no_trade_when_already_funded(self):
        p=default_params();d={'analytic_no_trade':0,'lp_calls':0,'lp_fallbacks':0}
        a=choose(self.obs(cash=20.),p,Policy('mpc'),d)
        self.assertEqual(a,(0.,0.,0.,0.));self.assertEqual(d['lp_calls'],0)
    def test_optional_facility_post_sale_collateral(self):
        p=replace(default_params(),facility=3.);o=self.obs(cash=0.)
        a,plan,_=plan_lp(o,p,True)
        self.assertTrue((plan.debt<=p.advance*plan.g+1e-7).all())
    def test_clopper_pearson_zero(self):
        self.assertAlmostEqual(upper_bound(0,1000),1-.05**.001)


class AdditionalAssuranceTests(unittest.TestCase):
    def test_actual_cost_has_independent_return_sacrifice_oracle(self):
        p=default_params();s=generate(1,44,p)[0];log=[]
        a=simulate(s,2.,Policy('mpc',5,.99),p,trace=log)
        cash_days=sum(r['opening_cash']+r['settlement']+r['recovery']+(r['restricted_cash']/(1+p.cash_rate/260)) for r in log)
        # Restricted close balance is unwound to its pre-income amount.
        self.assertAlmostEqual(a['cash_opportunity_cost'],cash_days*p.yield_spread/260,places=8)
    def test_cumulative_timing_envelope_is_monotone_in_quantile(self):
        p=default_params()
        a=np.array(future_envelope(p.timing_scale,p.timing_shape,p.timing_concentration,50,10,.5))
        b=np.array(future_envelope(p.timing_scale,p.timing_shape,p.timing_concentration,50,10,.99))
        self.assertTrue((np.cumsum(b)>=np.cumsum(a)-1e-10).all())
    def test_observation_is_immutable(self):
        from dataclasses import FrozenInstanceError
        p=default_params();obs=[];simulate(generate(1,3,p)[0],2.,Policy('rule'),p,observer=obs)
        with self.assertRaises(FrozenInstanceError):obs[0].cash=1000.
    def test_optional_facility_actual_engine_accounting(self):
        p=replace(default_params(),facility=3.,settlement_days=5)
        for s in generate(4,31,p):
            for pol in [Policy('rule',5,.9),Policy('mpc',5,.9)]:
                a=simulate(s,2.,pol,p)
                self.assertLess(a['max_ledger_residual'],1e-6)
                self.assertGreater(a['commitment_cost'],0.)
    def test_same_model_exact_lp_replays_actual_engine(self):
        from exact_benchmark import solve_exact_path
        p=replace(default_params(),days=8,background13=0.,background26=0.,background52=0.,background_ultimate=0.)
        plan,actual,trace,info=solve_exact_path(np.array([.1,.1,.3,.8,.4,1.2,.2,.2]),2.,p)
        self.assertLess(abs(info['cost_replay_residual']),1e-6)
        self.assertLess(info['max_cash_plan_replay_difference'],1e-6)


class IncomeAvailabilityTests(unittest.TestCase):
    def test_accrued_interest_is_not_immediate_cash(self):
        p=replace(default_params(),liquid_income=False,days=8,background13=0.,background26=0.,background52=0.,background_ultimate=0.)
        s=PathData(0,0.,np.zeros(8),np.full(8,np.nan),np.zeros(8),0.)
        log=[];a=simulate(s,2.,Policy('rule'),p,trace=log)
        self.assertAlmostEqual(a['end_cash'],2.)
        self.assertGreater(a['terminal_income_receivable'],0.)
        self.assertLess(a['max_ledger_residual'],1e-6)
        self.assertTrue(all(r['income']==0. for r in log))
    def test_untradeable_bucket_is_a_valid_zero_capacity_case(self):
        p=replace(default_params(),less_daily_cap=0.)
        a=simulate(generate(1,44,p)[0],2.,Policy('mpc'),p)
        self.assertLess(a['max_ledger_residual'],1e-6)



class EconomicEndpointTests(unittest.TestCase):
    def no_claim_cost(self,spread,cash):
        p=replace(default_params(),yield_spread=spread,background13=0.,background26=0.,background52=0.,background_ultimate=0.)
        s=PathData(0,0.,np.zeros(p.days),np.full(p.days,np.nan),np.zeros(p.days),0.)
        return simulate(s,cash,Policy('rule'),p,controller=lambda o,p:(0.,0.,0.,0.))['economic_cost']
    def test_positive_spread_does_not_favour_unnecessary_cash(self):
        self.assertLess(self.no_claim_cost(.01,0.),self.no_claim_cost(.01,90.))
    def test_zero_spread_no_invented_cash_penalty(self):
        self.assertAlmostEqual(self.no_claim_cost(0.,0.),self.no_claim_cost(0.,90.))
    def test_negative_spread_cash_endpoint_is_legitimate(self):
        self.assertGreater(self.no_claim_cost(-.005,0.),self.no_claim_cost(-.005,90.))
    def test_exact_h3_case_matches_full_lp(self):
        p=default_params();rng=np.random.default_rng(337)
        for _ in range(12):
            f=tuple(rng.uniform(0,2,3));o=Observation(4,float(rng.uniform(0,3)),10.,5.,0.,(0.,.2,.1),.1,f[0],3.,.2,1.,f)
            x=np.array(analytic_three_day(o,p));y=np.array(plan_lp(o,p))
            self.assertLess(np.max(np.abs(x-y)),1e-5)

class HorizonGuardTests(unittest.TestCase):
    def test_forward_families_can_see_delayed_trade_settle(self):
        p=replace(default_params(),settlement_days=5);s=generate(1,42,p)[0]
        for kind in ['rule','mpc']:
            obs=[];simulate(s,2.,Policy(kind,3,.99),p,observer=obs)
            self.assertEqual(len(obs[0].forecast),6)
            self.assertEqual(len(obs[-1].forecast),1)

if __name__=='__main__':unittest.main(verbosity=2)
