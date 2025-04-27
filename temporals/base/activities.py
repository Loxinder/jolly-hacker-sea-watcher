from temporalio import activity
import random
import logging

from shared import ReportDetails, EnrichedReportDetails

@activity.defn
async def calculate_trust_score(source_account_id: str) -> float:
    logging.info(f"Calculating trust score for account: {source_account_id}")
    # Fake trust calculation
    trust_score = round(random.uniform(0.5, 1.0), 2)
    logging.info(f"Calculated trust score: {trust_score}")
    return trust_score

@activity.defn
async def assign_report_number(report: ReportDetails) -> str:
    logging.info(f"Fetching AIS number for ship at coordinates: {report.latitude}, {report.longitude}")
    # Fake external API call
    report_number = f"AIS-{random.randint(10000, 99999)}"
    logging.info(f"Generated AIS number: {report_number}")
    return report_number

@activity.defn
async def calculate_visibility(report: EnrichedReportDetails) -> int:
    logging.info(f"Checking weather at coordinates: {report.latitude}, {report.longitude}")
    # Fake external API call
    visibility = random.randint(5, 10)
    logging.info(f"Generated AIS number: {visibility}")
    return visibility

@activity.defn
async def find_ais_neighbours(report: EnrichedReportDetails) -> list[str]:
    import requests
    logging.info(f"Fetching AIS data for ships around coordinates: {report.latitude}, {report.longitude}")
    url = f"http://0.0.0.0:8000/ships?lat={report.latitude}&lon={report.longitude}&radius={report.visibility}&tail_hours=0.1&sim_window_minutes=120"
    logging.info(f"Making GET request to {url}")
    try:
        response = requests.request(
            method="GET",
            url=url,
            timeout=15 # Example timeout for the request itself
        )
        # Raise an exception for bad status codes (4xx or 5xx)
        response.raise_for_status()

        # Handle cases where response might not have JSON body if needed
        ais_data = response.json()
        neighbours = []
        for ship in ais_data:
            logging.info(f"{ship}")
            neighbours.append(ship["vessel_name"])

        logging.info(f"Found ships around location at this time: {neighbours}")
        return neighbours

    except requests.exceptions.RequestException as e:
        activity.logger.error(f"HTTP request failed: {e}")
        # Re-raise the exception so Temporal knows the activity failed
        raise e


@activity.defn
async def convert_to_prometheus_metrics(report_data) -> str:
    return await _convert_to_prometheus_metrics(report_data)

async def _convert_to_prometheus_metrics(report_data) -> str:
    logging.info(f"Converting to Prometheus metrics: {report_data}")
    
    # Handle both dict and object inputs
    if isinstance(report_data, dict):
        source_account_id = report_data['source_account_id']
        latitude = report_data['latitude']
        longitude = report_data['longitude']
        report_number = report_data.get('report_number')
        trust_score = report_data.get('trust_score')
        enriched_description = report_data.get('enriched_description')
        visibility = report_data.get('visibility')
        ais_neighbours = report_data.get('ais_neighbours')
    else:
        source_account_id = report_data.source_account_id
        latitude = report_data.latitude
        longitude = report_data.longitude
        report_number = getattr(report_data, 'report_number', None)
        trust_score = getattr(report_data, 'trust_score', None)
        enriched_description = getattr(report_data, 'enriched_description', None)
        visibility = getattr(report_data, 'visibility', None)
        ais_neighbours = getattr(report_data, 'ais_neighbours', None)
    
    # Determine if this is initial or final metrics
    is_final = report_number is not None and trust_score is not None
    stage = "final" if is_final else "initial"
    
    # Build metrics with stage label
    metrics = []
    
    # For initial metrics, we only have basic ship info
    if not is_final:
        metrics.append(
            f'ship_info{{source_account_id="{source_account_id}",'
            f'latitude="{latitude}",longitude="{longitude}",'
            f'stage="{stage}"}} 1'
        )
    else:
        # For final metrics, we have all enriched data
        metrics.extend([
            f'ship_trust_score{{source_account_id="{source_account_id}",'
            f'latitude="{latitude}",longitude="{longitude}",'
            f'report_number="{report_number}",stage="{stage}",enriched="true"}} {trust_score}',
            f'ship_report_number_total{{source_account_id="{source_account_id}",'
            f'latitude="{latitude}",longitude="{longitude}",'
            f'stage="{stage}",enriched="true"}} 1'
        ])
        if enriched_description:
            metrics.append(
                f'ship_description_length{{source_account_id="{source_account_id}",'
                f'latitude="{latitude}",longitude="{longitude}",'
                f'stage="{stage}",enriched="true"}} {len(enriched_description)}'
            )
    
    result = '\n'.join(metrics)
    logging.info(f"Generated Prometheus metrics: {result}")
    return result

@activity.defn
async def llm_enrich(report: EnrichedReportDetails) -> str:
    """
    Enriches the report description using LLM.
    This activity takes the existing description and enhances it with additional context
    about the vessel, location, and surrounding conditions.
    """
    logging.info(f"Enriching description for ship at coordinates: {report.latitude}, {report.longitude}")
    
    # TODO: Implement LLM enrichment logic
    # This is where you would:
    # 1. Prepare the prompt with ship details
    # 2. Call your LLM service
    # 3. Process and return the enriched description
    
    # For now, return a placeholder enriched description
    enriched_description = f"Vessel {report.report_number} observed at coordinates ({report.latitude}, {report.longitude}). "
    if report.ais_neighbours:
        enriched_description += f"Nearby vessels: {', '.join(report.ais_neighbours)}. "
    enriched_description += f"Visibility conditions: {report.visibility}/10. Trust score: {report.trust_score}."
    
    logging.info(f"Generated enriched description: {enriched_description}")
    return enriched_description
