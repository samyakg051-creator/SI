"""
AgriChain – modules/price_predictor.py
ML-based price prediction using RandomForest on Agriculture_price_dataset.csv.

Trains a separate model per (Commodity, Market) pair, cached for the session.
Uses iterative (autoregressive) prediction so each day's forecast feeds
into the next day's features, producing realistically evolving prices.
"""

from __future__ import annotations
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import streamlit as st

try:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import StandardScaler
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

# Path to the larger agriculture dataset (737k rows, all-India)
AGRI_CSV = Path(__file__).resolve().parent.parent / "data" / "Agriculture_price_dataset.csv"


# ── Feature engineering ──────────────────────────────────────────────────────

def _build_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values("Date").copy()
    df["day_of_year"]  = df["Date"].dt.dayofyear
    df["month"]        = df["Date"].dt.month
    df["day_of_week"]  = df["Date"].dt.dayofweek
    df["week_of_year"] = df["Date"].dt.isocalendar().week.astype(int)
    df["trend"]        = np.arange(len(df))

    df["lag_7"]  = df["Price"].shift(7)
    df["lag_14"] = df["Price"].shift(14)
    df["lag_30"] = df["Price"].shift(30)

    df["roll_mean_7"]  = df["Price"].rolling(7,  min_periods=1).mean()
    df["roll_std_7"]   = df["Price"].rolling(7,  min_periods=1).std().fillna(0)
    df["roll_mean_14"] = df["Price"].rolling(14, min_periods=1).mean()
    df["roll_mean_30"] = df["Price"].rolling(30, min_periods=1).mean()

    df["momentum_7"]  = df["Price"] - df["roll_mean_7"]
    df["momentum_14"] = df["Price"] - df["roll_mean_14"]

    if "Min_Price" in df.columns and "Max_Price" in df.columns:
        df["price_spread"] = df["Max_Price"] - df["Min_Price"]
    else:
        df["price_spread"] = 0

    df = df.dropna()
    return df


FEATURE_COLS = [
    "day_of_year", "month", "day_of_week", "week_of_year", "trend",
    "lag_7", "lag_14", "lag_30",
    "roll_mean_7", "roll_std_7", "roll_mean_14", "roll_mean_30",
    "momentum_7", "momentum_14", "price_spread",
]


# ── Cached data loader ───────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def _load_agri_data():
    if not AGRI_CSV.exists():
        return None
    df = pd.read_csv(AGRI_CSV)
    df.columns = [c.strip() for c in df.columns]
    for col in ["STATE", "District Name", "Market Name", "Commodity"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    for col in ["Min_Price", "Max_Price", "Modal_Price"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "Price Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Price Date"], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["Modal_Price", "Date"])
    return df


# ── Model training (cached per session) ──────────────────────────────────────

@st.cache_resource(show_spinner=False)
def _train_model(crop: str, mandi: str):
    if not HAS_SKLEARN:
        return None, None, None

    full_df = _load_agri_data()
    if full_df is None:
        return None, None, None

    sub = full_df[
        (full_df["Commodity"].str.lower() == crop.lower()) &
        (full_df["Market Name"].str.lower() == mandi.lower())
    ].copy()

    if len(sub) < 30:
        sub = full_df[
            (full_df["Commodity"].str.lower() == crop.lower()) &
            (full_df["Market Name"].str.contains(mandi.split("(")[0].strip(), case=False, na=False))
        ].copy()

    if len(sub) < 30:
        return None, None, None

    sub = sub.rename(columns={"Modal_Price": "Price"})
    sub = sub[["Date", "Price", "Min_Price", "Max_Price"]].copy()

    featured = _build_features(sub)
    if len(featured) < 20:
        return None, None, None

    X = featured[FEATURE_COLS].values
    y = featured["Price"].values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = RandomForestRegressor(
        n_estimators=100, max_depth=12, min_samples_leaf=3,
        random_state=42, n_jobs=-1,
    )
    model.fit(X_scaled, y)

    last_data = featured[["Date", "Price"] + FEATURE_COLS].tail(60).copy()
    return model, scaler, last_data


