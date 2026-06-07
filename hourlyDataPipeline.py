import os
import requests
import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime, timezone

# ==================================================
# LOAD ENV VARIABLES
# ==================================================

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION")

LATITUDE = float(os.getenv("LATITUDE"))
LONGITUDE = float(os.getenv("LONGITUDE"))

# ==================================================
# CONNECT TO MONGODB
# ==================================================

print("Connecting to MongoDB...")

client = MongoClient(MONGO_URI)

db = client[MONGO_DB]
collection = db[MONGO_COLLECTION]

print("Connected to MongoDB OK")

# ==================================================
# CURRENT UTC DATE
# ==================================================

today_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d")

print(f"Running hourly pipeline for UTC date: {today_utc}")

# ==================================================
# FETCH AIR QUALITY DATA
# ==================================================

print("Fetching Air Quality data...")

air_url = "https://air-quality-api.open-meteo.com/v1/air-quality"

air_params = {
    "latitude": LATITUDE,
    "longitude": LONGITUDE,
    "start_date": today_utc,
    "end_date": today_utc,
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

air_response = requests.get(
    air_url,
    params=air_params,
    timeout=30
)

air_response.raise_for_status()

air_data = air_response.json()

if "hourly" not in air_data:
    print("AIR API RESPONSE:")
    print(air_data)
    raise Exception("Air Quality API did not return hourly data")

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

print("Air Quality data fetched OK")

# ==================================================
# FETCH WEATHER DATA
# ==================================================

print("Fetching Weather data...")

weather_url = "https://api.open-meteo.com/v1/forecast"

weather_params = {
    "latitude": LATITUDE,
    "longitude": LONGITUDE,
    "hourly": [
        "temperature_2m",
        "relative_humidity_2m",
        "surface_pressure",
        "wind_speed_10m"
    ],
    "forecast_days": 1
}

weather_response = requests.get(
    weather_url,
    params=weather_params,
    timeout=30
)

weather_response.raise_for_status()

weather_data = weather_response.json()

if "hourly" not in weather_data:
    print("WEATHER API RESPONSE:")
    print(weather_data)
    raise Exception("Weather API did not return hourly data")

weather_df = pd.DataFrame({
    "time": weather_data["hourly"]["time"],
    "temperature": weather_data["hourly"]["temperature_2m"],
    "humidity": weather_data["hourly"]["relative_humidity_2m"],
    "pressure": weather_data["hourly"]["surface_pressure"],
    "wind_speed": weather_data["hourly"]["wind_speed_10m"]
})

print("Weather data fetched OK")

# ==================================================
# MERGE DATA
# ==================================================

print("Merging datasets...")

air_df["time"] = pd.to_datetime(air_df["time"], utc=True)
weather_df["time"] = pd.to_datetime(weather_df["time"], utc=True)

df = pd.merge(
    air_df,
    weather_df,
    on="time",
    how="inner"
)

if df.empty:
    raise Exception("Merged dataframe is empty")

# ==================================================
# CLEAN DATA
# ==================================================

df = df.sort_values("time")

df = df.drop_duplicates(subset=["time"])

df = df.replace([float("inf"), float("-inf")], pd.NA)

df = df.ffill()
df = df.bfill()
df = df.dropna()

# ==================================================
# KEEP ONLY MOST RECENT HOUR
# ==================================================

latest_row = df.tail(1).copy()

latest_row["time"] = latest_row["time"].astype(str)

print("\nLatest record:")
print(latest_row)

# ==================================================
# UPSERT INTO MONGODB
# ==================================================

record = latest_row.iloc[0].to_dict()

result = collection.update_one(
    {"time": record["time"]},
    {"$set": record},
    upsert=True
)

# ==================================================
# LOG RESULTS
# ==================================================

if result.upserted_id:
    print(f"Inserted new record: {result.upserted_id}")
else:
    print("Record already exists or updated")

print("\nHourly pipeline completed successfully")