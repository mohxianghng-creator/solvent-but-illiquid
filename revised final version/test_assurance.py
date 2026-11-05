"""Adversarial boundary, primary-source, pairing and integrity regression tests."""
from dataclasses import replace
import hashlib
from pathlib import Path
import shutil
import tempfile
import unittest
import numpy as np
import pandas as pd
from liquidity_model import ROOT, Policy, default_params, generate, simulate, validate
from run_study import paired
from release_integrity import seal, verify
from audit_real_data import audit, extract_company


class BoundaryTests(unittest.TestCase):
    def setUp(self):
        self.p=replace(default_params(),days=5)
        self.path=generate(1,917,self.p)[0]

    def test_all_nonfinite_parameters_rejected(self):
        for name in ('cash_rate','restricted','facility','timing_concentration','funding_rate','liquid_spread','background13'):
            for value in (np.nan,np.inf,-np.inf):
                with self.subTest(name=name,value=value), self.assertRaises(ValueError):
                    validate(replace(self.p,**{name:value}))

    def test_invalid_domain_parameters_rejected(self):
        for name,value in [('days',2.5),('settlement_days',True),('facility_draw_until',-1),
            ('liquid_spread',1.),('less_liquid_spread',1.1),('funding_rate',-.1),
            ('commitment_rate',-.01),('timing_concentration',0.),('loss_log_sd',0.),('median_loss',0.)]:
            with self.subTest(name=name),self.assertRaises(ValueError): validate(replace(self.p,**{name:value}))

    def test_invalid_policy_rejected_before_engine_runs(self):
        for policy in (Policy('typo'),Policy('rule',1.5),Policy('rule',True),Policy('rule',3,np.nan),Policy('rule',3,.9,'typo')):
            with self.subTest(policy=policy),self.assertRaises(ValueError): simulate(self.path,2.,policy,self.p)

    def test_nonfinite_cash_rejected(self):
        with self.assertRaises(ValueError): simulate(self.path,np.nan,Policy('rule'),self.p)

    def test_invalid_scenario_shapes_rejected(self):
        for name in ('reports','recovery','catastrophe_due'):
            for value in (np.zeros(4),np.zeros((5,1))):
                with self.subTest(name=name),self.assertRaises(ValueError):
                    simulate(replace(self.path,**{name:value}),2.,Policy('rule'),self.p)

    def test_cash_flow_nan_and_negative_values_rejected(self):
        for name in ('recovery','catastrophe_due'):
            for value in (np.nan,np.inf,-1.):
                arr=np.zeros(5);arr[0]=value
                with self.subTest(name=name,value=value),self.assertRaises(ValueError):
                    simulate(replace(self.path,**{name:arr}),2.,Policy('rule'),self.p)

    def test_missing_reports_valid_but_infinity_invalid(self):
        result=simulate(replace(self.path,reports=np.full(5,np.nan)),2.,Policy('rule'),self.p)
        self.assertTrue(np.isfinite(result['economic_cost']))
        with self.assertRaises(ValueError):
            simulate(replace(self.path,reports=np.full(5,np.inf)),2.,Policy('rule'),self.p)

    def test_payments_cannot_exceed_liability_stock(self):
        with self.assertRaises(ValueError):
            simulate(replace(self.path,ultimate=0.),2.,Policy('rule'),self.p)

    def test_recoveries_cannot_exceed_recovery_asset(self):
        with self.assertRaises(ValueError):
            simulate(replace(self.path,recovery=np.ones(5),true_recovery=0.),2.,Policy('rule'),self.p)

    def test_malformed_controller_actions_fail_closed(self):
        for action in ((np.nan,0,0),(np.inf,0,0),(-1,0,0),(0,0),(0,0,0,0,0)):
            with self.subTest(action=action),self.assertRaises(ValueError):
                simulate(self.path,2.,Policy('rule'),self.p,controller=lambda o,p:action)

    def test_out_of_horizon_sale_rejected(self):
        with self.assertRaises(ValueError):
            simulate(self.path,2.,Policy('rule'),self.p,
                controller=lambda o,p:(.1,0,0,0) if o.day==p.days-1 else (0,0,0,0))


