import streamlit as st
import pandas as pd
import numpy as np
import pickle
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
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:ital,wght@0,400;0,700;1,400&family=Syne:wght@400;600;700;800&display=swap');

    /* ── Reset & Base ── */
    html, body, [class*="css"] {
        font-family: 'Syne', sans-serif;
        background-color: #080c12;
        color: #c8d6e8;
    }
    .stApp {
        background-color: #080c12;
        background-image:
            radial-gradient(ellipse 80% 50% at 50% -10%, rgba(32,80,140,0.28) 0%, transparent 70%),
            repeating-linear-gradient(
                0deg,
                transparent,
                transparent 39px,
                rgba(255,255,255,0.018) 39px,
                rgba(255,255,255,0.018) 40px
            ),
            repeating-linear-gradient(
                90deg,
                transparent,
                transparent 39px,
                rgba(255,255,255,0.018) 39px,
                rgba(255,255,255,0.018) 40px
            );
    }
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 4rem;
        max-width: 780px;
    }

    /* ── Hero Header ── */
    .hero-block {
        position: relative;
        margin-bottom: 2.5rem;
        padding: 2.8rem 2.4rem 2.2rem;
        border: 1px solid rgba(80,140,220,0.22);
        border-radius: 4px;
        background: linear-gradient(135deg, rgba(12,22,40,0.9) 0%, rgba(8,14,26,0.96) 100%);
        overflow: hidden;
    }
    .hero-block::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent 0%, #2e7ddb 35%, #5eb8ff 60%, transparent 100%);
    }
    .hero-block::after {
        content: 'AQI';
        position: absolute;
        right: 1.8rem; top: 50%;
        transform: translateY(-50%);
        font-family: 'Space Mono', monospace;
        font-size: 7rem;
        font-weight: 700;
        color: rgba(46,125,219,0.07);
        letter-spacing: -0.04em;
        pointer-events: none;
        user-select: none;
    }
    .hero-eyebrow {
        font-family: 'Space Mono', monospace;
        font-size: 0.65rem;
        letter-spacing: 0.22em;
        color: #2e7ddb;
        text-transform: uppercase;
        margin-bottom: 0.55rem;
    }
    .hero-title {
        font-size: 2.1rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        color: #e8f0fc;
        line-height: 1.15;
        margin-bottom: 0.4rem;
    }
    .hero-sub {
        font-family: 'Space Mono', monospace;
        font-size: 0.72rem;
        color: #607a9e;
        letter-spacing: 0.06em;
    }

    /* ── Section Label ── */
    .section-label {
        font-family: 'Space Mono', monospace;
        font-size: 0.6rem;
        letter-spacing: 0.28em;
        color: #2e7ddb;
        text-transform: uppercase;
        margin-bottom: 0.9rem;
        padding-left: 0.8rem;
        border-left: 2px solid #2e7ddb;
    }

    /* ── Forecast Cards ── */
    .forecast-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
        margin-bottom: 2rem;
    }
    .forecast-card {
        position: relative;
        background: linear-gradient(160deg, rgba(14,26,48,0.95) 0%, rgba(8,14,28,0.98) 100%);
        border: 1px solid rgba(60,110,190,0.2);
        border-radius: 4px;
        padding: 1.5rem 1.2rem 1.3rem;
        text-align: center;
        overflow: hidden;
        transition: border-color 0.25s ease, transform 0.2s ease;
    }
    .forecast-card:hover {
        border-color: rgba(94,184,255,0.4);
        transform: translateY(-2px);
    }
    .forecast-card::before {
        content: '';
        position: absolute;
        bottom: 0; left: 0; right: 0;
        height: 2px;
    }
    .fc-day {
        font-family: 'Space Mono', monospace;
        font-size: 0.6rem;
        letter-spacing: 0.2em;
        color: #5c7a9e;
        text-transform: uppercase;
        margin-bottom: 0.9rem;
    }
    .fc-value {
        font-family: 'Space Mono', monospace;
        font-size: 2.4rem;
        font-weight: 700;
        line-height: 1;
        margin-bottom: 0.3rem;
    }
    .fc-unit {
        font-family: 'Space Mono', monospace;
        font-size: 0.55rem;
        color: #465e7a;
        letter-spacing: 0.15em;
        text-transform: uppercase;
    }

    /* AQI Color Tiers */
    .tier-good       { color: #34d399; }
    .tier-moderate   { color: #fbbf24; }
    .tier-sensitive  { color: #f97316; }
    .tier-unhealthy  { color: #ef4444; }
    .tier-hazardous  { color: #a855f7; }

    .bar-good       { background: linear-gradient(90deg, #34d399, transparent); }
    .bar-moderate   { background: linear-gradient(90deg, #fbbf24, transparent); }
    .bar-sensitive  { background: linear-gradient(90deg, #f97316, transparent); }
    .bar-unhealthy  { background: linear-gradient(90deg, #ef4444, transparent); }
    .bar-hazardous  { background: linear-gradient(90deg, #a855f7, transparent); }

    /* ── Status Panel ── */
    .status-panel {
        background: rgba(10,18,34,0.9);
        border: 1px solid rgba(60,110,190,0.18);
        border-radius: 4px;
        overflow: hidden;
        margin-bottom: 2rem;
    }
    .status-row {
        display: flex;
        align-items: center;
        gap: 1.1rem;
        padding: 1rem 1.4rem;
        border-bottom: 1px solid rgba(40,70,120,0.18);
        transition: background 0.2s ease;
    }
    .status-row:last-child { border-bottom: none; }
    .status-row:hover { background: rgba(30,60,110,0.12); }
    .status-day-badge {
        font-family: 'Space Mono', monospace;
        font-size: 0.58rem;
        letter-spacing: 0.16em;
        color: #465e7a;
        text-transform: uppercase;
        min-width: 46px;
    }
    .status-bar-wrap {
        flex: 1;
        height: 3px;
        background: rgba(255,255,255,0.04);
        border-radius: 2px;
        overflow: hidden;
    }
    .status-bar-fill {
        height: 100%;
        border-radius: 2px;
    }
    .status-label {
        font-size: 0.8rem;
        font-weight: 600;
        min-width: 200px;
        text-align: right;
    }

    /* ── Location Tag ── */
    .location-tag {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        font-family: 'Space Mono', monospace;
        font-size: 0.65rem;
        letter-spacing: 0.12em;
        color: #607a9e;
        background: rgba(30,60,110,0.18);
        border: 1px solid rgba(60,110,190,0.2);
        border-radius: 3px;
        padding: 0.35rem 0.75rem;
        margin-bottom: 2rem;
    }
    .location-dot {
        width: 6px; height: 6px;
        border-radius: 50%;
        background: #2e7ddb;
        box-shadow: 0 0 6px #2e7ddb;
        animation: pulse-dot 2.2s ease-in-out infinite;
    }
    @keyframes pulse-dot {
        0%, 100% { opacity: 1; transform: scale(1); }
        50%       { opacity: 0.4; transform: scale(0.7); }
    }

    /* ── Divider ── */
    .styled-divider {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(60,110,190,0.3) 30%, rgba(60,110,190,0.3) 70%, transparent);
        margin: 2rem 0;
    }

    /* ── Expander ── */
    .streamlit-expanderHeader {
        font-family: 'Space Mono', monospace !important;
        font-size: 0.68rem !important;
        letter-spacing: 0.18em !important;
        color: #607a9e !important;
        background: rgba(10,18,34,0.8) !important;
        border: 1px solid rgba(60,110,190,0.18) !important;
        border-radius: 4px !important;
        text-transform: uppercase !important;
    }
    .streamlit-expanderContent {
        background: rgba(8,12,22,0.9) !important;
        border: 1px solid rgba(60,110,190,0.12) !important;
        border-top: none !important;
        border-radius: 0 0 4px 4px !important;
    }

    /* ── DataFrame ── */
    .stDataFrame {
        border: 1px solid rgba(60,110,190,0.18) !important;
        border-radius: 4px !important;
        overflow: hidden;
    }
    .stDataFrame table { background: transparent !important; }
    .stDataFrame th {
        font-family: 'Space Mono', monospace !important;
        font-size: 0.6rem !important;
        letter-spacing: 0.12em !important;
        color: #2e7ddb !important;
        background: rgba(14,26,48,0.9) !important;
        text-transform: uppercase !important;
    }
    .stDataFrame td {
        font-family: 'Space Mono', monospace !important;
        font-size: 0.72rem !important;
        color: #8faac8 !important;
        background: rgba(8,14,26,0.8) !important;
    }

    /* Hide default Streamlit decorations */
    #MainMenu, footer, header { visibility: hidden; }
    .stDeployButton { display: none; }
    </style>
""", unsafe_allow_html=True)

# ==================================================
# LOAD ENV / SECRETS
# ==================================================
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB", "aqi_db")
MODEL_COLLECTION = "models"
DATA_COLLECTION = os.getenv("MONGO_COLLECTION", "raw_aqi_data")

# ==================================================
# CONNECT MONGO
# ==================================================
@st.cache_resource
def connect_mongo():
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    return db

db = connect_mongo()
model_collection = db[MODEL_COLLECTION]
data_collection = db[DATA_COLLECTION]

# ==================================================
# LOAD MODEL FROM MONGO (NO LOCAL FILE)
# ==================================================
@st.cache_resource
def load_model():
    doc = model_collection.find_one({"_id": "best_model"})
    if not doc:
        st.error("Model not found in MongoDB!")
        st.stop()
    model_bytes = doc["model"]
    model = pickle.loads(model_bytes)
    return model

model = load_model()

# ==================================================
# FETCH DATA
# ==================================================
@st.cache_data
def load_data():
    data = list(data_collection.find())
    df = pd.DataFrame(data)
    if "_id" in df.columns:
        df = df.drop(columns=["_id"])
    df["time"] = df["time"] = pd.to_datetime(df["time"], format="mixed", utc=True)
    df = df.sort_values("time")
    return df

df = load_data()

# ==================================================
# FEATURE ENGINEERING
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
    return df.dropna()

df_feat = create_features(df)

# ==================================================
# LATEST ROW
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
# AQI CATEGORY LOGIC (UNCHANGED)
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

# ==================================================
# UI HELPERS
# ==================================================
def aqi_tier_class(value):
    if value <= 50:   return "good"
    if value <= 100:  return "moderate"
    if value <= 150:  return "sensitive"
    if value <= 200:  return "unhealthy"
    return "hazardous"

def aqi_bar_pct(value):
    return min(int((value / 300) * 100), 100)

# ==================================================
# RENDER UI
# ==================================================

# Hero
st.markdown("""
<div class="hero-block">
    <div class="hero-eyebrow">Environmental Intelligence System</div>
    <div class="hero-title">Air Quality Predictor</div>
    <div class="hero-sub">RAWALPINDI · 3-DAY FORECAST · MACHINE LEARNING MODEL</div>
</div>
""", unsafe_allow_html=True)

# Location tag
st.markdown("""
<div class="location-tag">
    <span class="location-dot"></span>
    RAWALPINDI, PUNJAB · PAKISTAN
</div>
""", unsafe_allow_html=True)

# Forecast Cards
t1 = aqi_tier_class(day1)
t2 = aqi_tier_class(day2)
t3 = aqi_tier_class(day3)

st.markdown('<div class="section-label">3-Day AQI Forecast</div>', unsafe_allow_html=True)

st.markdown(f"""
<div class="forecast-grid">
    <div class="forecast-card">
        <div class="fc-day">Day 01</div>
        <div class="fc-value tier-{t1}">{day1:.0f}</div>
        <div class="fc-unit">AQI Index</div>
        <div class="forecast-card" style="position:absolute;bottom:0;left:0;right:0;height:2px;padding:0;border:none;border-radius:0;" class="bar-{t1}"></div>
    </div>
    <div class="forecast-card">
        <div class="fc-day">Day 02</div>
        <div class="fc-value tier-{t2}">{day2:.0f}</div>
        <div class="fc-unit">AQI Index</div>
    </div>
    <div class="forecast-card">
        <div class="fc-day">Day 03</div>
        <div class="fc-value tier-{t3}">{day3:.0f}</div>
        <div class="fc-unit">AQI Index</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Status panel
st.markdown('<div class="section-label">Air Quality Status</div>', unsafe_allow_html=True)

days_data = [
    ("DAY 01", day1, aqi_category(day1), t1),
    ("DAY 02", day2, aqi_category(day2), t2),
    ("DAY 03", day3, aqi_category(day3), t3),
]

rows_html = ""
for label, val, cat, tier in days_data:
    pct = aqi_bar_pct(val)
    rows_html += f"""
    <div class="status-row">
        <div class="status-day-badge">{label}</div>
        <div class="status-bar-wrap">
            <div class="status-bar-fill bar-{tier}" style="width:{pct}%"></div>
        </div>
        <div class="status-label tier-{tier}">{cat}</div>
    </div>"""

st.markdown(f'<div class="status-panel">{rows_html}</div>', unsafe_allow_html=True)

# Divider
st.markdown('<hr class="styled-divider">', unsafe_allow_html=True)

# Raw data expander (logic unchanged)
with st.expander("▸  RAW SENSOR DATA — LATEST 10 RECORDS"):
    st.dataframe(df_feat.tail(10))