# ── Iterative (autoregressive) prediction ────────────────────────────────────

def _predict_iterative(model, scaler, last_data, days_ahead):
    last_date   = last_data["Date"].iloc[-1]
    last_trend  = last_data["trend"].iloc[-1]
    last_spread = float(last_data["price_spread"].iloc[-1]) if "price_spread" in last_data.columns else 0
    prices      = last_data["Price"].tolist()

    future_dates, mean_preds, std_preds = [], [], []

    for i in range(1, days_ahead + 1):
        fdate = last_date + timedelta(days=i)
        future_dates.append(fdate)

        feat = {
            "day_of_year":  fdate.timetuple().tm_yday,
            "month":        fdate.month,
            "day_of_week":  fdate.weekday(),
            "week_of_year": fdate.isocalendar()[1],
            "trend":        last_trend + i,
            "lag_7":        prices[-7]  if len(prices) >= 7  else prices[-1],
            "lag_14":       prices[-14] if len(prices) >= 14 else prices[-1],
            "lag_30":       prices[-30] if len(prices) >= 30 else prices[-1],
            "roll_mean_7":  np.mean(prices[-7:]),
            "roll_std_7":   float(np.std(prices[-7:])) if len(prices) >= 2 else 0,
            "roll_mean_14": np.mean(prices[-14:]),
            "roll_mean_30": np.mean(prices[-30:]),
            "momentum_7":   prices[-1] - np.mean(prices[-7:]),
            "momentum_14":  prices[-1] - np.mean(prices[-14:]),
            "price_spread": last_spread,
        }

        X_row = np.array([[feat[c] for c in FEATURE_COLS]])
        X_scaled = scaler.transform(X_row)

        tree_vals = np.array([tree.predict(X_scaled)[0] for tree in model.estimators_])
        pred_mean = float(tree_vals.mean())
        pred_std  = float(tree_vals.std())

        mean_preds.append(pred_mean)
        std_preds.append(pred_std)
        prices.append(pred_mean)  # feed prediction back for next day

    return future_dates, mean_preds, std_preds


# ── Public API ───────────────────────────────────────────────────────────────

def predict_future_prices(crop: str, mandi: str, days_ahead: int = 30) -> dict | None:
    if not HAS_SKLEARN:
        return None

    model, scaler, last_data = _train_model(crop, mandi)
    if model is None:
        return None

    future_dates, mean_preds, std_preds = _predict_iterative(model, scaler, last_data, days_ahead)
    current_price = float(last_data["Price"].iloc[-1])

    predictions = []
    for i, (dt, pred) in enumerate(zip(future_dates, mean_preds)):
        predictions.append({
            "date": dt.strftime("%b %d, %Y"),
            "price": round(float(pred), 0),
            "low":   round(float(max(pred - 1.96 * std_preds[i], 0)), 0),
            "high":  round(float(pred + 1.96 * std_preds[i]), 0),
        })

    price_7d  = float(mean_preds[min(6,  len(mean_preds)-1)])
    price_14d = float(mean_preds[min(13, len(mean_preds)-1)])
    price_30d = float(mean_preds[min(29, len(mean_preds)-1)])

    if price_7d > current_price * 1.02:
        trend = "up"
    elif price_7d < current_price * 0.98:
        trend = "down"
    else:
        trend = "stable"

    X_train = scaler.transform(last_data[FEATURE_COLS].values)
    r2 = model.score(X_train, last_data["Price"].values)
    confidence = round(max(min(r2 * 100, 99), 50), 1)

    history = []
    for _, row in last_data.tail(30).iterrows():
        history.append({"date": row["Date"].strftime("%b %d"), "price": round(float(row["Price"]), 0)})

    return {
        "predictions": predictions,
        "current_price": round(current_price, 0),
        "price_7d": round(price_7d, 0),
        "price_14d": round(price_14d, 0),
        "price_30d": round(price_30d, 0),
        "trend_direction": trend,
        "confidence": confidence,
        "history": history,
        "data_points": len(last_data),
    }
