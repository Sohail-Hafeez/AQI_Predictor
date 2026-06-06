import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import os

# ==================================================
# LOAD ENV
# ==================================================
load_dotenv()

LATITUDE = float(os.getenv("LATITUDE"))
LONGITUDE = float(os.getenv("LONGITUDE"))

# ==================================================
# CURRENT DATE (TEST MODE)
# ==================================================
now = datetime.utcnow()
start_date = now.strftime("%Y-%m-%d")
end_date = start_date

print("\n==============================")
print("HOURLY PIPELINE TEST MODE")
print("==============================\n")
print("Date:", start_date)

# ==================================================
# FETCH AIR QUALITY DATA
# ==================================================
print("\nFetching Air Quality data...")

air_url = "https://air-quality-api.open-meteo.com/v1/air-quality"

air_params = {
    "latitude": LATITUDE,
    "longitude": LONGITUDE,
    "start_date": start_date,
    "end_date": end_date,
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
print("\nFetching Weather data...")

weather_url = "https://archive-api.open-meteo.com/v1/archive"

weather_params = {
    "latitude": LATITUDE,
    "longitude": LONGITUDE,
    "start_date": start_date,
    "end_date": end_date,
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
# MERGE DATA
# ==================================================
print("\nMerging datasets...")

air_df["time"] = pd.to_datetime(air_df["time"])
weather_df["time"] = pd.to_datetime(weather_df["time"])

df = pd.merge(air_df, weather_df, on="time", how="inner")

# ==================================================
# CLEAN DATA
# ==================================================
print("Cleaning data...")

df = df.drop_duplicates(subset=["time"])
df = df.sort_values("time")

df = df.replace([float("inf"), float("-inf")], None)
df = df.ffill().bfill().dropna()

# ==================================================
# OUTPUT RESULT
# ==================================================
print("\n==============================")
print("FINAL OUTPUT (NO DATABASE)")
print("==============================\n")

print("Shape:", df.shape)
print("\nColumns:\n", list(df.columns))

print("\nSample Data:\n")
print(df.head(10).to_string(index=False))

print("\n==============================")
print("PIPELINE TEST COMPLETE ✔")
print("==============================")