from temporalio import activity
import random
import logging

from shared import ShipDetails, EnrichedShipDetails

@activity.defn
async def fetch_ais_number(ship: ShipDetails) -> str:
    logging.info(f"Fetching AIS number for ship at coordinates: {ship.latitude}, {ship.longitude}")
    # Fake external API call
    ais_number = f"AIS-{random.randint(10000, 99999)}"
    logging.info(f"Generated AIS number: {ais_number}")
    return ais_number

@activity.defn
async def calculate_trust_score(source_account_id: str) -> float:
    logging.info(f"Calculating trust score for account: {source_account_id}")
    # Fake trust calculation
    trust_score = round(random.uniform(0.5, 1.0), 2)
    logging.info(f"Calculated trust score: {trust_score}")
    return trust_score

@activity.defn
async def convert_to_prometheus_metrics(ship_data) -> str:
    return await _convert_to_prometheus_metrics(ship_data)

async def _convert_to_prometheus_metrics(ship_data) -> str:
    logging.info(f"Converting to Prometheus metrics: {ship_data}")
    
    # Handle both dict and object inputs
    if isinstance(ship_data, dict):
        source_account_id = ship_data['source_account_id']
        latitude = ship_data['latitude']
        longitude = ship_data['longitude']
        ais_number = ship_data.get('ais_number')
        trust_score = ship_data.get('trust_score')
    else:
        source_account_id = ship_data.source_account_id
        latitude = ship_data.latitude
        longitude = ship_data.longitude
        ais_number = getattr(ship_data, 'ais_number', None)
        trust_score = getattr(ship_data, 'trust_score', None)
    
    # Determine if this is initial or final metrics
    is_final = ais_number is not None and trust_score is not None
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
            f'ais_number="{ais_number}",stage="{stage}",enriched="true"}} {trust_score}',
            f'ship_ais_number_total{{source_account_id="{source_account_id}",'
            f'latitude="{latitude}",longitude="{longitude}",'
            f'stage="{stage}",enriched="true"}} 1'
        ])
    
    result = '\n'.join(metrics)
    logging.info(f"Generated Prometheus metrics: {result}")
    return result
