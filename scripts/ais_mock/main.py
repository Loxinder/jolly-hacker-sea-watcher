# main.py
import os
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field # Import Pydantic
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import uvicorn
import time # Import time module for timing

# --- Configuration ---
# Updated CSV file path as requested
CSV_FILE_PATH = 'AIS_2024_05_05.csv' # !!! IMPORTANT: Update this path if needed !!!
LAT_COL = "LAT"
LON_COL = "LON"
TIME_COL = "BaseDateTime" # Column for timestamp
MMSI_COL = "MMSI"       # Column for ship identifier

EARTH_RADIUS_KM = 6371

# --- Global Variables ---
ais_data_df: Optional[pd.DataFrame] = None # Main DataFrame for initial filtering
# --- OPTIMIZATION: Dictionary to hold pre-grouped data by MMSI ---
ais_data_grouped_by_mmsi: Dict[str, pd.DataFrame] = {}
# --- End Optimization ---
max_historical_time: Optional[pd.Timestamp] = None
time_offset: Optional[pd.Timedelta] = None

# --- Pydantic Models for API Response ---

class Position(BaseModel):
    """Represents a single point in a ship's tail."""
    lat: float = Field(..., description="Latitude of the position.")
    lon: float = Field(..., description="Longitude of the position.")
    timestamp: datetime = Field(..., description="Simulated UTC timestamp of the position.")

class ShipData(BaseModel):
    """Represents aggregated data for a single ship, including its tail."""
    mmsi: str = Field(..., description="Maritime Mobile Service Identity (MMSI).")
    latest_timestamp: datetime = Field(..., description="Simulated UTC timestamp of the latest position.")
    latest_lat: float = Field(..., description="Latitude of the latest position.")
    latest_lon: float = Field(..., description="Longitude of the latest position.")
    distance_km: float = Field(..., description="Distance from the query point to the ship's latest position (km).")
    # Updated description for tail
    tail: List[Position] = Field(..., description="List of recent positions forming the ship's tail (points are at least 1 minute apart).")

    # Include other relevant fields from the latest record
    sog: Optional[float] = Field(None, description="Speed Over Ground (knots).")
    cog: Optional[float] = Field(None, description="Course Over Ground (degrees).")
    heading: Optional[float] = Field(None, description="True heading (degrees).")
    vessel_name: Optional[str] = Field(None, description="Vessel Name.")
    imo: Optional[str] = Field(None, description="IMO Number.")
    call_sign: Optional[str] = Field(None, description="Call Sign.")
    vessel_type: Optional[int] = Field(None, description="Vessel Type code.")
    status: Optional[int] = Field(None, description="Navigation Status code.")
    length: Optional[float] = Field(None, description="Vessel Length (meters).")
    width: Optional[float] = Field(None, description="Vessel Width (meters).")
    draft: Optional[float] = Field(None, description="Vessel Draft (meters).")
    cargo: Optional[str] = Field(None, description="Cargo Type code.")
    transceiver_class: Optional[str] = Field(None, description="AIS Transceiver Class.")

    @classmethod
    def from_record(cls, record: pd.Series, tail_positions: List[Position], dist: float, simulated_time: datetime):
        """
        Helper method to create ShipData instance from a pandas Series and tail.
        Handles NaN values and type conversions for all optional fields.
        """
        data = {}

        # --- Helper function for safe conversion ---
        def safe_convert(value: Any, target_type: type) -> Optional[Any]:
            """Converts value to target_type if not NaN/None, else returns None."""
            if pd.isna(value):
                return None
            try:
                # Handle potential edge case where integer string needs float first
                if target_type == int and isinstance(value, float):
                    if value.is_integer():
                        return int(value)
                    else:
                        return None
                return target_type(value)
            except (ValueError, TypeError) as e:
                 return None

        # --- Populate data dictionary with safe conversions ---
        data["mmsi"] = str(record.get(MMSI_COL))
        data["latest_timestamp"] = simulated_time
        data["latest_lat"] = record.get(LAT_COL)
        data["latest_lon"] = record.get(LON_COL)
        data["distance_km"] = dist
        data["tail"] = tail_positions

        # Optional Floats
        data["sog"] = safe_convert(record.get("SOG"), float)
        data["cog"] = safe_convert(record.get("COG"), float)
        data["heading"] = safe_convert(record.get("Heading"), float)
        data["length"] = safe_convert(record.get("Length"), float)
        data["width"] = safe_convert(record.get("Width"), float)
        data["draft"] = safe_convert(record.get("Draft"), float)

        # Optional Integers
        data["vessel_type"] = safe_convert(record.get("VesselType"), int)
        data["status"] = safe_convert(record.get("Status"), int)

        # Optional Strings
        data["vessel_name"] = safe_convert(record.get("VesselName"), str)
        data["imo"] = safe_convert(record.get("IMO"), str)
        data["call_sign"] = safe_convert(record.get("CallSign"), str)
        data["cargo"] = safe_convert(record.get("Cargo"), str)
        data["transceiver_class"] = safe_convert(record.get("TransceiverClass"), str)

        # Pydantic will perform final validation based on the model definition
        return cls(**data)

    class Config:
        orm_mode = True


