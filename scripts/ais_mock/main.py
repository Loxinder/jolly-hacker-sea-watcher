# main.py
import os
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException, Query
from typing import List, Dict, Any
import uvicorn # Required to run the app with `python main.py`

# --- Configuration ---
# !!! IMPORTANT: Replace 'your_ais_data.csv' with the actual path to your CSV file !!!
CSV_FILE_PATH = 'AIS_2024_05_05.csv'
# Define the columns expected in the CSV based on the PDF
# Adjust these if your CSV headers are slightly different
EXPECTED_COLUMNS = [
    "MMSI", "BaseDateTime", "LAT", "LON", "SOG", "COG", "Heading",
    "VesselName", "IMO", "CallSign", "VesselType", "Status", "Length",
    "Width", "Draft", "Cargo", "TransceiverClass"
]
LAT_COL = "LAT"
LON_COL = "LON"

# Earth radius in kilometers (used for distance calculation)
EARTH_RADIUS_KM = 6371

# --- Global Variable for Data ---
# This will hold the loaded AIS data in a pandas DataFrame
ais_data_df = None

# --- Helper Functions ---

def haversine(lat1: float, lon1: float, lat2: pd.Series, lon2: pd.Series) -> pd.Series:
    """
    Calculate the great-circle distance in kilometers between a point (lat1, lon1)
    and arrays of points (lat2, lon2) using the Haversine formula.

    Args:
        lat1: Latitude of the first point (scalar).
        lon1: Longitude of the first point (scalar).
        lat2: Series of latitudes for the second points.
        lon2: Series of longitudes for the second points.

    Returns:
        A pandas Series containing distances in kilometers.
    """
    # Convert decimal degrees to radians
    lon1_rad, lat1_rad, lon2_rad, lat2_rad = map(np.radians, [lon1, lat1, lon2, lat2])

    # Haversine formula
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    a = np.sin(dlat / 2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    distance_km = EARTH_RADIUS_KM * c
    return distance_km

def load_ais_data(file_path: str) -> pd.DataFrame | None:
    """
    Loads AIS data from the specified CSV file into a pandas DataFrame.
    Performs basic validation and data type conversion.

    Args:
        file_path: The path to the AIS data CSV file.

    Returns:
        A pandas DataFrame containing the AIS data, or None if loading fails.
    """
    print(f"Attempting to load AIS data from: {file_path}")
    if not os.path.exists(file_path):
        print(f"Error: CSV file not found at {file_path}")
        return None

    try:
        # Read the CSV file
        df = pd.read_csv(file_path)
        print(f"Successfully loaded {len(df)} records.")

        # Basic validation: Check if essential columns exist
        missing_cols = [col for col in [LAT_COL, LON_COL] if col not in df.columns]
        if missing_cols:
            print(f"Error: Missing essential columns in CSV: {missing_cols}")
            return None

        # Ensure LAT and LON are numeric, coercing errors to NaN
        df[LAT_COL] = pd.to_numeric(df[LAT_COL], errors='coerce')
        df[LON_COL] = pd.to_numeric(df[LON_COL], errors='coerce')

        # Drop rows where LAT or LON could not be converted (are NaN)
        initial_rows = len(df)
        df.dropna(subset=[LAT_COL, LON_COL], inplace=True)
        dropped_rows = initial_rows - len(df)
        if dropped_rows > 0:
            print(f"Warning: Dropped {dropped_rows} rows due to invalid LAT/LON values.")

        # Optional: Convert other columns if needed (e.g., BaseDateTime)
        if "BaseDateTime" in df.columns:
             df["BaseDateTime"] = pd.to_datetime(df["BaseDateTime"], errors='coerce')

        print("Data cleaning and type conversion complete.")
        return df

    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return None
    except pd.errors.EmptyDataError:
        print(f"Error: CSV file at {file_path} is empty.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while loading CSV: {e}")
        return None

# --- FastAPI Application Setup ---
app = FastAPI(
    title="Ship AIS Data API",
    description="Provides access to ship AIS data based on location and radius.",
    version="1.0.0"
)

# --- Load Data on Application Startup ---
@app.on_event("startup")
async def startup_event():
    """Load the AIS data when the FastAPI application starts."""
    global ais_data_df
    print("Application startup: Loading AIS data...")
    ais_data_df = load_ais_data(CSV_FILE_PATH)
    if ais_data_df is None:
        print("FATAL: Failed to load AIS data. The API might not function correctly.")
        # Depending on requirements, you might want the app to exit if data loading fails.
        # For this example, it will continue running but the endpoint will return an error.
    else:
        print("AIS data loaded successfully.")


# --- API Endpoint Definition ---
@app.get("/ships",
         response_model=List[Dict[str, Any]],
         summary="Find ships within a radius",
         description="Returns a list of ships and their AIS data found within the specified radius (in kilometers) from the given latitude and longitude.")
async def get_ships_in_radius(
    lat: float = Query(...,
                       description="Latitude of the center point (decimal degrees).",
                       ge=-90.0, le=90.0), # Add validation for lat range
    lon: float = Query(...,
                       description="Longitude of the center point (decimal degrees).",
                       ge=-180.0, le=180.0), # Add validation for lon range
    radius: float = Query(...,
                          description="Search radius in kilometers.",
                          gt=0) # Radius must be positive
):
    """
    API endpoint to retrieve ship data within a specified radius.

    Args:
        lat: Center latitude.
        lon: Center longitude.
        radius: Search radius in kilometers.

    Returns:
        A list of dictionaries, where each dictionary represents a ship's data.

    Raises:
        HTTPException: 503 if AIS data is not loaded.
        HTTPException: 404 if no ships are found within the radius.
    """
    global ais_data_df
    if ais_data_df is None:
        raise HTTPException(status_code=503, detail=f"AIS data could not be loaded from {CSV_FILE_PATH}. API is unavailable.")

    if ais_data_df.empty:
         raise HTTPException(status_code=404, detail="AIS data is loaded but contains no valid records.")

    try:
        # Calculate distances from the query point to all ships in the DataFrame
        distances = haversine(lat, lon, ais_data_df[LAT_COL], ais_data_df[LON_COL])

        # Filter the DataFrame to include only ships within the specified radius
        ships_within_radius_df = ais_data_df[distances <= radius].copy() # Use .copy() to avoid SettingWithCopyWarning

        # Add the calculated distance to the result (optional)
        ships_within_radius_df['distance_km'] = distances[distances <= radius]

        if ships_within_radius_df.empty:
            raise HTTPException(status_code=404, detail="No ships found within the specified radius.")

        # Convert the filtered DataFrame to a list of dictionaries for JSON response
        # Handle potential NaN values by replacing them with None (which becomes JSON null)
        result = ships_within_radius_df.replace({np.nan: None}).to_dict(orient='records')

        return result

    except Exception as e:
        # Catch unexpected errors during processing
        print(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {e}")


# --- Main Execution Block ---
# This allows running the app directly using `python main.py`
if __name__ == "__main__":
    print("Starting AIS Data API server...")
    # Check if the CSV file exists before starting the server
    if not os.path.exists(CSV_FILE_PATH):
         print("-" * 50)
         print(f"WARNING: The specified CSV file '{CSV_FILE_PATH}' does not exist.")
         print("Please ensure the file exists and the CSV_FILE_PATH variable is set correctly.")
         print("You can create a dummy CSV for testing if needed.")
         print("-" * 50)
         # You might want to exit here if the file is absolutely required
         # import sys
         # sys.exit(1)

    # Run the FastAPI server using uvicorn
    # host="0.0.0.0" makes it accessible on your network
    # reload=True automatically restarts the server when code changes (useful for development)
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
