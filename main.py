from fastapi import FastAPI, Query
import time
import json
from pathlib import Path
from datetime import datetime, timezone

app = FastAPI(
    title="Cyclopolis Smart Bike Support API",
    version="2.0.0"
)

# =========================================================
# CONFIGURATION
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

# PoC-only memory for reboot attempts.
# This resets whenever the server restarts.
reboot_attempts = {}


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def load_json(filename):
    with open(
        BASE_DIR / filename,
        "r",
        encoding="utf-8"
    ) as f:
        return json.load(f)


def save_json(filename, data):
    with open(
        BASE_DIR / filename,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            data,
            f,
            indent=2,
            ensure_ascii=False
        )


def now():
    return datetime.now(
        timezone.utc
    ).isoformat()


def find_station_by_id(stations, station_id):

    for station in stations:

        if station["station_id"] == station_id:
            return station

    return None


def find_station_by_name(stations, name):

    if not name:
        return None

    target = name.strip().lower()

    for station in stations:

        if station["name"].strip().lower() == target:
            return station

    return None


def find_bike(bikes, bike_id):

    for bike in bikes:

        if bike["bike_id"] == bike_id:
            return bike

    return None


def find_ride_by_id(rides, ride_id):

    for ride in rides:

        if ride["ride_id"] == ride_id:
            return ride

    return None


def find_active_ride_by_bike(rides, bike_id):

    active_statuses = {
        "ongoing",
        "active",
        "in_progress"
    }

    for ride in rides:

        status = str(
            ride.get("status", "")
        ).lower()

        if (
            ride["bike_id"] == bike_id
            and status in active_statuses
        ):
            return ride

    return None


def find_latest_ride_by_bike(rides, bike_id):

    matching_rides = [
        ride
        for ride in rides
        if ride["bike_id"] == bike_id
    ]

    if not matching_rides:
        return None

    return matching_rides[-1]


# =========================================================
# MIDDLEWARE
# =========================================================

@app.middleware("http")
async def log_request(request, call_next):

    start_time = time.time()

    response = await call_next(request)

    process_time = (
        time.time() - start_time
    )

    print(
        f"{request.method} "
        f"{request.url.path}"
        f" | Status: "
        f"{response.status_code}"
        f" | Time: "
        f"{process_time:.4f} sec"
    )

    return response


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
def health():

    return {
        "success": True,
        "status": "ok",
        "service": "Cyclopolis Smart Bike Support API",
        "environment": "PoC",
        "version": "2.0.0"
    }


# =========================================================
# STATION STATUS
# =========================================================

@app.get("/station")
def get_station(
    station_id: int = Query(None),
    name: str = Query(None)
):

    stations = load_json(
        "stations.json"
    )

    bikes = load_json(
        "bikes.json"
    )

    station = None

    # -----------------------------------------
    # Find by station ID
    # -----------------------------------------

    if station_id is not None:

        station = find_station_by_id(
            stations,
            station_id
        )

    # -----------------------------------------
    # Find by station name
    # -----------------------------------------

    elif name is not None:

        station = find_station_by_name(
            stations,
            name
        )

    # -----------------------------------------
    # Not found
    # -----------------------------------------

    if station is None:

        return {
            "success": False,
            "error": "Station not found"
        }

    current_station_id = (
        station["station_id"]
    )

    # -----------------------------------------
    # Get bikes belonging to station
    # -----------------------------------------

    station_bikes = [
        bike
        for bike in bikes
        if bike["station_id"]
        == current_station_id
    ]

    available_bikes = [
        bike
        for bike in station_bikes
        if str(
            bike.get("status", "")
        ).lower() == "available"
    ]

    # -----------------------------------------
    # Return useful station information
    # -----------------------------------------

    return {
        "success": True,
        "station_id": station["station_id"],
        "name": station["name"],

        # Optional fields are returned only
        # if they exist in the JSON.
        "municipality":
            station.get("municipality"),

        "address":
            station.get("address"),

        "available_bikes":
            len(available_bikes),

        "available_bike_ids": [
            bike["bike_id"]
            for bike in available_bikes
        ],

        "empty_docks":
            station.get("available_docks", 0)
    }


# =========================================================
# STATION BIKE INVENTORY
# =========================================================

@app.get("/station/{station_id}/bikes")
def get_station_bikes(
    station_id: int
):

    stations = load_json(
        "stations.json"
    )

    bikes = load_json(
        "bikes.json"
    )

    station = find_station_by_id(
        stations,
        station_id
    )

    if station is None:

        return {
            "success": False,
            "error": "Station not found"
        }

    station_bikes = [
        bike
        for bike in bikes
        if bike["station_id"]
        == station_id
    ]

    return {
        "success": True,
        "station_id": station_id,
        "station_name": station["name"],
        "bikes": station_bikes
    }


