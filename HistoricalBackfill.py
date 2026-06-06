import os
import requests
import pandas as pd
from pymongo import MongoClient, UpdateOne
from dotenv import load_dotenv

# ==================================================
# LOAD ENV VARIABLES
# ==================================================

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB", "aqi_db")
COLLECTION_NAME = os.getenv("MONGO_COLLECTION", "raw_aqi_data")

LATITUDE = float(os.getenv("LATITUDE"))
LONGITUDE = float(os.getenv("LONGITUDE"))
START_DATE = os.getenv("START_DATE")
END_DATE = os.getenv("END_DATE")

# ==================================================
# CONNECT TO MONGO
# ==================================================

print("Connecting to MongoDB...")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

print("Connected to MongoDB OK")

# ==================================================
# FETCH AIR QUALITY DATA
# ==================================================

print("Fetching Air Quality data...")

air_url = "https://air-quality-api.open-meteo.com/v1/air-quality"

air_params = {
    "latitude": LATITUDE,
    "longitude": LONGITUDE,
    "start_date": START_DATE,
    "end_date": END_DATE,
    "hourly": [
        "pm10",
        "pm2_5",
        "carbon_monoxide",
        "nitrogen_dioxide",
        "sulphur_dioxide",
        "ozone",
        "methane",
        "dust",
        "european_aqi"
    ]
}

air_data = requests.get(air_url, params=air_params, timeout=30).json()

air_df = pd.DataFrame({
    "time": air_data["hourly"]["time"],
    "pm10": air_data["hourly"]["pm10"],
    "pm2_5": air_data["hourly"]["pm2_5"],
    "carbon_monoxide": air_data["hourly"]["carbon_monoxide"],
    "nitrogen_dioxide": air_data["hourly"]["nitrogen_dioxide"],
    "sulphur_dioxide": air_data["hourly"]["sulphur_dioxide"],
    "ozone": air_data["hourly"]["ozone"],
    "methane": air_data["hourly"]["methane"],
    "dust": air_data["hourly"]["dust"],
    "aqi": air_data["hourly"]["european_aqi"]
})

print("Air data fetched OK")

# ==================================================
# FETCH WEATHER DATA
# ==================================================

print("Fetching Weather data...")

weather_url = "https://archive-api.open-meteo.com/v1/archive"

weather_params = {
    "latitude": LATITUDE,
    "longitude": LONGITUDE,
    "start_date": START_DATE,
    "end_date": END_DATE,
    "hourly": [
        "temperature_2m",
        "relative_humidity_2m",
        "surface_pressure",
        "wind_speed_10m"
    ]
}

weather_data = requests.get(weather_url, params=weather_params, timeout=30).json()

weather_df = pd.DataFrame({
    "time": weather_data["hourly"]["time"],
    "temperature": weather_data["hourly"]["temperature_2m"],
    "humidity": weather_data["hourly"]["relative_humidity_2m"],
    "pressure": weather_data["hourly"]["surface_pressure"],
    "wind_speed": weather_data["hourly"]["wind_speed_10m"]
})

print("Weather data fetched OK")

# ==================================================
# MERGE
# ==================================================

print("Merging datasets...")

air_df["time"] = pd.to_datetime(air_df["time"])
weather_df["time"] = pd.to_datetime(weather_df["time"])

df = pd.merge(air_df, weather_df, on="time", how="inner")

# ==================================================
# CLEANING
# ==================================================

print("Cleaning data...")

df = df.sort_values("time")
df = df.drop_duplicates(subset=["time"])

df = df.replace([float("inf"), float("-inf")], pd.NA)
df = df.ffill().bfill().dropna()

df = df.reset_index(drop=True)

# ==================================================
# MONGODB BULK UPSERT (FAST PART)
# ==================================================

print("Uploading to MongoDB (FAST BULK MODE)...")

df["time"] = df["time"].astype(str)
records = df.to_dict(orient="records")

operations = [
    UpdateOne(
        {"time": record["time"]},   # unique key
        {"$set": record},
        upsert=True
    )
    for record in records
]

if operations:
    result = collection.bulk_write(operations)

    print("Inserted:", result.upserted_count)
    print("Modified:", result.modified_count)

print("UPLOAD SUCCESSFUL OK")
print("Pipeline completed successfully [FINISHED]")