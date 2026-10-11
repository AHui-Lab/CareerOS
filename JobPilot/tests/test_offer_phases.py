"""Domestic salary quotations and employment phases are facts, not inferred guarantees."""
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from fastapi.testclient import TestClient
from jobpilot import db
from jobpilot.main import app


class OfferPhaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        for p in (patch.object(db,'DATA_DIR',Path(self.tmp.name)),patch.object(db,'DB_PATH',Path(self.tmp.name)/'jobpilot.db'),patch.object(db,'BACKUP_DIR',Path(self.tmp.name)/'backups'),patch.object(db,'_copy_legacy_database_if_needed',return_value=False)):
            p.start();self.addCleanup(p.stop)
        db.init_db();self.client=TestClient(app)

    def test_average_and_unknown_discount_basis_roundtrip(self):
        details={'pay_quote_type':'annual_average','annual_reference':280000,'annual_reference_scope':'转正后同岗平均，包含绩效','pay_phases':[{'phase_type':'internship','duration_months':2,'pay_method':'fixed','monthly_amount':3000},{'phase_type':'probation','duration_months':3,'pay_method':'discount','percentage':80,'included_in_first_year':True,'agreement':'劳动合同试用期条款','evidence':{'status':'verbal','source':'HR 说明，基数尚未明确'}}]}
        response=self.client.post('/api/offers',json={'company':'测试央企','role':'工程师','details':details})
        self.assertEqual(response.status_code,200,response.text);item=response.json()['item']
        self.assertIsNone(item['details']['monthly_base'])
        self.assertIsNone(item['details']['guaranteed_annual_cash'])
        phase=item['details']['pay_phases'][1]
        self.assertIsNone(phase['discount_base_monthly'])
        self.assertEqual(phase['percentage'],80)
        self.assertEqual(phase['evidence']['source'],'HR 说明，基数尚未明确')
        reread=self.client.get(f"/api/offers/{item['id']}").json()['item']
        self.assertEqual(reread['details'],item['details'])

    def test_phase_annual_reference_is_kept_separate_from_monthly_amount(self):
        payload={'company':'见习年收入示例','role':'工程师','details':{'pay_phases':[{'phase_type':'trainee','duration_months':12,'pay_method':'annual_reference','annual_low':140000,'annual_high':170000,'annual_scope':'含绩效、津贴，固定月工资未明确','included_in_first_year':True}]}}
        response=self.client.post('/api/offers',json=payload)
        self.assertEqual(response.status_code,200,response.text)
        phase=response.json()['item']['details']['pay_phases'][0]
        self.assertIsNone(phase['monthly_amount'])
        self.assertEqual(phase['annual_low'],140000)
        self.assertEqual(phase['annual_scope'],'含绩效、津贴，固定月工资未明确')

    def test_invalid_phase_and_reference_are_rejected(self):
        details=[{'pay_quote_type':'annual_range','annual_reference_low':300000,'annual_reference_high':200000},{'pay_quote_type':'invalid'},{'pay_phases':[{'percentage':101}]},{'pay_phases':[{'start_date':'2027-01-01','end_date':'2027-06-30','duration_months':6,'included_in_first_year':True},{'start_date':'2027-04-01','end_date':'2027-09-30','duration_months':6,'included_in_first_year':True}]},{'pay_phases':[{'start_date':'2027-06-01','end_date':'2027-05-01'}]},{'pay_phases':[{'duration_months':7,'included_in_first_year':True},{'duration_months':6,'included_in_first_year':True}]}]
        for value in details:
            response=self.client.post('/api/offers',json={'company':'测试','role':'工程师','details':value})
            self.assertEqual(response.status_code,422,response.text)
        self.assertEqual(self.client.get('/api/offers').json()['items'],[])

    def test_old_fields_survive_new_phase_edit_and_new_defaults(self):
        old={'company':'旧记录','role':'工程师','details':{'monthly_base':18000,'guaranteed_months':13,'tripartite':'原三方内容','probation_pay':16000,'custom':[{'name':'落户','value':'待核'}],'evidence':{'pay':{'status':'written','source':'原 Offer'}}}}
        first=self.client.post('/api/offers',json=old).json()['item']
        details={**first['details'],'pay_phases':[{'phase_type':'probation','pay_method':'fixed','monthly_amount':16000,'duration_months':3,'included_in_first_year':True}]}
        result=self.client.patch(f"/api/offers/{first['id']}",json={'revision':1,'details':details})
        self.assertEqual(result.status_code,200,result.text)
        saved=result.json()['item']['details']
        for key in ('monthly_base','guaranteed_months','tripartite','probation_pay','custom','evidence'):self.assertEqual(saved[key],first['details'][key])
        self.assertEqual(saved['pay_phases'][0]['monthly_amount'],16000)
