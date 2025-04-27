# Ship Enrichment System

This system processes ship data through a workflow that enriches it with AIS numbers and trust scores. It exposes metrics at two points:
1. When ships are first submitted
2. After enrichment is complete

## Prerequisites

- Python 3.9+
- Temporal CLI
- Virtual environment (recommended)

## Setup

1. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate  # On Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the System

The system consists of three components that need to be running simultaneously. Open three separate terminal windows.

### Terminal 1: Temporal Server
```bash
cd temporals
temporal server start-dev --port 7234
```

### Terminal 2: Worker
```bash
cd temporals/base
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate  # On Windows
python worker.py
```

### Terminal 3: Main Server
```bash
cd temporals/base
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate  # On Windows
python server.py
```

## Testing the System

1. Submit a ship:
```bash
curl -X POST "http://localhost:8001/submit_ship" \
  -H "Content-Type: application/json" \
  -d '{
    "source_account_id": "test-account-1",
    "timestamp": "2024-04-27T00:00:00Z",
    "latitude": 37.7749,
    "longitude": -122.4194,
    "picture_url": "https://example.com/ship1.jpg"
  }'
```

2. Check metrics:
```bash
curl http://localhost:8001/metrics
```

## Troubleshooting

If you encounter port conflicts:
```bash
# Kill all Python processes
pkill -f python

# Kill Temporal server
pkill -f temporal
```

## Metrics Format

The system exposes two types of metrics:

1. Initial metrics (when ship is submitted):
```
ship_info{source_account_id="test-account-1",latitude="37.7749",longitude="-122.4194",stage="initial"} 1
```

2. Final metrics (after enrichment):
```
ship_trust_score{source_account_id="test-account-1",latitude="37.7749",longitude="-122.4194",ais_number="AIS-12345",stage="final",enriched="true"} 0.85
ship_ais_number_total{source_account_id="test-account-1",latitude="37.7749",longitude="-122.4194",stage="final",enriched="true"} 1
```

## Architecture

```
Client -> FastAPI (/submit_ship) -> Temporal Server -> Worker -> Activities -> Enriched Data
                                                      |
                                                      v
                                               Metrics Storage
                                                      |
                                                      v
                                               FastAPI (/metrics)
```

- The FastAPI server handles ship submissions and metrics exposure
- Temporal handles the workflow execution
- The worker processes the enrichment activities
- Metrics are stored in memory and exposed via the /metrics endpoint 