# AIS Data API (Simulated)

This Python script provides a FastAPI-based web API to query simulated ship Automatic Identification System (AIS) data. It reads historical AIS data from a CSV file, simulates a "real-time" view by offsetting timestamps, and allows querying for ships within a specific geographic radius. For each ship found, it returns the latest simulated position and a historical track ("tail") with points filtered to be at least one minute apart.

The data is pre-processed at startup by grouping records per ship (MMSI) to optimize query performance.

## Features

* Loads AIS data from a CSV file.
* Simulates real-time data based on the latest timestamp in the source file.
* Provides a `/ships` endpoint to query data by latitude, longitude, and radius.
* Returns aggregated ship data including the latest position and a historical tail.
* Optimized tail calculation using pre-grouped data.
* Tail points are filtered to be at least 1 minute apart based on original timestamps.

## Requirements

* Python 3.x
* Nix package manager (for NixOS/Nix environment setup)
* An AIS data CSV file (e.g., `AIS_2024_05_05.csv`) with columns matching the expected format (including `MMSI`, `BaseDateTime`, `LAT`, `LON`, etc.).

## Setup and Running (NixOS / Nix)

1.  **Place Files:** Ensure `main.py`, `shell.nix`, and your AIS data CSV file (e.g., `AIS_2024_05_05.csv`) are in the same directory.
2.  **Update CSV Path:** Verify that the `CSV_FILE_PATH` variable inside `main.py` points to your correct CSV file name.
    ```python
    # main.py
    CSV_FILE_PATH = 'AIS_2024_05_05.csv' # <-- Make sure this matches your file
    ```
3.  **Enter Nix Shell:** Open a terminal in the project directory and run:
    ```bash
    nix-shell
    ```
    This command reads `shell.nix`, downloads/builds the required dependencies (Python, FastAPI, Pandas, NumPy, Uvicorn), and creates an isolated environment.
4.  **Run the API Server:** Once inside the Nix shell, start the FastAPI server using Uvicorn:
    ```bash
    python main.py
    ```
    The server should start, typically listening on `http://0.0.0.0:8000`. You'll see log messages indicating the data loading and preparation process.

## API Endpoint: `/ships`

Retrieves ship data within a specified radius and time window.

* **Method:** `GET`
* **URL:** `/ships`
* **Query Parameters:**
    * `lat` (float, **required**): Latitude of the center point (e.g., `37.7895943`).
    * `lon` (float, **required**): Longitude of the center point (e.g., `-122.3851222`).
    * `radius` (float, **required**): Search radius in kilometers (e.g., `1`). Must be > 0.
    * `tail_hours` (float, optional, default: `24.0`): How far back in time (in hours) to look for tail points relative to the ship's latest found position. Must be > 0.
    * `sim_window_minutes` (int, optional, default: `60`): How many minutes back from the simulated "now" to look for the *latest* position reports when initially filtering ships. Must be > 0.

* **Example Request:**
    ```
    [http://0.0.0.0:8000/ships?lat=37.7895943&lon=-122.3851222&radius=1&tail_hours=0.1&sim_window_minutes=360](http://0.0.0.0:8000/ships?lat=37.7895943&lon=-122.3851222&radius=1&tail_hours=0.1&sim_window_minutes=360)
    ```
    This requests ships within a 1 km radius of the given coordinates. It considers ships whose latest simulated position report falls within the last 360 minutes (6 hours). For the ships found, it calculates a tail going back 0.1 hours (6 minutes) from their respective latest positions, filtering tail points to be at least 1 minute apart.

* **Success Response:** `200 OK` with a JSON array of `ShipData` objects.
* **Error Responses:**
    * `404 Not Found`: If no ships match the criteria.
    * `422 Unprocessable Entity`: If query parameters are invalid.
    * `500 Internal Server Error`: If an unexpected error occurs during processing.
    * `503 Service Unavailable`: If the AIS data failed to load at startup.

## Development

* The server uses `reload=True`, so changes saved to `main.py` while the server is running (within `nix-shell`) should trigger an automatic restart.
* Detailed logs are printed to the console during startup and for each request, including timing for different processing steps.