# =========================================================
# BIKE STATUS
# =========================================================

@app.get("/bike")
def get_bike(
    bike_id: int = Query(None)
):

    bikes = load_json(
        "bikes.json"
    )

    stations = load_json(
        "stations.json"
    )

    rides = load_json(
        "rides.json"
    )

    if bike_id is None:

        return {
            "success": False,
            "error": "Bike ID is required"
        }

    bike = find_bike(
        bikes,
        bike_id
    )

    if bike is None:

        return {
            "success": False,
            "error": "Bike not found",
            "bike_id": bike_id
        }

    station = find_station_by_id(
        stations,
        bike["station_id"]
    )

    active_ride = find_active_ride_by_bike(
        rides,
        bike_id
    )

    return {
        "success": True,

        "bike_id":
            bike["bike_id"],

        "status":
            bike["status"],

        "battery":
            bike["battery"],

        "station_id":
            bike["station_id"],

        "station_name":
            station["name"]
            if station
            else None,

        "municipality":
            station.get("municipality")
            if station
            else None,

        "dock_position":
            bike.get("dock_position"),

        "connection_status":
            bike.get("connection_status"),

        "current_ride_id":
            active_ride["ride_id"]
            if active_ride
            else None
    }


# =========================================================
# RIDE STATUS
# =========================================================

@app.get("/ride")
def get_ride(
    ride_id: int = Query(None),
    bike_id: int = Query(None)
):

    rides = load_json(
        "rides.json"
    )

    bikes = load_json(
        "bikes.json"
    )

    stations = load_json(
        "stations.json"
    )

    # -----------------------------------------
    # No identifier supplied
    # -----------------------------------------

    if (
        ride_id is None
        and bike_id is None
    ):

        return {
            "success": False,
            "error": (
                "Provide either "
                "ride_id or bike_id"
            )
        }

    ride = None

    # -----------------------------------------
    # Priority 1: Ride ID
    # -----------------------------------------

    if ride_id is not None:

        ride = find_ride_by_id(
            rides,
            ride_id
        )

    # -----------------------------------------
    # Priority 2: Active ride by Bike ID
    # -----------------------------------------

    elif bike_id is not None:

        ride = find_active_ride_by_bike(
            rides,
            bike_id
        )

        # If there is no active ride,
        # return latest known ride for the bike.
        if ride is None:

            ride = find_latest_ride_by_bike(
                rides,
                bike_id
            )

    # -----------------------------------------
    # Ride not found
    # -----------------------------------------

    if ride is None:

        return {
            "success": False,
            "error": "Ride not found",
            "ride_id": ride_id,
            "bike_id": bike_id
        }

    bike = find_bike(
        bikes,
        ride["bike_id"]
    )

    station = None

    if "station_id" in ride:

        station = find_station_by_id(
            stations,
            ride["station_id"]
        )

    active_statuses = {
        "ongoing",
        "active",
        "in_progress"
    }

    is_active = (
        str(
            ride.get("status", "")
        ).lower()
        in active_statuses
    )

    return {
        "success": True,

        "ride_id":
            ride["ride_id"],

        "bike_id":
            ride["bike_id"],

        "user_id":
            ride.get("user_id"),

        "status":
            ride.get("status"),

        "is_active":
            is_active,

        "station_id":
            ride.get("station_id"),

        "station_name":
            station["name"]
            if station
            else None,

        "municipality":
            station.get("municipality")
            if station
            else None,

        "bike_status":
            bike["status"]
            if bike
            else None,

        "battery":
            bike["battery"]
            if bike
            else None,

        "started_at":
            ride.get("started_at"),

        "ended_at":
            ride.get("ended_at"),

        "duration":
            ride.get("duration")
    }


# =========================================================
# REBOOT BIKE
# =========================================================

