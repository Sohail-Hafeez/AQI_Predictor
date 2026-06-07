# 🌫️ AQI Predictor — Rawalpindi Air Quality Forecast System

A **production-grade, end-to-end MLOps pipeline** that continuously ingests real-time air quality and weather data for Rawalpindi, Pakistan, trains machine learning models, and serves a **3-day AQI forecast** through an interactive Streamlit dashboard.

---

## 📌 Table of Contents

- [Project Overview](#-project-overview)
- [Architecture](#-architecture)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Setup & Installation](#-setup--installation)
- [Environment Variables](#-environment-variables)
- [Running Locally](#-running-locally)
- [CI/CD Pipelines](#-cicd-pipelines)
- [ML Models](#-ml-models)
- [Dashboard](#-dashboard)

---

## 📖 Project Overview

This project predicts the **Air Quality Index (AQI) for Rawalpindi** over the next 3 days using a fully automated ML pipeline:

1. **Hourly data ingestion** from Open-Meteo APIs (air quality + weather)
2. **Persistent storage** in MongoDB Atlas
3. **Daily model retraining** with ensemble ML models
4. **Live dashboard** powered by Streamlit

The system is designed for **zero human intervention** — GitHub Actions drives the entire schedule.

---

## 🏗️ Architecture

```
Open-Meteo API (Air Quality)  ─┐
                                ├──► hourlyDataPipeline.py ──► MongoDB Atlas
Open-Meteo API (Weather)      ─┘           │
                                            │  (raw_aqi_data collection)
                                            │
                                    Training.py (daily)
                                            │
                                    ┌───────┴────────┐
                                    │  ML Models     │
                                    │  (best_model)  │
                                    │  (ensemble)    │
                                    └───────┬────────┘
                                            │  (models collection in MongoDB)
                                            │
                                        app.py (Streamlit)
                                            │
                                    ┌───────┴────────────────┐
                                    │  3-Day AQI Forecast UI │
                                    └────────────────────────┘
```

---

## ✨ Features

- **Real-time data ingestion** — Fetches air quality (PM2.5, PM10, CO, NO₂, SO₂, O₃, methane, dust, AQI) and weather (temperature, humidity, pressure, wind speed) every hour via GitHub Actions
- **MongoDB Atlas storage** — All data is stored and queried from a cloud MongoDB database with upsert-based deduplication
- **Automated daily model training** — Three models (Linear Regression, Random Forest, Gradient Boosting) compete; the best is selected and an ensemble is also saved
- **3-day AQI forecast** — Predicts AQI for Day 1, Day 2, and Day 3 ahead from the latest sensor snapshot
- **Streamlit dashboard** — Interactive web UI with forecast cards, AQI categories, trend chart, and raw data explorer
- **Fully automated CI/CD** — Two GitHub Actions workflows handle ingestion (hourly) and training (daily) with no manual steps required

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Language** | Python 3.10 |
| **Data Source** | [Open-Meteo API](https://open-meteo.com/) (free, no key required) |
| **Database** | MongoDB Atlas |
| **ML Framework** | scikit-learn (RandomForest, GradientBoosting, VotingRegressor) |
| **Feature Engineering** | Lag features, rolling statistics, time features |
| **Dashboard** | Streamlit |
| **CI/CD** | GitHub Actions |
| **Secret Management** | GitHub Repository Secrets |

---

## 📁 Project Structure

```
AQI_Predictor/
│
├── .github/
│   └── workFlows/
│       ├── hourly.yml          # Hourly data ingestion pipeline
│       └── daily_train.yml     # Daily model retraining pipeline
│
├── hourlyDataPipeline.py       # Fetches + upserts latest hourly AQI & weather data
├── Training.py                 # Loads data from MongoDB, trains models, saves back to MongoDB
├── app.py                      # Streamlit dashboard (live AQI forecast UI)
│
├── HistoricalBackfill.py       # One-time historical data backfill script
├── dry_run.py                  # Test the pipeline without writing to any database
│
├── requirements.txt            # Python dependencies
├── .gitignore                  # Excludes .env, venv, *.pkl, etc.
└── README.md
```

---

## ⚙️ Setup & Installation

### Prerequisites

- Python 3.10+
- A [MongoDB Atlas](https://www.mongodb.com/atlas) account (free tier works)
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/Sohail-Hafeez/AQI_Predictor.git
cd AQI_Predictor
```

### 2. Create a Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 🔐 Environment Variables

Create a `.env` file in the project root (never commit this file):

```env
MONGO_URI=mongodb+srv://<user>:<password>@<cluster>.mongodb.net/
MONGO_DB=aqi_db
MONGO_COLLECTION=raw_aqi_data

LATITUDE=33.59839
LONGITUDE=73.04414
```

### GitHub Actions Secrets

For the CI/CD workflows to work, add the following secrets in your GitHub repository under **Settings → Secrets and variables → Actions**:

| Secret Name | Description |
|-------------|-------------|
| `MONGO_URI` | Your full MongoDB Atlas connection string |
| `LATITUDE` | Target location latitude (e.g. `33.59839`) |
| `LONGITUDE` | Target location longitude (e.g. `73.04414`) |

---

## 🚀 Running Locally

### Step 1 — Run Historical Backfill (first-time only)

Populates MongoDB with historical data from March–May 2026:

```bash
python HistoricalBackfill.py
```

### Step 2 — Run Training

Trains and saves models to MongoDB:

```bash
python Training.py
```

### Step 3 — Launch the Dashboard

```bash
streamlit run app.py
```

The dashboard will open at `http://localhost:8501`.

### Dry Run (no database write)

Test the data pipeline locally without touching MongoDB:

```bash
python dry_run.py
```

---

## 🤖 CI/CD Pipelines

### 1. Hourly Data Pipeline (`hourly.yml`)

**Trigger:** Every hour on the hour (`0 * * * *`) + manual dispatch

**Steps:**
1. Checkout repository
2. Setup Python 3.10
3. Install dependencies from `requirements.txt`
4. Validate no unsafe local paths in requirements
5. Run `hourlyDataPipeline.py` — fetches today's air quality & weather data and upserts into MongoDB

### 2. Daily Model Training (`daily_train.yml`)

**Trigger:** Every day at midnight UTC (`0 0 * * *`) + manual dispatch

**Steps:**
1. Checkout repository
2. Setup Python 3.10
3. Install dependencies from `requirements.txt`
4. Validate requirements safety
5. Run `Training.py` — retrains all models on the latest MongoDB data and saves updated models back to MongoDB
6. Auto-commits updated model artifact if changed

---

## 🧠 ML Models

Feature engineering is performed on the raw MongoDB data before training:

| Feature Type | Features |
|---|---|
| **Pollutants** | `pm10`, `pm2_5`, `carbon_monoxide`, `nitrogen_dioxide`, `sulphur_dioxide`, `ozone`, `methane`, `dust` |
| **Weather** | `temperature`, `humidity`, `pressure`, `wind_speed` |
| **Time** | `hour`, `day`, `month` |
| **Lag Features** | `aqi_lag_1`, `aqi_lag_2`, `aqi_lag_3`, `aqi_lag_6`, `aqi_lag_12`, `aqi_lag_24` |
| **Rolling Stats** | `aqi_roll_mean_3`, `aqi_roll_mean_6`, `aqi_roll_mean_24`, `aqi_roll_std_6` |

### Models Trained

| Model | Type |
|---|---|
| Linear Regression | Baseline |
| Random Forest (n=200, max_depth=12) | Tree ensemble |
| Gradient Boosting (n=200, lr=0.1) | Boosted ensemble |
| **Voting Regressor (RF + GBR + LR)** | **Final ensemble (always saved)** |

The **best individual model** (by R² score on 20% test set) and the **ensemble model** are both serialized and stored in the MongoDB `models` collection.

### Targets

| Target | Description |
|---|---|
| `t+1` | AQI forecast 1 hour ahead |
| `t+2` | AQI forecast 2 hours ahead |
| `t+3` | AQI forecast 3 hours ahead |

> In the dashboard context, these map to **Day 1**, **Day 2**, and **Day 3** forecasts.

---

## 📊 Dashboard

The Streamlit dashboard (`app.py`) provides:

- **3-Day AQI Forecast Cards** — Day 1, Day 2, Day 3 predictions with colour-coded labels
- **AQI Category Labels** — Good / Moderate / Unhealthy for Sensitive / Unhealthy / Hazardous
- **Trend Chart** — Line chart showing AQI trajectory over the 3-day horizon
- **Raw Data Explorer** — Expandable table showing the most recent 10 sensor readings

### AQI Scale Reference

| Range | Category |
|---|---|
| 0–50 | 😊 Good |
| 51–100 | 😐 Moderate |
| 101–150 | 😷 Unhealthy for Sensitive Groups |
| 151–200 | 🚨 Unhealthy |
| 201+ | ☠️ Hazardous |

---

## 📍 Location

This system is configured for **Rawalpindi, Pakistan** (Lat: 33.5984, Lon: 73.0441).

To change the target city, update the `LATITUDE` and `LONGITUDE` values in your `.env` file and GitHub Secrets.

---

## 📜 License

This project is for educational and research purposes.

---

*Built by the AQI Forecasting Team | Powered by Open-Meteo + MongoDB + scikit-learn + Streamlit*
