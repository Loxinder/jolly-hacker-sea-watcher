# @@@SNIPSTART python-money-transfer-project-template-shared
from pydantic import BaseModel
from typing import Optional

class ShipDetails(BaseModel):
    source_account_id: str
    timestamp: str
    latitude: float
    longitude: float
    picture_url: str

class EnrichedShipDetails(ShipDetails):
    ais_number: Optional[str] = None
    trust_score: Optional[float] = None
