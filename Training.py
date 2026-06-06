import pandas as pd
import numpy as np
from pymongo import MongoClient
import joblib

from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.multioutput import MultiOutputRegressor
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, VotingRegressor
from sklearn.linear_model import LinearRegression

from dotenv import load_dotenv
import os

# ==================================================
# LOAD ENV + MONGO
# ==================================================
load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("MONGO_DB", "aqi_db")]
collection = db[os.getenv("MONGO_COLLECTION", "raw_aqi_data")]

print("Loading data...")

df = pd.DataFrame(list(collection.find()))

df["time"] = pd.to_datetime(df["time"])
df = df.sort_values("time").reset_index(drop=True)

# ==================================================
# FEATURE ENGINEERING (TIME SERIES)
# ==================================================

for lag in [1, 2, 3, 6, 12, 24]:
    df[f"aqi_lag_{lag}"] = df["aqi"].shift(lag)

df["aqi_roll_mean_3"] = df["aqi"].rolling(3).mean()
df["aqi_roll_mean_6"] = df["aqi"].rolling(6).mean()
df["aqi_roll_mean_24"] = df["aqi"].rolling(24).mean()

df["aqi_roll_std_6"] = df["aqi"].rolling(6).std()

df["hour"] = df["time"].dt.hour
df["day"] = df["time"].dt.day
df["month"] = df["time"].dt.month

# ==================================================
# TARGET (3-DAY FORECAST)
# ==================================================
df["t+1"] = df["aqi"].shift(-1)
df["t+2"] = df["aqi"].shift(-2)
df["t+3"] = df["aqi"].shift(-3)

df = df.dropna().reset_index(drop=True)

# ==================================================
# FEATURES & TARGET
# ==================================================

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

X = df[features]
y = df[["t+1", "t+2", "t+3"]]

# ==================================================
# TRAIN TEST SPLIT (NO SHUFFLE)
# ==================================================
split = int(len(df) * 0.8)

X_train, X_test = X.iloc[:split], X.iloc[split:]
y_train, y_test = y.iloc[:split], y.iloc[split:]

# ==================================================
# MODELS
# ==================================================

models = {
    "linear": MultiOutputRegressor(LinearRegression()),
    
    "rf": MultiOutputRegressor(
        RandomForestRegressor(n_estimators=200, max_depth=12, random_state=42)
    ),
    
    "gbr": MultiOutputRegressor(
        GradientBoostingRegressor(n_estimators=200, learning_rate=0.1, max_depth=5)
    )
}

# ==================================================
# TRAIN + EVALUATE
# ==================================================

def evaluate_model(name, model):
    model.fit(X_train, y_train)
    preds = model.predict(X_test)

    mse = mean_squared_error(y_test, preds)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_test, preds)

    print(f"\n{name.upper()} RESULTS")
    print("MSE :", mse)
    print("RMSE:", rmse)
    print("R2  :", r2)

    return model, r2

results = {}

for name, model in models.items():
    trained_model, score = evaluate_model(name, model)
    results[name] = (trained_model, score)

# ==================================================
# BEST MODEL SELECTION
# ==================================================

best_model_name = max(results, key=lambda k: results[k][1])
best_model = results[best_model_name][0]

print("\nBEST MODEL:", best_model_name)

# ==================================================
# ENSEMBLE MODEL (Voting Regressor)
# ==================================================

ensemble = MultiOutputRegressor(
    VotingRegressor([
        ("rf", RandomForestRegressor(n_estimators=200, random_state=42)),
        ("gbr", GradientBoostingRegressor(n_estimators=200, random_state=42)),
        ("lr", LinearRegression())
    ])
)

ensemble.fit(X_train, y_train)

ensemble_preds = ensemble.predict(X_test)

ens_mse = mean_squared_error(y_test, ensemble_preds)
ens_rmse = np.sqrt(ens_mse)
ens_r2 = r2_score(y_test, ensemble_preds)

print("\nENSEMBLE RESULTS")
print("MSE :", ens_mse)
print("RMSE:", ens_rmse)
print("R2  :", ens_r2)

# ==================================================
# SAVE BEST MODEL + ENSEMBLE
# ==================================================

joblib.dump(best_model, "best_model.pkl")
joblib.dump(ensemble, "ensemble_model.pkl")

print("\nModels saved ✔")