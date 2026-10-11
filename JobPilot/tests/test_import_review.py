"""Preview payloads must remain valid after the user reviews a dynamic job page."""
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from jobpilot import db
from jobpilot.main import app


class ImportReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        for p in (patch.object(db,'DATA_DIR',Path(self.tmp.name)),patch.object(db,'DB_PATH',Path(self.tmp.name)/'jobpilot.db'),patch.object(db,'_copy_legacy_database_if_needed',return_value=False),patch('jobpilot.main.enrich_with_ai',AsyncMock(return_value={})),patch('jobpilot.main.legacy_match_profile',return_value={})):
            p.start();self.addCleanup(p.stop)
        db.init_db();self.client=TestClient(app)

    def test_short_dynamic_source_saves_after_review_without_losing_raw_source(self):
        with patch('jobpilot.main.fetch_page',AsyncMock(return_value=('标题'*400,'加载中',{}))):
            preview=self.client.post('/api/opportunities/preview-url',json={'url':'https://jobs.example.com/1'}).json()
        self.assertLessEqual(len(preview['source']['title']),500)
        self.assertIn('补充岗位 JD',preview['warning'])
        payload={**preview['source'],'review':{'company':'回归测试公司','role':'工程师','jd_text':'负责嵌入式系统开发，熟悉 C++ 和实时操作系统。'}}
        saved=self.client.post('/api/opportunities/import-page',json=payload)
        self.assertEqual(saved.status_code,200,saved.text)
        item=saved.json()['item']
        self.assertEqual(item['company'],'回归测试公司')
        self.assertEqual(item['jd_text'],payload['review']['jd_text'])
        self.assertEqual(item['raw_text'],'加载中')

    def test_short_source_without_substantial_review_returns_actionable_error(self):
        for review in (None,{'jd_text':'加载中'}):
            response=self.client.post('/api/opportunities/import-page',json={'url':'https://jobs.example.com/1','text':'加载中','review':review})
            self.assertEqual(response.status_code,422)
            self.assertIn('请在岗位 JD 中粘贴',response.json()['detail'][0]['msg'])
        self.assertEqual(db.list_opportunities(),[])

    def test_huawei_personal_center_four_character_source_can_be_reviewed(self):
        url='https://career.huawei.com/cn/personal-center?pageType=myApplication&recType=CR'
        with patch('jobpilot.main.fetch_page',AsyncMock(return_value=('个人中心','个人中心',{}))):
            preview=self.client.post('/api/opportunities/preview-url',json={'url':url}).json()
        payload={**preview['source'],'review':{'company':'华为','role':'嵌入式软件开发工程师','jd_text':'负责嵌入式软件开发与调试，熟悉 C/C++ 和实时操作系统。'}}
        saved=self.client.post('/api/opportunities/import-page',json=payload)
        self.assertEqual(saved.status_code,200,saved.text)
        self.assertEqual(saved.json()['item']['raw_text'],'个人中心')
        self.assertEqual(saved.json()['item']['company'],'华为')

    def test_reimport_preserves_stage_organization_and_related_schedule(self):
        payload={'url':'https://jobs.example.com/1','text':'招聘岗位：工程师，负责硬件与软件开发。','review':{'company':'测试公司','role':'工程师','jd_text':'负责硬件软件开发，熟悉 C++。'}}
        first=self.client.post('/api/opportunities/import-page',json=payload).json()['item']
        db.update_status(first['id'],'interview')
        db.organize_opportunities([{'id':first['id'],'disposition':'later','revisit_at':'2026-10-20','disposition_note':'月底再看'}])
        event=db.insert_schedule_event({'event_type':'interview','title':'技术面','event_date':'2026-10-20','opportunity_id':first['id']})
        payload.update(text='',refresh_existing=True)
        payload['review']['jd_text']='更新要求：负责嵌入式系统开发，熟悉 C++。'
        result=self.client.post('/api/opportunities/import-page',json=payload)
        self.assertEqual(result.status_code,200,result.text)
        item=result.json()['item']
        self.assertEqual(item['status'],'interview')
        self.assertEqual(item['disposition'],'later')
        self.assertEqual(item['revisit_at'],'2026-10-20')
        self.assertEqual(db.get_schedule_event(event['id']),event)
        self.assertEqual(len(db.list_opportunities()),1)