# --- Helper Functions ---

def haversine(lat1: float, lon1: float, lat2: pd.Series, lon2: pd.Series) -> pd.Series:
    """Calculates the great-circle distance in kilometers."""
    lon1_rad, lat1_rad, lon2_rad, lat2_rad = map(np.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    a = np.sin(dlat / 2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    distance_km = EARTH_RADIUS_KM * c
    return distance_km

def load_and_prepare_ais_data(file_path: str) -> Optional[pd.DataFrame]:
    """Loads, cleans, sorts, pre-groups, and prepares AIS data."""
    # Make sure we modify the global variables
    global max_historical_time, time_offset, ais_data_grouped_by_mmsi
    print(f"LOAD: Attempting to load AIS data from: {file_path}")
    load_start = time.time()
    if not os.path.exists(file_path):
        print(f"LOAD ERROR: CSV file not found at {file_path}")
        return None

    try:
        # Read CSV
        df = pd.read_csv(file_path, low_memory=False)
        print(f"LOAD: Successfully loaded {len(df)} records. (Took {time.time() - load_start:.2f}s)")
        prep_start = time.time()

        # --- Data Cleaning and Type Conversion ---
        print("LOAD: Starting data cleaning and type conversion...")
        essential_cols = [MMSI_COL, TIME_COL, LAT_COL, LON_COL]
        missing_cols = [col for col in essential_cols if col not in df.columns]
        if missing_cols:
            print(f"LOAD ERROR: Missing essential columns in CSV: {missing_cols}")
            return None

        # Convert Time Column
        df[TIME_COL] = pd.to_datetime(df[TIME_COL], errors='coerce')
        initial_rows = len(df)
        df.dropna(subset=[TIME_COL], inplace=True)
        if len(df) < initial_rows:
             print(f"LOAD: Dropped {initial_rows - len(df)} rows due to invalid '{TIME_COL}' values.")

        # Convert Lat/Lon Columns
        df[LAT_COL] = pd.to_numeric(df[LAT_COL], errors='coerce')
        df[LON_COL] = pd.to_numeric(df[LON_COL], errors='coerce')
        initial_rows = len(df)
        df.dropna(subset=[LAT_COL, LON_COL], inplace=True)
        if len(df) < initial_rows:
             print(f"LOAD: Dropped {initial_rows - len(df)} rows due to invalid LAT/LON values.")

        # Convert MMSI to string
        df[MMSI_COL] = df[MMSI_COL].astype(str)

        # Convert known numeric columns to numeric, coercing errors.
        numeric_cols = ["SOG", "COG", "Heading", "Length", "Width", "Draft", "VesselType", "Status"]
        for col in numeric_cols:
             if col in df.columns:
                 df[col] = pd.to_numeric(df[col], errors='coerce')

        # Convert known string columns to string type in DataFrame.
        string_cols = ["IMO", "CallSign", "VesselName", "TransceiverClass", "Cargo"]
        for col in string_cols:
            if col in df.columns:
                df[col] = df[col].fillna('').astype(str).replace('', np.nan)

        if df.empty:
            print("LOAD ERROR: No valid records remaining after cleaning.")
            return None
        print(f"LOAD: Cleaning and type conversion finished. (Took {time.time() - prep_start:.2f}s)")

        # --- Sort Data ---
        sort_start = time.time()
        print(f"LOAD: Sorting data by '{MMSI_COL}' and '{TIME_COL}'...")
        df.sort_values(by=[MMSI_COL, TIME_COL], inplace=True, ascending=True)
        # No need to reset index here if we group right after
        print(f"LOAD: Sorting complete. (Took {time.time() - sort_start:.2f}s)")

        # --- OPTIMIZATION: Pre-group data by MMSI ---
        group_start = time.time()
        print(f"LOAD: Pre-grouping data by {MMSI_COL}...")
        # Use a dictionary comprehension for potentially better performance
        ais_data_grouped_by_mmsi = {
            mmsi: group_df.reset_index(drop=True) # Reset index within each group
            for mmsi, group_df in df.groupby(MMSI_COL, sort=False) # sort=False since df is already sorted
        }
        num_groups = len(ais_data_grouped_by_mmsi)
        print(f"LOAD: Pre-grouping complete. Created {num_groups} groups. (Took {time.time() - group_start:.2f}s)")
        # --- End Optimization ---

        # --- Calculate Time Offset ---
        offset_start = time.time()
        # Calculate max time from the original df before it's potentially modified/discarded
        max_historical_time = df[TIME_COL].max()
        if pd.isna(max_historical_time):
             print("LOAD ERROR: Could not determine maximum historical timestamp after cleaning.")
             # Clean up potentially large intermediate df before returning None
             del df
             ais_data_grouped_by_mmsi = {}
             return None

        current_utc_time = pd.Timestamp.utcnow().tz_localize(None)
        time_offset = current_utc_time - max_historical_time
        print(f"LOAD: Max historical timestamp: {max_historical_time}")
        print(f"LOAD: Current UTC time: {current_utc_time}")
        print(f"LOAD: Calculated time offset: {time_offset}. (Took {time.time() - offset_start:.2f}s)")

        print(f"LOAD: Data loading and preparation complete. Total time: {time.time() - load_start:.2f}s")
        # Return the main DataFrame as it's still needed for initial filtering
        return df

    except FileNotFoundError:
        print(f"LOAD ERROR: File not found at {file_path}")
        return None
    except pd.errors.EmptyDataError:
        print(f"LOAD ERROR: CSV file at {file_path} is empty.")
        return None
    except Exception as e:
        print(f"LOAD ERROR: An unexpected error occurred during data loading/preparation: {e}")
        import traceback
        traceback.print_exc()
        return None


# --- FastAPI Application Setup ---
app = FastAPI(
    title="Ship AIS Data API (v2 - Pre-Grouped)",
    description="Provides simulated real-time ship AIS data with position tails, based on historical data. Optimized with pre-grouping.",
    version="2.1.0" # Incremented version number for optimization
)

# --- Load Data on Application Startup ---
@app.on_event("startup")
async def startup_event():
    """Load and prepare the AIS data when the FastAPI application starts."""
    # Make sure we assign to the global df variable
    global ais_data_df
    print("="*20 + " Application Startup " + "="*20)
    startup_start = time.time()
    # Load data and perform pre-grouping
    ais_data_df = load_and_prepare_ais_data(CSV_FILE_PATH)
    if ais_data_df is None or not ais_data_grouped_by_mmsi:
        print("STARTUP FATAL: Failed to load or pre-group AIS data. API endpoints will likely fail.")
        # Ensure ais_data_df is None if loading failed
        ais_data_df = None
    else:
        print(f"STARTUP SUCCESS: AIS data ({len(ais_data_df)} records) loaded and pre-grouped ({len(ais_data_grouped_by_mmsi)} ships). (Took {time.time() - startup_start:.2f}s)")
    print("="*20 + " Startup Complete " + "="*20)


# --- API Endpoint Definition ---
@app.get("/ships",
         response_model=List[ShipData],
         summary="Find ships with tails within a radius",
         description="Returns a list of ships, each with its latest simulated position and a 'tail' of previous positions.")
async def get_ships_with_tails(
    lat: float = Query(..., description="Latitude of the center point.", ge=-90.0, le=90.0),
    lon: float = Query(..., description="Longitude of the center point.", ge=-180.0, le=180.0),
    radius: float = Query(..., description="Search radius in kilometers.", gt=0),
    tail_hours: float = Query(24.0, description="Duration of the ship's 'tail' in hours (default: 24).", gt=0),
    sim_window_minutes: int = Query(60, description="Simulation window size in minutes (how far back from 'now' to look).", gt=0)
):
    """API endpoint to retrieve aggregated ship data with position tails."""
    global ais_data_df, time_offset, ais_data_grouped_by_mmsi # Include grouped data
    request_start_time = time.time()
    print(f"\n--- Request Received: /ships?lat={lat}&lon={lon}&radius={radius}&tail_hours={tail_hours}&sim_window={sim_window_minutes} ---")

    # Check if both main df and grouped data are available
    if ais_data_df is None or ais_data_df.empty or not ais_data_grouped_by_mmsi or time_offset is None:
        print("REQUEST ERROR: AIS data not available or not pre-grouped.")
        raise HTTPException(status_code=503, detail="AIS data is not available or not properly loaded/pre-grouped.")

    try:
        # --- Time Simulation Filter (on main DataFrame) ---
        step_start_time = time.time()
        current_utc_time = pd.Timestamp.utcnow().tz_localize(None)
        simulated_window_end = current_utc_time
        simulated_window_start = simulated_window_end - pd.Timedelta(minutes=sim_window_minutes)
        target_start_time = simulated_window_start - time_offset
        target_end_time = simulated_window_end - time_offset
        print(f"Step 1: Calculated time window ({target_start_time} to {target_end_time}). (Took {time.time() - step_start_time:.4f}s)")

        step_start_time = time.time()
        # Filter the main DataFrame
        time_filtered_df = ais_data_df[
            (ais_data_df[TIME_COL] >= target_start_time) &
            (ais_data_df[TIME_COL] <= target_end_time)
        ].copy() # Copy might not be strictly needed if only used for filtering indices
        print(f"Step 2: Filtered main DF by time window. Found {len(time_filtered_df)} potential records. (Took {time.time() - step_start_time:.4f}s)")

        if time_filtered_df.empty:
             print("REQUEST INFO: No records found within the time window in main DF.")
             raise HTTPException(status_code=404, detail=f"No ship data found within the simulated time window ({sim_window_minutes} mins).")

        # --- Geographic Filter (on time-filtered DataFrame) ---
        step_start_time = time.time()
        distances = haversine(lat, lon, time_filtered_df[LAT_COL], time_filtered_df[LON_COL])
        print(f"Step 3: Calculated distances for {len(time_filtered_df)} records. (Took {time.time() - step_start_time:.4f}s)")

        step_start_time = time.time()
        within_radius_idx = distances <= radius
        # Get the DataFrame of records within the radius and time window
        geo_time_filtered_df = time_filtered_df[within_radius_idx].copy() # Copy needed before adding column
        geo_time_filtered_df['distance_km'] = distances[within_radius_idx]
        print(f"Step 4: Filtered by radius ({radius}km). Found {len(geo_time_filtered_df)} records in area/time. (Took {time.time() - step_start_time:.4f}s)")


        if geo_time_filtered_df.empty:
            print("REQUEST INFO: No records found within the radius after time filtering.")
            raise HTTPException(status_code=404, detail="No ships found within the specified radius and time window.")

        # --- Aggregation: Find Latest Record per Ship (from geo/time filtered data) ---
        step_start_time = time.time()
        # Group the filtered data and find the index of the latest time for each MMSI
        latest_indices = geo_time_filtered_df.groupby(MMSI_COL)[TIME_COL].idxmax()
        # Select the full rows for these latest records
        latest_records_df = geo_time_filtered_df.loc[latest_indices]
        num_unique_ships = len(latest_records_df)
        print(f"Step 5: Found latest records for {num_unique_ships} unique ships in area/time. (Took {time.time() - step_start_time:.4f}s)")


        # --- Prepare Response ---
        step_start_time = time.time()
        print(f"Step 6: Preparing response and calculating tails for {num_unique_ships} ships using pre-grouped data...")
        result_ships: List[ShipData] = []
        tail_duration = pd.Timedelta(hours=tail_hours)
        min_time_diff = timedelta(minutes=1) # Minimum time difference for tail points
        ship_process_times = []

        for i, (index, latest_record) in enumerate(latest_records_df.iterrows()):
            ship_start_time = time.time()
            mmsi = latest_record[MMSI_COL]
            latest_original_time = latest_record[TIME_COL]
            latest_simulated_time = latest_original_time + time_offset
            distance = latest_record['distance_km']

            # --- Calculate Tail using Pre-Grouped Data ---
            tail_positions: List[Position] = []
            # --- OPTIMIZATION: Get the pre-grouped DataFrame for this MMSI ---
            ship_df = ais_data_grouped_by_mmsi.get(mmsi)
            # --- End Optimization ---

            if ship_df is not None and not ship_df.empty:
                tail_start_original_time = latest_original_time - tail_duration
                # --- OPTIMIZATION: Filter the smaller ship_df ---
                tail_candidates_df = ship_df[
                    (ship_df[TIME_COL] >= tail_start_original_time) &
                    (ship_df[TIME_COL] <= latest_original_time)
                ]
                # --- End Optimization ---

                # --- Select points at least 1 minute apart (from candidates) ---
                selected_tail_rows = []
                last_added_original_time = None

                if not tail_candidates_df.empty:
                    # Iterate backwards through the candidates (from newest to oldest)
                    for idx in range(len(tail_candidates_df) - 1, -1, -1):
                        current_row = tail_candidates_df.iloc[idx]
                        current_original_time = current_row[TIME_COL]

                        if last_added_original_time is None:
                            selected_tail_rows.append(current_row)
                            last_added_original_time = current_original_time
                        elif (last_added_original_time - current_original_time) >= min_time_diff:
                            selected_tail_rows.append(current_row)
                            last_added_original_time = current_original_time

                    selected_tail_rows.reverse() # Restore chronological order

                # Iterate over the selected tail rows to create Position objects
                for _, tail_row in pd.DataFrame(selected_tail_rows).iterrows():
                     simulated_tail_time = tail_row[TIME_COL] + time_offset
                     tail_positions.append(
                         Position(
                             lat=tail_row[LAT_COL],
                             lon=tail_row[LON_COL],
                             timestamp=simulated_tail_time
                         )
                     )
            else:
                print(f"  - Warning: No pre-grouped data found for MMSI {mmsi}. Tail will be empty.")


            # --- Construct ShipData Object ---
            ship_object = ShipData.from_record(
                record=latest_record,
                tail_positions=tail_positions,
                dist=distance,
                simulated_time=latest_simulated_time
            )
            result_ships.append(ship_object)
            ship_process_time = time.time() - ship_start_time
            ship_process_times.append(ship_process_time)


        avg_ship_time = np.mean(ship_process_times) if ship_process_times else 0
        max_ship_time = np.max(ship_process_times) if ship_process_times else 0
        print(f"Step 7: Finished processing tails (min 1 min interval using pre-grouped data). Avg time/ship: {avg_ship_time:.4f}s, Max time/ship: {max_ship_time:.4f}s. (Total Step 6/7 Took {time.time() - step_start_time:.4f}s)")


        if not result_ships:
             print("REQUEST INFO: No ships found after final processing.")
             raise HTTPException(status_code=404, detail="No ships found after processing.")

        total_request_time = time.time() - request_start_time
        print(f"--- Request Completed: Found {len(result_ships)} ships. Total time: {total_request_time:.4f}s ---")
        return result_ships

    except HTTPException as e:
         total_request_time = time.time() - request_start_time
         print(f"--- Request Failed (HTTPException): Status={e.status_code}, Detail='{e.detail}'. Total time: {total_request_time:.4f}s ---")
         raise e
    except Exception as e:
        total_request_time = time.time() - request_start_time
        print(f"--- Request Failed (Unexpected Error): {e}. Total time: {total_request_time:.4f}s ---")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


# --- Main Execution Block ---
if __name__ == "__main__":
    print("Starting AIS Data API server (v2 - Pre-Grouped)...")
    if not os.path.exists(CSV_FILE_PATH):
         print("-" * 50)
         print(f"WARNING: CSV file '{CSV_FILE_PATH}' not found.")
         print("Ensure the file exists and the path is correct in the script.")
         print("-" * 50)

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
