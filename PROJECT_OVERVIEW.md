# AgriChain — Project Overview

> **Harvest Readiness Intelligence** for Indian farmers.  
> Helps farmers decide **when** to sell and **where** to sell for maximum profit with minimum spoilage.

---

## 🏗️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Streamlit 1.32+ | Multi-page dashboard UI |
| **Styling** | Custom HTML/CSS (injected via `st.markdown`) | Premium green/cream theme, responsive cards |
| **Data Processing** | Pandas 2.0 | CSV loading, filtering, aggregation |
| **ML Prediction** | scikit-learn (RandomForestRegressor) | 30-day price forecasting |
| **Weather API** | Open-Meteo (free, no key needed) | 5-day forecast + AQI + current conditions |
| **Air Quality API** | Open-Meteo Air Quality | AQI, PM2.5, PM10 data |
| **AI Chat** | Groq API (LLaMA 3.1 8B Instant) | Conversational AI advisor for farmers |
| **Maps** | Folium + streamlit-folium | Interactive mandi map with price heatmaps |
| **Charts** | Plotly 5.18+ | Price trend visualizations |
| **i18n** | Custom `translator.py` | English / Hindi / Marathi support |
| **Config** | python-dotenv | Secrets management via `.env` |

---

## 📊 Datasets

### 1. `data/mandi_prices.csv` (~736 KB)
The **primary working dataset** for price analysis.

| Column | Type | Description |
|--------|------|-------------|
| `Crop` | string | Crop name (e.g., Potato, Wheat, Tomato, Onion) |
| `Mandi` | string | Market name (e.g., Ahmednagar, Sangli, Pune) |
| `Date` | date | Price recording date (DD/MM/YYYY format) |
| `Price` | float | Price in ₹ per quintal |

- Used by: `price_analysis.py` for 7-day/30-day trend analysis
- Used by: `data_loader.py` for crop-mandi selection, top mandi ranking

### 2. `data/Agriculture_price_dataset.csv` (~55 MB)
A **large historical dataset** used exclusively for ML model training.

| Column | Type | Description |
|--------|------|-------------|
| `Commodity` | string | Crop/commodity name |
| `Market` | string | Market name |
| `Arrival_Date` | date | Date of price record |
| `Modal_Price` | float | Modal (most common) price in ₹/quintal |
| `Min_Price` | float | Minimum price |
| `Max_Price` | float | Maximum price |

- Used by: `price_predictor.py` for RandomForest model training
- Contains thousands of records across multiple crops and mandis in Maharashtra

---

## 🔄 Application Workflow

### Step-by-Step User Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│  USER selects: Crop → Mandi → Storage Type → Distance → [Calculate]│
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
              ┌────────────────────────────────┐
              │   1. PRICE ANALYSIS            │
              │   (price_analysis.py)          │
              │   • Load mandi_prices.csv      │
              │   • Filter by crop + mandi     │
              │   • Compute 7-day, 30-day avg  │
              │   • Compute % trend            │
              │   • Score: 0–30                │
              └────────────┬───────────────────┘
                           │
                           ▼
              ┌────────────────────────────────┐
              │   2. WEATHER SCORING           │
              │   (weather.py)                 │
              │   • Call Open-Meteo API        │
              │   • 5-day forecast + AQI       │
              │   • Penalize hot days (>35°C)  │
              │   • Penalize rainy days (>60%) │
              │   • Score: 0–30                │
              └────────────┬───────────────────┘
                           │
                           ▼
              ┌────────────────────────────────┐
              │   3. SCORING ENGINE            │
              │   (scoring.py)                 │
              │   • Storage score: 0–20        │
              │   • Transport score: 0–20      │
              │   • Weighted final: 0–100      │
              │     Price 40% + Weather 30%    │
              │     + Storage 20% + Transport  │
              │     10%                        │
              │   • Traffic light: 🟢🟡🔴      │
              └────────────┬───────────────────┘
                           │
                           ▼
              ┌────────────────────────────────┐
              │   4. EXPLANATION GENERATOR     │
              │   (explanation.py)             │
              │   • Farmer summary (plain text)│
              │   • Harvest window advice      │
              │   • "Why this recommendation?" │
              └────────────┬───────────────────┘
                           │
                           ▼
              ┌────────────────────────────────┐
              │   5. ML PRICE FORECAST         │
              │   (price_predictor.py)         │
              │   • Train RandomForest model   │
              │   • Feature engineering:       │
              │     lag, rolling mean, momentum│
              │   • Predict 7/14/30-day prices │
              │   • Autoregressive prediction  │
              │   • Confidence score           │
              └────────────┬───────────────────┘
                           │
                           ▼
              ┌────────────────────────────────┐
              │   6. AI CHAT ASSISTANT         │
              │   (ai_assistant.py)            │
              │   • Groq LLaMA 3.1 8B         │
              │   • Context = all scores +     │
              │     weather + prices           │
              │   • Multi-turn conversation    │
              │   • Hindi/English support      │
              └────────────────────────────────┘
