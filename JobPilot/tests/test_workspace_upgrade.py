"""Regression coverage for durable linking, independent notes, and existing records."""
import json
import io
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from jobpilot import db, interview_prep
from jobpilot.resume import generate_pdf_bytes
from pypdf import PdfReader


class WorkspaceLinkTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        for target, name, value in [(db, 'DATA_DIR', root), (db, 'DB_PATH', root / 'jobpilot.db')]:
            patcher = patch.object(target, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        with patch.object(db, '_copy_legacy_database_if_needed', return_value=False):
            db.init_db()
        self.job = db.insert_opportunity({'company':'测试公司','role':'测试工程师','status':'interview'})
        app = FastAPI()
        app.include_router(interview_prep.router)
        self.client = TestClient(app)

    def test_create_links_workspace_without_changing_job_or_other_notes(self):
        before = db.get_opportunity(self.job['id'])
        response = self.client.post('/api/interview-prep', json={
            'company':'测试公司', 'role':'测试工程师', 'jd':'岗位要求', 'opportunity_id':self.job['id']})
        self.assertEqual(response.status_code, 201)
        key = response.json()['workspace']['id']
        self.assertEqual(response.json()['workspace']['opportunity_id'], self.job['id'])
        self.client.patch(f'/api/interview-prep/{key}/notes', json={'revision':0,'notes':'我的准备笔记'})
        items = {item['id']: item for item in self.client.get('/api/interview-prep').json()['items']}
        self.assertEqual(items[key]['opportunity_id'], self.job['id'])
        self.assertEqual(db.get_opportunity(self.job['id']), before)
        self.assertEqual(self.client.get(f'/api/interview-prep/{key}').json()['notes']['notes'], '我的准备笔记')

    def test_link_existing_curated_workspace_keeps_material_and_notes_unchanged(self):
        base = '/api/interview-prep/sany-bms-202610'
        initial = self.client.get(base).json()
        self.assertEqual(self.client.patch(base+'/opportunity',json={'opportunity_id':self.job['id']}).status_code,200)
        self.assertEqual(self.client.get(base).json(),initial)
        item = next(item for item in self.client.get('/api/interview-prep').json()['items'] if item['id']=='sany-bms-202610')
        self.assertEqual(item['opportunity_id'],self.job['id'])
        self.assertEqual(self.client.patch(base+'/opportunity',json={'opportunity_id':None}).status_code,200)
        item = next(item for item in self.client.get('/api/interview-prep').json()['items'] if item['id']=='sany-bms-202610')
        self.assertIsNone(item['opportunity_id'])

    def test_invalid_link_does_not_write_or_create_workspace(self):
        before = set(interview_prep._workspace_ids())
        self.assertEqual(self.client.post('/api/interview-prep',json={
            'company':'测试公司','role':'工程师','opportunity_id':999999}).status_code,404)
        self.assertEqual(self.client.patch('/api/interview-prep/sany-bms-202610/opportunity',json={'opportunity_id':999999}).status_code,404)
        self.assertEqual(self.client.patch('/api/interview-prep/nonexistent/opportunity',json={'opportunity_id':self.job['id']}).status_code,404)
        self.assertEqual(set(interview_prep._workspace_ids()),before)
        self.assertFalse((db.DATA_DIR/'private/interview-prep/opportunity-links.json').exists())


class PdfExportTests(unittest.TestCase):
    def test_chinese_resume_without_photo_preserves_plain_text(self):
        version = {'target_role':'工程师 <C++>', 'resume':{'summary':'开发 & 验证',
            'sections':[{'title':'项目经历','items':[{'title':'工具 <v2>',
                'organization':'团队 A & B','bullets':['比较 x < y，保留 <code> 文本。']}]}],
            'skills':['C++','嵌入式']}}
        content = generate_pdf_bytes({'name':'测试 & 姓名'},version)
        self.assertTrue(content.startswith(b'%PDF'))
        reader = PdfReader(io.BytesIO(content))
        self.assertEqual(len(reader.pages),1)
        extracted = reader.pages[0].extract_text()
        for value in ['测试 & 姓名','工程师 <C++>','工具 <v2>','团队 A & B','<code>']:
            self.assertIn(value,extracted)

    def test_pdf_export_has_cjk_fallback_without_system_fonts(self):
        from reportlab.pdfbase import pdfmetrics
        with patch.object(pdfmetrics,'getRegisteredFontNames',return_value=[]), patch.object(Path,'is_file',return_value=False):
            content = generate_pdf_bytes({'name':'测试姓名'},{'resume':{}})
        self.assertTrue(content.startswith(b'%PDF'))
        self.assertEqual(len(PdfReader(io.BytesIO(content)).pages),1)


if __name__=='__main__':
    unittest.main()
