from temporalio.worker import Worker
import logging
from temporalio.client import Client

from activities import fetch_ais_number, calculate_trust_score, convert_to_prometheus_metrics
from workflow import ShipDetailsWorkflow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def run_worker():
    logger.info("Connecting to Temporal server...")
    client = await Client.connect("127.0.0.1:7234")
    logger.info("Connected to Temporal server")

    logger.info("Starting worker...")
    worker = Worker(
        client,
        task_queue="ship-processing",
        workflows=[ShipDetailsWorkflow],
        activities=[fetch_ais_number, calculate_trust_score, convert_to_prometheus_metrics],
    )

    logger.info("Worker started, waiting for tasks...")
    await worker.run()

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_worker())