class PairedExperimentTests(unittest.TestCase):
    def setUp(self):
        self.a=pd.DataFrame(dict(path_id=[10,20,30],failure=[0,1,0],economic_cost=[.1,.4,.3]))
        self.b=pd.DataFrame(dict(path_id=[10,20,30],failure=[1,0,0],economic_cost=[.2,.3,.5]))

    def test_shuffled_rows_leave_paired_inference_unchanged(self):
        self.assertEqual(paired(self.a,self.b),paired(self.a.iloc[[2,0,1]],self.b.iloc[[1,2,0]]))

    def test_duplicate_ids_rejected(self):
        with self.assertRaises(ValueError): paired(self.a,pd.concat([self.b,self.b.iloc[:1]]))

    def test_unmatched_ids_rejected(self):
        with self.assertRaises(ValueError): paired(self.a,self.b.iloc[:2])

    def test_invalid_outcomes_rejected(self):
        for column,value in [('failure',2),('economic_cost',np.nan),('path_id',np.nan)]:
            bad=self.b.copy();bad.loc[0,column]=value
            with self.subTest(column=column),self.assertRaises(ValueError): paired(self.a,bad)


class ReleaseIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=ROOT/'work',prefix='assurance_');self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        (self.root/'model.txt').write_text('baseline')
        seal(self.root)

    def test_verification_is_read_only(self):
        before=(self.root/'MANIFEST_SHA256.txt').read_bytes()
        self.assertEqual(verify(self.root),1)
        self.assertEqual(before,(self.root/'MANIFEST_SHA256.txt').read_bytes())

    def test_tamper_is_detected_without_resealing(self):
        before=(self.root/'MANIFEST_SHA256.txt').read_bytes()
        (self.root/'model.txt').write_text('changed')
        with self.assertRaises(ValueError): verify(self.root)
        self.assertEqual(before,(self.root/'MANIFEST_SHA256.txt').read_bytes())

    def test_deleted_file_detected(self):
        (self.root/'model.txt').unlink()
        with self.assertRaises(ValueError): verify(self.root)

    def test_unexpected_new_file_detected(self):
        (self.root/'unreviewed.csv').write_text('new')
        with self.assertRaises(ValueError): verify(self.root)

    def test_development_artifacts_do_not_change_release(self):
        (self.root/'work').mkdir();(self.root/'work/log.txt').write_text('new test run')
        self.assertEqual(verify(self.root),1)

    def test_unsafe_and_duplicate_paths_rejected(self):
        digest=hashlib.sha256(b'x').hexdigest()
        for entry in ('../outside','C:/outside','/outside','model.txt\n'+digest+'  model.txt'):
            (self.root/'MANIFEST_SHA256.txt').write_text(digest+'  '+entry+'\n')
            with self.subTest(entry=entry),self.assertRaises(ValueError): verify(self.root)


@unittest.skipUnless((ROOT/'sources/Tower_2025_Official.pdf').is_file(),
    'Primary-source cache absent; run fetch_sources.py, then verify_public.py --with-sources')
class PrimaryEvidenceTests(unittest.TestCase):
    def test_pdf_extraction_and_dataset_reconciliation(self):
        frame,summary=audit()
        self.assertEqual(len(frame),40)
        self.assertEqual(summary['kaikoura_source_assertions'],2)
        self.assertEqual(frame[(frame.year==2025)&(frame.field=='cash')].value.item(),71.047)

    def test_transcription_error_is_detected_against_pdf(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'work',prefix='assurance_') as name:
            root=Path(name)
            shutil.copytree(ROOT/'data',root/'data')
            shutil.copytree(ROOT/'sources',root/'sources')
            csv=root/'data/tower_financial_evidence.csv'
            frame=pd.read_csv(csv);frame.loc[0,'cash']+=1;frame.to_csv(csv,index=False)
            with self.assertRaisesRegex(ValueError,'Source mismatch'): audit(root)


if __name__=='__main__': unittest.main(verbosity=2)
