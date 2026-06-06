import requests
import pandas as pd
from pymongo import MongoClient
from datetime import datetime
import pytz
from dotenv import load_dotenv
import os

# ==================================================
# LOAD ENV
# ==================================================
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB", "aqi_db")
COLLECTION_NAME = os.getenv("MONGO_COLLECTION", "raw_aqi_data")

LATITUDE = float(os.getenv("LATITUDE"))
LONGITUDE = float(os.getenv("LONGITUDE"))

# ==================================================
# CONNECT MONGO
# ==================================================
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

print("Connected to MongoDB")

# ==================================================
# TIMEZONE (IMPORTANT FIX)
# ==================================================
pakistan_tz = pytz.timezone("Asia/Karachi")
now = datetime.now(pakistan_tz)

date_str = now.strftime("%Y-%m-%d")

print("Running hourly pipeline for:", date_str)

# ==================================================
# FETCH AIR QUALITY DATA
# ==================================================
air_url = "https://air-quality-api.open-meteo.com/v1/air-quality"

air_params = {
    "latitude": LATITUDE,
    "longitude": LONGITUDE,
    "start_date": date_str,
    "end_date": date_str,
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

# ==================================================
# FETCH WEATHER DATA
# ==================================================
weather_url = "https://archive-api.open-meteo.com/v1/archive"

weather_params = {
    "latitude": LATITUDE,
    "longitude": LONGITUDE,
    "start_date": date_str,
    "end_date": date_str,
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

# ==================================================
# MERGE
# ==================================================
air_df["time"] = pd.to_datetime(air_df["time"])
weather_df["time"] = pd.to_datetime(weather_df["time"])

df = pd.merge(air_df, weather_df, on="time", how="inner")

# ==================================================
# CLEAN
# ==================================================
df = df.sort_values("time")
df = df.drop_duplicates(subset=["time"])

df = df.replace([float("inf"), float("-inf")], None)
df = df.ffill().bfill().dropna()

# ==================================================
# UPSERT TO MONGO (NO DUPLICATES)
# ==================================================

print("Uploading to MongoDB (UPSERT MODE)...")

count = 0

for record in df.to_dict(orient="records"):
    
    record["time"] = str(record["time"])

    collection.update_one(
        {
            "time": record["time"],
            "latitude": LATITUDE,
            "longitude": LONGITUDE
        },
        {"$set": record},
        upsert=True
    )

    count += 1

print(f"Inserted/Updated: {count}")
print("Hourly pipeline completed ✔")