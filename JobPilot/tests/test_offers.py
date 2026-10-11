"""Durable Offer capture, conflict protection, attachments and independent job history."""
import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from fastapi.testclient import TestClient
from jobpilot import db
from jobpilot.main import app


class OfferTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        for p in (patch.object(db,'DATA_DIR',Path(self.tmp.name)),patch.object(db,'DB_PATH',Path(self.tmp.name)/'jobpilot.db'),patch.object(db,'BACKUP_DIR',Path(self.tmp.name)/'backups'),patch.object(db,'_copy_legacy_database_if_needed',return_value=False)):
            p.start();self.addCleanup(p.stop)
        db.init_db();self.client=TestClient(app)
        self.job=db.insert_opportunity({'company':'公司甲','role':'工程师','status':'offer','jd_text':'真实岗位要求'})
        self.payload={'company':'公司甲','role':'工程师','city':'深圳','opportunity_id':self.job['id'],'reply_deadline':'2026-10-15','details':{'monthly_base':18000,'guaranteed_months':13,'fixed_bonus':0,'monthly_allowance':0,'bonus_target':20000,'evidence':{'pay':{'status':'written','source':'Offer 第 2 页','confirmed_date':'2026-10-11'}},'custom':[{'name':'落户支持','value':'需核实','source':'HR 沟通'}]}}

    def create(self,payload=None):
        response=self.client.post('/api/offers',json=payload or self.payload)
        self.assertEqual(response.status_code,200,response.text)
        return response.json()['item']

    def test_record_edit_archive_restore_preserves_job_history_and_unknowns(self):
        original=db.get_opportunity(self.job['id']);item=self.create()
        self.assertEqual(item['details']['fixed_bonus'],0)
        self.assertIsNone(item['details']['signing_bonus'])
        self.assertEqual(item['details']['evidence']['pay']['status'],'written')
        for archived in (True,False):
            response=self.client.patch(f"/api/offers/{item['id']}",json={'revision':item['revision'],'archived':archived})
            self.assertEqual(response.status_code,200,response.text);item=response.json()['item']
            self.assertEqual(item['archived'],archived)
            self.assertEqual(item['details']['custom'][0]['name'],'落户支持')
        self.assertEqual(db.get_opportunity(self.job['id']),original)
        self.assertEqual(len(self.client.get('/api/offers').json()['items']),1)
        db.delete_opportunity(self.job['id'])
        self.assertIsNone(self.client.get(f"/api/offers/{item['id']}").json()['item']['opportunity_id'])

    def test_stale_edit_cannot_overwrite_newer_record(self):
        item=self.create()
        response=self.client.patch(f"/api/offers/{item['id']}",json={'revision':1,'city':'北京'})
        self.assertEqual(response.status_code,200)
        response=self.client.patch(f"/api/offers/{item['id']}",json={'revision':1,'city':'上海'})
        self.assertEqual(response.status_code,409)
        self.assertEqual(self.client.get(f"/api/offers/{item['id']}").json()['item']['city'],'北京')

    def test_invalid_amounts_dates_contract_time_and_duplicate_dimensions(self):
        invalid=[{'monthly_base':-1},{'monthly_base':float('inf')},{'fund_employer_pct':101},{'signing_date':'2026-02-30'},{'signing_time':'25:00'},{'signing_time':'14:00'},{'bonus_min':30000,'bonus_target':20000},{'custom':[{'name':'城市','value':'a'},{'name':'城市','value':'b'}]},{'evidence':{'wrong':{'status':'written'}}}]
        for details in invalid:
            if details.get('monthly_base')==float('inf'):
                from jobpilot.offers import OfferDetails
                with self.assertRaises(ValueError):OfferDetails.model_validate(details)
                continue
            response=self.client.post('/api/offers',json={**self.payload,'details':details})
            self.assertEqual(response.status_code,422,response.text)
        self.assertEqual(self.client.post('/api/offers',json={**self.payload,'reply_deadline':'2026-02-30'}).status_code,422)
        self.assertEqual(self.client.post('/api/offers',json={**self.payload,'company':'   '}).status_code,422)
        self.assertEqual(self.client.get('/api/offers').json()['items'],[])

    def test_attachment_download_is_scoped_and_in_database_backup(self):
        item=self.create();other=self.create({**self.payload,'company':'乙'})
        content=b'%PDF-1.4\nOffer regression test'
        response=self.client.post(f"/api/offers/{item['id']}/attachments",files={'file':('../offer.pdf',content,'application/pdf')})
        self.assertEqual(response.status_code,200,response.text);attachment=response.json()['items'][0]
        self.assertEqual(attachment['name'],'offer.pdf')
        self.assertNotIn('content',attachment)
        path=f"/api/offers/{item['id']}/attachments/{attachment['id']}"
        result=self.client.get(path)
        self.assertEqual(result.content,content)
        self.assertIn('attachment;',result.headers['content-disposition'])
        self.assertEqual(self.client.get(f"/api/offers/{other['id']}/attachments/{attachment['id']}").status_code,404)
        self.assertEqual(self.client.post(f"/api/offers/{item['id']}/attachments",files={'file':('unsafe.html',b'<script>', 'text/html')}).status_code,400)
        backup=db.backup_database()
        with sqlite3.connect(backup) as conn:
            self.assertEqual(conn.execute('SELECT content FROM offer_attachments').fetchone()[0],content)

    def test_null_patch_and_missing_link_do_not_corrupt_record(self):
        item=self.create()
        for patch_data in [{'company':None},{'status':None},{'reply_deadline':'2026-02-30'},{'details':None}]:
            response=self.client.patch(f"/api/offers/{item['id']}",json={'revision':1,**patch_data})
            self.assertEqual(response.status_code,400,response.text)
        self.assertEqual(self.client.post('/api/offers',json={**self.payload,'opportunity_id':999999}).status_code,404)
        self.assertEqual(self.client.get(f"/api/offers/{item['id']}").json()['item']['revision'],1)

    def test_reply_and_signing_calendar_follow_offer_updates_without_touching_manual_events(self):
        item=self.create({**self.payload,'details':{'signing_date':'2026-10-12','signing_time':'14:00'}})
        manual=db.insert_schedule_event({'event_type':'interview','title':'技术面','event_date':'2026-10-12'})
        rows=self.client.get('/api/schedule-events').json()['items']
        generated=[row for row in rows if row['source']=='offer']
        self.assertEqual(len(generated),2)
        signing=next(row for row in generated if row['event_type']=='signing')
        self.assertEqual(signing['company'],'公司甲')
        self.assertEqual(signing['offer_id'],item['id'])
        self.assertEqual(self.client.patch(f"/api/schedule-events/{signing['id']}",json={'event_date':'2026-10-13'}).status_code,409)
        self.assertEqual(self.client.delete(f"/api/schedule-events/{signing['id']}").status_code,409)
        self.client.patch(f"/api/offers/{item['id']}",json={'revision':1,'reply_deadline':'2026-10-16','details':{'signing_date':'2026-10-14','signing_time':'15:00'}})
        rows=self.client.get('/api/schedule-events').json()['items']
        signing_new=next(row for row in rows if row['source_key']==signing['source_key'])
        self.assertEqual(signing_new['id'],signing['id'])
        self.assertEqual(signing_new['event_date'],'2026-10-14')
        self.assertEqual(db.get_schedule_event(manual['id']),manual)
        self.client.patch(f"/api/offers/{item['id']}",json={'revision':2,'archived':True})
        rows=self.client.get('/api/schedule-events').json()['items']
        self.assertFalse(any(row['source']=='offer' for row in rows))