@app.api_route(
    "/reboot_bike",
    methods=["POST", "GET"]
)
def reboot_bike(
    bike_id: int = Query(
        ...,
        description=(
            "ID of the bike that "
            "needs to be rebooted."
        )
    )
):

    bikes = load_json(
        "bikes.json"
    )

    stations = load_json(
        "stations.json"
    )

    rides = load_json(
        "rides.json"
    )

    # -----------------------------------------
    # Find bike
    # -----------------------------------------

    bike = find_bike(
        bikes,
        bike_id
    )

    if bike is None:

        return {
            "success": False,
            "completed": False,
            "bike_id": bike_id,
            "reboot_status": "failed",
            "error": "Bike not found"
        }

    # -----------------------------------------
    # Maintenance bikes cannot be rebooted
    # -----------------------------------------

    if (
        str(
            bike.get("status", "")
        ).lower()
        == "maintenance"
    ):

        return {
            "success": False,
            "completed": False,
            "bike_id": bike_id,
            "reboot_status": "failed",
            "error": (
                "Bike is currently "
                "in maintenance"
            )
        }

    # -----------------------------------------
    # Determine required attempts
    #
    # bikes.json can optionally contain:
    #
    # "reboot_attempts_required": 2
    #
    # If it doesn't exist, default = 1.
    # -----------------------------------------

    required_attempts = int(
        bike.get(
            "reboot_attempts_required",
            1
        )
    )

    current_attempt = (
        reboot_attempts.get(
            bike_id,
            0
        )
        + 1
    )

    reboot_attempts[bike_id] = (
        current_attempt
    )

    # -----------------------------------------
    # Reboot still in progress
    # -----------------------------------------

    if current_attempt < required_attempts:

        return {
            "success": True,
            "completed": False,
            "bike_id": bike_id,
            "attempt": current_attempt,
            "attempts_remaining":
                required_attempts
                - current_attempt,
            "reboot_status":
                "in_progress"
        }

    # -----------------------------------------
    # Successful reboot
    # -----------------------------------------

    bike["connection_status"] = "online"

    bike["last_rebooted_at"] = now()

    save_json(
        "bikes.json",
        bikes
    )

    # Reset attempt counter
    reboot_attempts.pop(
        bike_id,
        None
    )

    station = find_station_by_id(
        stations,
        bike["station_id"]
    )

    active_ride = find_active_ride_by_bike(
        rides,
        bike_id
    )

    return {
        "success": True,
        "completed": True,
        "bike_id": bike_id,

        "reboot_status":
            "completed",

        "station_id":
            bike["station_id"],

        "station_name":
            station["name"]
            if station
            else None,

        "dock_position":
            bike.get("dock_position"),

        "current_ride_id":
            active_ride["ride_id"]
            if active_ride
            else None,

        "message":
            "Bike reboot completed"
    }


# =========================================================
# END RIDE
# =========================================================

@app.api_route(
    "/end_ride",
    methods=["POST", "GET"]
)
def end_ride(
    ride_id: int = Query(None),
    bike_id: int = Query(None)
):

    rides = load_json(
        "rides.json"
    )

    bikes = load_json(
        "bikes.json"
    )

    # -----------------------------------------
    # Identifier validation
    # -----------------------------------------

    if (
        ride_id is None
        and bike_id is None
    ):

        return {
            "success": False,
            "status": "failed",
            "error": (
                "Provide either "
                "ride_id or bike_id"
            )
        }

    ride = None

    # -----------------------------------------
    # Find by Ride ID
    # -----------------------------------------

    if ride_id is not None:

        ride = find_ride_by_id(
            rides,
            ride_id
        )

    # -----------------------------------------
    # Find active ride by Bike ID
    # -----------------------------------------

    elif bike_id is not None:

        ride = find_active_ride_by_bike(
            rides,
            bike_id
        )

    # -----------------------------------------
    # Ride not found
    # -----------------------------------------

    if ride is None:

        return {
            "success": False,
            "status": "failed",
            "error": "Ride not found",
            "ride_id": ride_id,
            "bike_id": bike_id
        }

    current_status = str(
        ride.get("status", "")
    ).lower()

    # -----------------------------------------
    # Already completed
    # -----------------------------------------

    if current_status in {
        "completed",
        "closed"
    }:

        return {
            "success": True,
            "already_completed": True,
            "ride_id":
                ride["ride_id"],
            "bike_id":
                ride["bike_id"],
            "status":
                ride["status"]
        }

    # -----------------------------------------
    # Ride is not active
    # -----------------------------------------

    if current_status not in {
        "ongoing",
        "active",
        "in_progress"
    }:

        return {
            "success": False,
            "status": "failed",
            "error": (
                "Ride cannot be ended "
                f"from status "
                f"'{ride.get('status')}'"
            ),
            "ride_id":
                ride["ride_id"]
        }

    # -----------------------------------------
    # End ride
    # -----------------------------------------

    ride["status"] = "completed"

    ride["ended_at"] = now()

    # -----------------------------------------
    # Make bike available again
    # -----------------------------------------

    bike = find_bike(
        bikes,
        ride["bike_id"]
    )

    if bike:

        bike["status"] = "available"

    # -----------------------------------------
    # Save state
    # -----------------------------------------

    save_json(
        "rides.json",
        rides
    )

    save_json(
        "bikes.json",
        bikes
    )

    return {
        "success": True,
        "already_completed": False,

        "ride_id":
            ride["ride_id"],

        "bike_id":
            ride["bike_id"],

        "status":
            "completed",

        "message":
            "Ride successfully ended"
    }