```

---

## 📄 Pages (Multi-page Streamlit App)

| Page | File | What It Does |
|------|------|-------------|
| **Home** | `app.py` | Main dashboard — score card, price analysis, weather, ML forecast, AI chat |
| **Harvest Window** | `pages/1_🌾_Harvest.py` | Detailed harvest timing recommendations |
| **Mandi Ranker** | `pages/2_🏪_Mandi.py` | Compare prices across mandis, find best market to sell |
| **Spoilage Assessor** | `pages/3_⚠️_Spoilage.py` | Post-harvest spoilage risk assessment |
| **Spoilage Prevention** | `pages/2_Spoilage_Prevention.py` | Actionable steps to prevent crop spoilage |
| **Map Explorer** | `pages/4_Map_Explorer.py` | Interactive Folium map with mandi locations and price heatmap |

---

## 📁 Module Breakdown

### `modules/` — Core Business Logic

| Module | Role | Key Functions |
|--------|------|--------------|
| `data_loader.py` | Central data access layer | `load_price_df()`, `get_all_crops()`, `get_mandis_for_crop()`, `get_mandi_coords()` |
| `price_analysis.py` | Price trend calculation | `analyse_prices(crop, mandi)` → returns 7/30-day avg, trend %, score/30 |
| `weather.py` | Live weather + AQI | `get_weather_score(lat, lon)` → 5-day forecast, current conditions, AQI, score/30 |
| `scoring.py` | Composite scoring engine | `generate_score()` → storage/20 + transport/20 + final/100 + traffic light |
| `explanation.py` | Human-readable text | `generate_explanation()`, `generate_farmer_summary()`, `generate_harvest_window()` |
| `price_predictor.py` | ML forecasting | `predict_future_prices(crop, mandi)` → 30-day forecast with confidence |
| `ai_assistant.py` | Groq LLM chat | `get_ai_response()` → contextual farming advice |
| `spoilage_assessor.py` | Spoilage risk scoring | `assess_spoilage()` → risk %, actions, preservation tips |
| `mandi_ranker.py` | Multi-mandi comparison | Ranks mandis by profitability |
| `map_utils.py` | Folium map builder | Interactive map with price markers |
| `harvest_engine.py` | Harvest timing logic | Engine for optimal harvest window |
| `agri_data.py` | Agricultural reference data | Crop info, growing seasons, perishability |

### `utils/` — Shared Utilities

| Utility | Role |
|---------|------|
| `translator.py` | English ↔ Hindi ↔ Marathi translations (18K+ characters of translation maps) |
| `sidebar.py` | Shared sidebar navigation + language selector |
| `geo.py` | District → (lat, lon) coordinate mapping |
| `geo_translate.py` | Transliteration for geographic names |
| `green_theme.py` | Shared CSS theme |
| `banner.py` | Reusable page header |
| `shared_state.py` | Cross-page session state management |
| `map_selector.py` | Map location picker widget |

---

## 🧮 Scoring Formula

```
Final Score = (Price/30 × 40%) + (Weather/30 × 30%) + (Storage/20 × 20%) + (Transport/20 × 10%)
```

| Component | Max Score | Weight | Source |
|-----------|----------|--------|--------|
| **Price** | 30 | 40% | 7-day vs 30-day price trend |
| **Weather** | 30 | 30% | Penalties for hot (>35°C) and rainy (>60%) days |
| **Storage** | 20 | 20% | Cold storage=20, Warehouse=15, Shed=10, Open=5, None=0 |
| **Transport** | 20 | 10% | Distance bands: ≤50km=20, ≤150km=15, ≤300km=10, ≤500km=5 |

### Traffic Light
- 🟢 **Green** (≥70): Good time to sell
- 🟡 **Yellow** (40–69): Monitor conditions
- 🔴 **Red** (<40): Hold — wait for better prices

---

## 🤖 ML Price Prediction Pipeline

1. **Data**: Loads `Agriculture_price_dataset.csv` (55 MB)
2. **Feature Engineering** (15 features):
   - Temporal: `day_of_year`, `month`, `day_of_week`, `week_of_year`
   - Trend: linear trend counter
   - Lag features: `lag_7`, `lag_14`, `lag_30`
   - Rolling stats: `roll_mean_7`, `roll_std_7`, `roll_mean_14`, `roll_mean_30`
   - Momentum: `momentum_7`, `momentum_14`, `price_spread` (max - min)
3. **Model**: `RandomForestRegressor` (100 trees, max_depth=15)
4. **Prediction**: Autoregressive — each day's prediction feeds into the next day's features
5. **Output**: 7/14/30-day price forecasts with confidence intervals and trend direction

---

## 🌐 External APIs Used

| API | URL | Auth | Data |
|-----|-----|------|------|
| Open-Meteo Forecast | `api.open-meteo.com/v1/forecast` | None (free) | Temperature, humidity, wind, UV, precipitation |
| Open-Meteo AQI | `air-quality-api.open-meteo.com/v1/air-quality` | None (free) | US AQI, PM2.5, PM10 |
| Groq LLM | `api.groq.com` | API key required | LLaMA 3.1 8B Instant for AI chat |

---

## 🚀 How to Run

```bash
# 1. Clone and enter the repo
git clone https://github.com/samyakg051-creator/SI.git
cd SI

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set environment variable
# Create .env file with:
# GROQ_API_KEY=your_groq_api_key_here

# 5. Run
streamlit run app.py
```
