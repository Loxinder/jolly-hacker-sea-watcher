from temporalio import workflow
from temporalio.common import RetryPolicy

import logging

from datetime import timedelta
from shared import ShipDetails, EnrichedShipDetails

from activities import calculate_trust_score, fetch_ais_number, convert_to_prometheus_metrics

RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=5),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(minutes=1),
    maximum_attempts=5,
)

@workflow.defn
class ShipDetailsWorkflow:
    def __init__(self):
        self._metrics = []

    @workflow.run
    async def run(self, ship: ShipDetails) -> EnrichedShipDetails:
        logging.info(f"Running workflow with ship details: {ship}")
        
        # Store initial metrics
        initial_metric = await workflow.execute_activity(
            convert_to_prometheus_metrics,
            ship,
            start_to_close_timeout=timedelta(seconds=5),
        )
        self._metrics.append(initial_metric)
        logging.info(f"Stored initial metric: {initial_metric}")

        enriched = EnrichedShipDetails(**ship.__dict__)

        enriched.ais_number = await workflow.execute_activity(
            fetch_ais_number,
            enriched,
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RETRY_POLICY,
        )
        logging.info(f"Enriched with AIS number: {enriched.ais_number}")

        enriched.trust_score = await workflow.execute_activity(
            calculate_trust_score,
            enriched.source_account_id,
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RETRY_POLICY,
        )
        logging.info(f"Trust score calculated: {enriched.trust_score}")

        # Store final metrics
        final_metric = await workflow.execute_activity(
            convert_to_prometheus_metrics,
            enriched,
            start_to_close_timeout=timedelta(seconds=5),
        )
        self._metrics.append(final_metric)
        logging.info(f"Stored final metric: {final_metric}")

        return enriched

    @workflow.query
    def get_metrics(self) -> str:
        if not self._metrics:
            return ""
        # Add type and help information
        result = (
            '# HELP ship_trust_score Trust score for ships\n'
            '# TYPE ship_trust_score gauge\n'
            '# HELP ship_ais_number_total Total number of ships with AIS numbers\n'
            '# TYPE ship_ais_number_total counter\n'
        )
        # Add all metrics
        result += '\n'.join(self._metrics)
        return result