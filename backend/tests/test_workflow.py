import sys
import types
import unittest
from unittest.mock import patch, AsyncMock, MagicMock
from pydantic import BaseModel

# Create a real in-memory shared module with minimal stubs
shared_mod = types.ModuleType('shared')
class ReportDetails(BaseModel):
    source_account_id: str = "stub"
    timestamp: str = "stub"
    latitude: float = 0.0
    longitude: float = 0.0
    picture_url: str = "stub"
    vessel_registry: str = None
class EnrichedReportDetails(ReportDetails):
    report_number: str = None
    trust_score: float = None
    ais_neighbours: list = None
    visibility: int = 1
setattr(shared_mod, 'ReportDetails', ReportDetails)
setattr(shared_mod, 'EnrichedReportDetails', EnrichedReportDetails)
sys.modules['shared'] = shared_mod

# Patch only the essential external dependencies
sys.modules['temporalio'] = types.ModuleType('temporalio')
temporalio_workflow_mod = types.ModuleType('temporalio.workflow')
def no_op_decorator(f):
    return f
temporalio_workflow_mod.defn = no_op_decorator
temporalio_workflow_mod.run = no_op_decorator
temporalio_workflow_mod.query = no_op_decorator
sys.modules['temporalio.workflow'] = temporalio_workflow_mod
# Add a dummy RetryPolicy to temporalio.common
common_mod = types.ModuleType('temporalio.common')
class RetryPolicy:
    def __init__(self, *args, **kwargs):
        pass
setattr(common_mod, 'RetryPolicy', RetryPolicy)
sys.modules['temporalio.common'] = common_mod

import importlib
workflow_mod = importlib.import_module('temporals.base.workflow')

class TestReportDetailsWorkflow(unittest.TestCase):
    def setUp(self):
        self.workflow = workflow_mod.ReportDetailsWorkflow()

    def test_get_metrics_empty(self):
        # Should return empty string if no metrics
        self.assertEqual(self.workflow.get_metrics(), "")

    def test_get_metrics_with_data(self):
        self.workflow._metrics = ['foo', 'bar']
        expected = (
            '# HELP ship_trust_score Trust score for ships\n'
            '# TYPE ship_trust_score gauge\n'
            '# HELP ship_report_number_total Total number of ships with AIS numbers\n'
            '# TYPE ship_report_number_total counter\n'
        ) + 'foo\nbar'
        self.assertEqual(self.workflow.get_metrics(), expected)

    # The run method is async and depends on many activities; we can only test it with heavy patching or integration tests

if __name__ == "__main__":
    unittest.main()
