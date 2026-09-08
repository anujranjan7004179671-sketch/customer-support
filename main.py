from fastapi import FastAPI, Query
import time
import json
from pathlib import Path

app = FastAPI(title="Smart Bike Support API")

# ---------------------------------------
# Helper Functions
# ---------------------------------------

BASE_DIR = Path(__file__).resolve().parent


def load_json(filename):
    with open(BASE_DIR / filename, "r") as f:
        return json.load(f)


# ---------------------------------------
# Middleware
# ---------------------------------------

@app.middleware("http")
async def log_request(request, call_next):

    start_time = time.time()

    response = await call_next(request)

    process_time = time.time() - start_time

    print(
        f"{request.method} {request.url.path}"
        f" | Status: {response.status_code}"
        f" | Time: {process_time:.4f} sec"
    )

    return response


# ---------------------------------------
# Station Endpoint
# ---------------------------------------

@app.get("/station")
def get_station(
    station_id: int = Query(None),
    name: str = Query(None)
):

    stations = load_json("stations.json")

    if station_id is not None:
        for station in stations:
            if station["station_id"] == station_id:
                return station

    if name is not None:
        for station in stations:
            if station["name"].lower() == name.lower():
                return station

    return {
        "error": "Station not found"
    }


# ---------------------------------------
# Bike Endpoint
# ---------------------------------------

@app.get("/bike")
def get_bike(
    bike_id: int = Query(None)
):

    bikes = load_json("bikes.json")

    if bike_id is not None:
        for bike in bikes:
            if bike["bike_id"] == bike_id:
                return bike

    return {
        "error": "Bike not found"
    }


# ---------------------------------------
# Ride Endpoint
# ---------------------------------------

@app.get("/ride")
def get_ride(
    ride_id: int = Query(None)
):

    rides = load_json("rides.json")

    if ride_id is not None:
        for ride in rides:
            if ride["ride_id"] == ride_id:
                return ride

    return {
        "error": "Ride not found"
    }
@app.post("/reboot_bike")
def reboot_bike(
    bike_id: int = Query(..., description="The ID of the bike to reboot")
):
    bikes = load_json("bikes.json")
    
    for bike in bikes:
        if bike["bike_id"] == bike_id:
            # Simulating the hardware reboot command
            return {
                "bike_id": bike_id,
                "reboot_status": "completed",
                "message": f"Successfully sent reboot command to bike {bike_id}."
            }
            
    return {
        "error": "Bike not found",
        "reboot_status": "failed"
    } 
@app.post("/end_ride")
def end_ride(
    ride_id: int = Query(..., description="The ID of the ride or booking to end")
):
    rides = load_json("rides.json")
    
    for ride in rides:
        if ride["ride_id"] == ride_id:
            # Simulating ending the trip in the database
            return {
                "ride_id": ride_id,
                "status": "completed",
                "message": f"Successfully ended ride {ride_id}. The user is free to book another bike."
            }
            
    return {
        "error": "Ride not found",
        "status": "failed"
    }