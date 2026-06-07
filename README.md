# 🌫️ AQI Predictor — Rawalpindi Air Quality Forecast System 

Live demo : [Click to view](https://10pearlsaqiproject.streamlit.app/)

<img width="1366" height="727" alt="image" src="https://github.com/user-attachments/assets/be6e794b-277f-4de2-b54d-372aa5b1979d" />


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

---

## 🚧 Issues Faced

This section documents the real-world challenges encountered during development and how each was resolved.

---

### 1. 📡 Data Source Limitations — OpenWeather & AQICN

**Problem:**
The project required historical AQI and pollutant data to build a meaningful training dataset. Two APIs were evaluated:

- **OpenWeather** — Provided historical data, but the historical endpoint is **paid** and not accessible on a free tier.
- **AQICN** — Only offered a **real-time snapshot** of current conditions. No historical data was available through its API.

**Resolution:**
Switched to the **[Open-Meteo API](https://open-meteo.com/)**, a completely free and open-source weather and air quality API. It provides:
- Hourly historical air quality data (PM2.5, PM10, CO, NO₂, SO₂, O₃, methane, dust, European AQI)
- Hourly historical and forecast weather data (temperature, humidity, pressure, wind speed)

This allowed building a rich multi-month historical dataset with no API cost or rate limiting constraints.

---

### 2. 🗄️ Hopsworks Feature Store — Hudi Table Materialization Failure

**Problem:**
The original design used **Hopsworks Feature Store** to store engineered features. Hopsworks normally auto-creates an offline Apache Hudi table when data is inserted into a feature group. However, in this project the Hudi table was never materialized, causing the following persistent error every time `fg.read()` was called:

```
FlightServerError: No hudi properties found for featuregroup:
/apps/hive/warehouse/.../aqi_features_7
This usually means that no data has been written yet to this feature group.
```

Investigation revealed that:
- The Spark materialization jobs were getting stuck in `SUBMITTED` state on the Hopsworks free-tier YARN cluster — never transitioning to `RUNNING`
- Multiple stale job executions from earlier versions (v3–v6) were clogging the cluster queue
- Even after stopping the stale jobs and waiting over 45 minutes, the cluster did not pick up the new executions

**Resolution:**
Abandoned Hopsworks Feature Store and migrated to **MongoDB Atlas** as the data persistence layer:
- Raw AQI + weather data is upserted hourly into a MongoDB collection
- Feature engineering is performed in-memory at training time
- Models are serialized and saved directly to a MongoDB `models` collection — no local file dependency

This eliminated all cloud cluster dependency issues and made the pipeline significantly more reliable.

---

### 3. 🔁 GitHub Actions — Stale `requirements.txt` Cache Bug

**Problem:**
After cleaning up the `requirements.txt` file (which previously contained a local path reference: `twofish @ file:///C:/Users/.../scratch/dummy_twofish`), the GitHub Actions CI/CD workflow kept failing with a dependency error — even after the bad line had been deleted and the fix was committed and pushed.

GitHub Actions was fetching and using an **older cached version** of `requirements.txt` that still contained the invalid local path, rather than the freshly committed version. This is unexpected behaviour — Actions should always use the file from the current commit.

```
ERROR: twofish @ file:///C:/Users/Mushaf/Desktop/AQI_Predictor/scratch/dummy_twofish
       does not appear to be a Python project
```

Neither clearing pip cache steps nor force-pushing resolved the issue.

**Resolution:**
The only working fix was to:
1. **Delete the entire GitHub repository**
2. Create a **fresh repository** with a clean history
3. Push all project files again to the new repo

After the fresh push with a clean `requirements.txt`, the GitHub Actions workflow ran successfully with no stale cache issues.

---

