from temporalio.worker import Worker
import logging
from temporalio.client import Client
import os
from dotenv import load_dotenv

from activities import assign_report_number, calculate_trust_score, calculate_visibility, find_ais_neighbours, convert_to_prometheus_metrics, llm_enrich
from workflow import ReportDetailsWorkflow

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Check if OpenAI API key is loaded
api_key = os.environ.get("OPENAI_API_KEY")
if api_key:
    logger.info("OpenAI API key is loaded")
else:
    logger.error("OpenAI API key is not loaded")

async def run_worker():
    logger.info("Connecting to Temporal server...")
    client = await Client.connect("127.0.0.1:7234")
    logger.info("Connected to Temporal server")

    logger.info("Starting worker...")
    worker = Worker(
        client,
        task_queue="ship-processing",
        workflows=[ReportDetailsWorkflow],
        activities=[assign_report_number, calculate_trust_score, calculate_visibility, find_ais_neighbours, convert_to_prometheus_metrics, llm_enrich],
    )

    logger.info("Worker started, waiting for tasks...")
    await worker.run()

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_worker())
