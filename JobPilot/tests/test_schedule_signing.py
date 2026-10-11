"""Signing appointments use the same durable calendar path as interviews."""
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from fastapi.testclient import TestClient
from jobpilot import db
from jobpilot.main import app


class SigningScheduleTests(unittest.TestCase):
    def test_create_edit_and_read_signing_keeps_other_appointments(self):
        with TemporaryDirectory() as tmp, patch.object(db, 'DATA_DIR', Path(tmp)), patch.object(db, 'DB_PATH', Path(tmp) / 'jobpilot.db'), patch.object(db, '_copy_legacy_database_if_needed', return_value=False):
            db.init_db()
            job = db.insert_opportunity({'company': '测试公司', 'role': '工程师', 'status': 'offer'})
            client = TestClient(app)
            first = client.post('/api/schedule-events', json={'event_type': 'interview', 'title': '技术面试', 'event_date': '2026-10-10', 'opportunity_id': job['id']}).json()['item']
            created = client.post('/api/schedule-events', json={'event_type': 'signing', 'title': '确认合同与签约', 'event_date': '2026-10-12', 'event_time': '14:00', 'opportunity_id': job['id']})
            self.assertEqual(created.status_code, 200)
            saved = created.json()['item']
            updated = client.patch(f"/api/schedule-events/{saved['id']}", json={'event_type': 'signing', 'event_time': '15:00'})
            self.assertEqual(updated.status_code, 200)
            rows = {item['id']: item for item in client.get('/api/schedule-events').json()['items']}
            self.assertEqual(rows[saved['id']]['company'], '测试公司')
            self.assertEqual(rows[saved['id']]['event_type'], 'signing')
            self.assertEqual(rows[saved['id']]['event_time'], '15:00')
            self.assertEqual(rows[first['id']]['event_type'], 'interview')
            self.assertEqual(db.get_opportunity(job['id'])['status'], 'offer')
