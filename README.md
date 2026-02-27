# 🌾 AgriChain — Farm-to-Market Intelligence

AgriChain is a **Streamlit-based agricultural decision support system** that helps Indian farmers maximize harvest profits by combining real-time weather data, market prices, and ML predictions.

## ✨ Features

| Page | Description |
|------|-------------|
| 🏠 **Home** | Harvest Readiness Score (0–100) combining price, weather, storage & transport factors. AI chatbot for farming advice. |
| 🌾 **Harvest Window** | Recommends the optimal 5-day harvest window using weather forecasts + seasonal price trends. |
| 🏪 **Mandi Ranker** | Ranks nearby mandis by **net profit after transport cost** — find where to sell for maximum return. |
| ⚠️ **Spoilage Assessor** | Calculates post-harvest spoilage risk based on crop type, storage, transit duration & weather. |
| 🛡️ **Spoilage Prevention** | Detailed spoilage risk analysis with prevention tips per crop and storage type. |
| 🗺️ **Map Explorer** | Interactive Maharashtra map with mandi locations, prices, and Google Maps navigation. |

## 🎨 Design

- **Cream/green theme** (`#fefae0` background, `#2d6a4f` accents, `#1a3d2e` sidebar)
- **Unified sidebar** with branding, language selector, and navigation across all pages
- **Multilingual**: English, हिंदी, मराठी (Devanagari script)
- **Plotly charts** for interactive data visualization

## 🚀 Quick Start

```bash
# Clone
git clone https://github.com/samyakg051-creator/Ripple_Effect.git
cd Ripple_Effect

# Install dependencies
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Mac/Linux
pip install -r requirements.txt

# Set up API key (for AI chatbot)
echo GROQ_API_KEY=your_key_here > .env

# Run
streamlit run app.py
```

## 📁 Project Structure

```
├── app.py                      # Main dashboard (Harvest Readiness Score + AI)
├── pages/
│   ├── 1_🌾_Harvest.py         # Harvest Window recommender
│   ├── 2_🏪_Mandi.py           # Mandi profit ranker
│   ├── 2_Spoilage_Prevention.py # Spoilage risk & tips
│   ├── 3_⚠️_Spoilage.py        # Spoilage assessor with gauge
│   └── 4_Map_Explorer.py       # Interactive Maharashtra map
├── modules/
│   ├── agri_data.py             # Crop data, mandi coords, translations
│   ├── harvest_engine.py        # Harvest window scoring logic
│   ├── mandi_ranker.py          # Net profit ranking engine
│   ├── spoilage_assessor.py     # Spoilage risk calculator
│   ├── price_predictor.py       # ML price forecasting (scikit-learn)
│   ├── weather.py               # Open-Meteo weather API
│   └── ai_assistant.py          # Groq LLM integration
├── utils/
│   ├── sidebar.py               # Shared sidebar (nav + language)
│   ├── translator.py            # En/Hi/Mr translations
│   ├── geo.py                   # District coordinates + haversine
│   └── map_selector.py          # Folium map district picker
├── data/
│   ├── Agriculture_price_dataset.csv
│   └── mandi_prices.csv
└── requirements.txt
```

## 🔌 APIs Used

- **[Open-Meteo](https://open-meteo.com/)** — Weather forecasts (free, no key needed)
- **[Groq](https://groq.com/)** — AI chatbot (free tier, key required)

## 📦 Dependencies

`streamlit` · `pandas` · `plotly` · `scikit-learn` · `folium` · `streamlit-folium` · `requests` · `groq` · `python-dotenv`

## 📄 License

MIT

---

> Built for Indian farmers 🇮🇳 — *Know when to harvest, where to sell, and how to protect your produce.*
