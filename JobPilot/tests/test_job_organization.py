"""Organization is durable, atomic and independent of application history."""
import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from fastapi.testclient import TestClient
from jobpilot import db
from jobpilot.main import app


class JobOrganizationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        for p in (patch.object(db, 'DATA_DIR', Path(self.tmp.name)), patch.object(db, 'DB_PATH', Path(self.tmp.name)/'jobpilot.db'), patch.object(db, '_copy_legacy_database_if_needed', return_value=False)):
            p.start(); self.addCleanup(p.stop)
        db.init_db()
        self.client = TestClient(app)
        self.jobs = [db.insert_opportunity({'company': name, 'role':'工程师', 'status':'applied', 'jd_text':'原始要求', 'applied_at':'2026-09-01', 'note':'原始备注'}) for name in ('甲', '乙')]
        self.event = db.insert_schedule_event({'event_type':'interview','title':'技术面','event_date':'2026-10-12','opportunity_id':self.jobs[0]['id']})

    def batch(self, changes):
        return self.client.post('/api/opportunities/organize', json={'changes':changes})

    def change(self, job, disposition='later', **kwargs):
        return {'id':job['id'], 'disposition':disposition, **kwargs}

    def test_roundtrip_and_undo_preserve_history(self):
        before = {j['id']:db.get_opportunity(j['id']) for j in self.jobs}
        response = self.batch([self.change(j, revisit_at='2026-10-20', disposition_note='月底再看') for j in self.jobs])
        self.assertEqual(response.status_code,200)
        result=response.json()
        for item in result['items']:
            for field,value in before[item['id']].items():
                if field not in {*db.ORGANIZATION_FIELDS, 'updated_at'}:self.assertEqual(item[field],value,field)
        self.assertEqual(db.get_schedule_event(self.event['id']),self.event)
        expected={'disposition':'later','revisit_at':'2026-10-20','disposition_note':'月底再看'}
        undo=self.batch([{**row,'expected':expected} for row in result['before']])
        self.assertEqual(undo.status_code,200)
        self.assertEqual(db.get_opportunity(self.jobs[0]['id'])['disposition'],'')

    def test_conflict_and_missing_job_are_atomic(self):
        self.batch([self.change(self.jobs[1],'skipped')])
        response=self.batch([self.change(self.jobs[0],'closed'),self.change(self.jobs[1],'closed',expected={'disposition':'','revisit_at':'','disposition_note':''})])
        self.assertEqual(response.status_code,409)
        self.assertEqual(db.get_opportunity(self.jobs[0]['id'])['disposition'],'')
        response=self.batch([self.change(self.jobs[0],'closed'),{'id':999999,'disposition':'closed'}])
        self.assertEqual(response.status_code,404)
        self.assertEqual(db.get_opportunity(self.jobs[0]['id'])['disposition'],'')

    def test_undo_does_not_overwrite_later_organization(self):
        first=self.batch([self.change(self.jobs[0],'later')]).json()
        self.batch([self.change(self.jobs[0],'closed')])
        response=self.batch([{**first['before'][0],'expected':{'disposition':'later','revisit_at':'','disposition_note':''}}])
        self.assertEqual(response.status_code,409)
        self.assertEqual(db.get_opportunity(self.jobs[0]['id'])['disposition'],'closed')

    def test_invalid_input_is_rejected_without_writes(self):
        invalid=[[],[self.change(self.jobs[0],'bogus')],[self.change(self.jobs[0]),self.change(self.jobs[0])],[self.change(self.jobs[0],revisit_at='2026-02-30')],[self.change(self.jobs[0],'active',revisit_at='2026-10-20')]]
        for changes in invalid:
            self.assertGreaterEqual(self.batch(changes).status_code,400)
        self.assertEqual(db.get_opportunity(self.jobs[0]['id'])['disposition'],'')

    def test_migration_preserves_existing_records(self):
        with sqlite3.connect(db.DB_PATH) as conn:
            for field in db.ORGANIZATION_FIELDS:conn.execute(f'ALTER TABLE opportunities DROP COLUMN {field}')
        db.init_db();db.init_db()
        for original in self.jobs:
            current=db.get_opportunity(original['id'])
            self.assertEqual(current['company'],original['company'])
            self.assertEqual(current['status'],'applied')
            self.assertEqual(current['disposition'],'')
