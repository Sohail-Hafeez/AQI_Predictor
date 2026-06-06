import streamlit as st
import pandas as pd
import numpy as np
import joblib
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# ==================================================
# PAGE CONFIG (DARK THEME)
# ==================================================
st.set_page_config(
    page_title="AQI Predictor - Rawalpindi",
    page_icon="🌫️",
    layout="centered"
)

st.markdown("""
    <style>
    body {
        background-color: #0e1117;
        color: white;
    }
    .main {
        background-color: #0e1117;
    }
    </style>
""", unsafe_allow_html=True)

# ==================================================
# TITLE
# ==================================================
st.title("🌫️ AQI Predictor - Rawalpindi")
st.markdown("### 3-Day Air Quality Forecast System")

# ==================================================
# LOAD MODEL
# ==================================================
model = joblib.load("best_model.pkl")

# ==================================================
# CONNECT MONGO
# ==================================================
load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("MONGO_DB", "aqi_db")]
collection = db[os.getenv("MONGO_COLLECTION", "raw_aqi_data")]

# ==================================================
# FETCH DATA
# ==================================================
@st.cache_data
def load_data():
    data = list(collection.find())
    df = pd.DataFrame(data)
    df["time"] = pd.to_datetime(df["time"])
    df = df.sort_values("time")
    return df

df = load_data()

# ==================================================
# FEATURE ENGINEERING (same as training)
# ==================================================

def create_features(df):
    df = df.copy()

    for lag in [1, 2, 3, 6, 12, 24]:
        df[f"aqi_lag_{lag}"] = df["aqi"].shift(lag)

    df["aqi_roll_mean_3"] = df["aqi"].rolling(3).mean()
    df["aqi_roll_mean_6"] = df["aqi"].rolling(6).mean()
    df["aqi_roll_mean_24"] = df["aqi"].rolling(24).mean()

    df["aqi_roll_std_6"] = df["aqi"].rolling(6).std()

    df["hour"] = df["time"].dt.hour
    df["day"] = df["time"].dt.day
    df["month"] = df["time"].dt.month

    df = df.dropna()

    return df

df_feat = create_features(df)

# ==================================================
# GET LATEST ROW
# ==================================================
latest = df_feat.iloc[-1:]

features = [
    "pm10", "pm2_5", "carbon_monoxide", "nitrogen_dioxide",
    "sulphur_dioxide", "ozone", "methane", "dust",
    "temperature", "humidity", "pressure", "wind_speed",
    "hour", "day", "month",
    "aqi_lag_1", "aqi_lag_2", "aqi_lag_3",
    "aqi_lag_6", "aqi_lag_12", "aqi_lag_24",
    "aqi_roll_mean_3", "aqi_roll_mean_6", "aqi_roll_mean_24",
    "aqi_roll_std_6"
]

X_latest = latest[features]

# ==================================================
# PREDICTION
# ==================================================
pred = model.predict(X_latest)[0]

day1, day2, day3 = pred

# ==================================================
# DISPLAY RESULTS
# ==================================================

st.markdown("## 📍 Location: Rawalpindi")

st.markdown("### 📊 3-Day Forecast")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Day 1 AQI", f"{day1:.2f}")

with col2:
    st.metric("Day 2 AQI", f"{day2:.2f}")

with col3:
    st.metric("Day 3 AQI", f"{day3:.2f}")

# ==================================================
# AQI CATEGORY FUNCTION
# ==================================================
def aqi_category(value):
    if value <= 50:
        return "Good 😊"
    elif value <= 100:
        return "Moderate 😐"
    elif value <= 150:
        return "Unhealthy for Sensitive 😷"
    elif value <= 200:
        return "Unhealthy 🚨"
    else:
        return "Hazardous ☠️"

st.markdown("### 🏷️ Air Quality Status")

st.write("Day 1:", aqi_category(day1))
st.write("Day 2:", aqi_category(day2))
st.write("Day 3:", aqi_category(day3))

# ==================================================
# RAW DATA EXPANDER
# ==================================================
with st.expander("📂 View Latest Data"):
    st.dataframe(df_feat.tail(10))