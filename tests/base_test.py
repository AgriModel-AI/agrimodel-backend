import unittest
import json
from app import create_app, db
from config import TestingConfig

class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestingConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        with self.app_context:
            db.create_all()
        
        # Stop the scheduler if running in tests
        if hasattr(self.app, "apscheduler"):
            self.app.apscheduler.shutdown(wait=False)

    def tearDown(self):
        with self.app_context:
            db.session.remove()
            db.drop_all()
        self.app_context.pop()