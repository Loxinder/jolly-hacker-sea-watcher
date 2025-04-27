import unittest
from unittest.mock import patch, MagicMock
import sys
from pydantic import BaseModel

# Minimal stub Pydantic models to satisfy FastAPI
class ReportDetails(BaseModel):
    source_account_id: str = "stub"
    timestamp: str = "stub"
    location: str = "stub"
    picture_url: str = "stub"

class EnrichedReportDetails(BaseModel):
    pass

# Patch sys.modules for all external dependencies before importing server
sys.modules['temporalio'] = MagicMock()
sys.modules['temporalio.client'] = MagicMock()
sys.modules['workflow'] = MagicMock()
# Patch shared to include our stub models
shared_mock = MagicMock()
shared_mock.ReportDetails = ReportDetails
shared_mock.EnrichedReportDetails = EnrichedReportDetails
sys.modules['shared'] = shared_mock
sys.modules['activities'] = MagicMock()
from temporals.base import server

class TestServer(unittest.TestCase):
    def setUp(self):
        # Patch dependencies and global lists
        self.patcher_initial = patch('temporals.base.server.initial_metrics', [])
        self.patcher_final = patch('temporals.base.server.final_metrics', [])
        self.mock_initial = self.patcher_initial.start()
        self.mock_final = self.patcher_final.start()

    def tearDown(self):
        self.patcher_initial.stop()
        self.patcher_final.stop()

    def test_get_metrics_empty(self):
        # Test the /metrics endpoint logic with empty metrics
        expected = (
            '# HELP ship_trust_score Trust score for ships\n'
            '# TYPE ship_trust_score gauge\n'
            '# HELP ship_ais_number_total Total number of ships with AIS numbers\n'
            '# TYPE ship_ais_number_total counter\n'
        )
        expected += '\n'.join([] + [])
        result = server.get_metrics()
        # Since get_metrics is async, run it with asyncio.run
        import asyncio
        output = asyncio.run(result)
        self.assertEqual(output, expected)

    def test_get_metrics_with_data(self):
        # Simulate some metrics
        with patch('temporals.base.server.initial_metrics', ['foo']), \
             patch('temporals.base.server.final_metrics', ['bar']):
            expected = (
                '# HELP ship_trust_score Trust score for ships\n'
                '# TYPE ship_trust_score gauge\n'
                '# HELP ship_ais_number_total Total number of ships with AIS numbers\n'
                '# TYPE ship_ais_number_total counter\n'
            )
            expected += '\n'.join(['foo', 'bar'])
            result = server.get_metrics()
            import asyncio
            output = asyncio.run(result)
            self.assertEqual(output, expected)

if __name__ == "__main__":
    unittest.main()
