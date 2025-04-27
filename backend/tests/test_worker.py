import sys
import types
import unittest
from unittest.mock import patch, MagicMock, AsyncMock
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
# Add dummy Worker to temporalio.worker
worker_mod = types.ModuleType('temporalio.worker')
class Worker:
    def __init__(self, *args, **kwargs):
        pass
setattr(worker_mod, 'Worker', Worker)
sys.modules['temporalio.worker'] = worker_mod
# Add dummy Client to temporalio.client
client_mod = types.ModuleType('temporalio.client')
class Client:
    def __init__(self, *args, **kwargs):
        pass
    @staticmethod
    async def connect(*args, **kwargs):
        pass
setattr(client_mod, 'Client', Client)
sys.modules['temporalio.client'] = client_mod

import importlib
worker_mod = importlib.import_module('temporals.base.worker')

class TestWorker(unittest.IsolatedAsyncioTestCase):
    async def test_run_worker(self):
        # Patch all external calls and workflow/activity registrations
        with patch('temporals.base.worker.Client.connect', new=AsyncMock()), \
             patch('temporals.base.worker.Worker') as MockWorker:
            mock_worker_instance = MockWorker.return_value
            mock_worker_instance.run = AsyncMock()
            await worker_mod.run_worker()
            MockWorker.assert_called()
            mock_worker_instance.run.assert_awaited()

if __name__ == "__main__":
    unittest.main()
