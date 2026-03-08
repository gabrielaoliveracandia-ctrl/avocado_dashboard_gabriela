# 🥑 Avocado Sales Explorer

Interactive Dash dashboard converting the HW1 avocado notebook analysis into a fully interactive web app.

---

## Project Structure

```
avocado_dashboard/
├── app.py               ← Dash app (layout + all callbacks)
├── data_loader.py       ← All pandas logic from notebook (unchanged)
├── requirements.txt     ← Python dependencies
├── render.yaml          ← Render.com deployment config
├── assets/
│   └── style.css        ← Custom styling
└── data/
    └── avocado.csv      ← ← ← PUT YOUR CSV HERE
```

---

## Local Setup

```bash
# 1. Clone the repo
git clone <your-repo-url>
cd avocado_dashboard

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add your data
mkdir data
cp /path/to/avocado.csv data/avocado.csv

# 5. Run
python app.py
# → Open http://localhost:8050
```

---

## Deploy to Render

1. Push this repo to GitHub (include the `data/` folder with `avocado.csv`)
2. Go to [render.com](https://render.com) → **New Web Service**
3. Connect your GitHub repo
4. Render will auto-detect `render.yaml` and configure everything
5. Click **Deploy** — your dashboard will be live at `https://avocado-dashboard.onrender.com`

> **Note:** The free Render tier spins down after inactivity. First load may take ~30s.

---

## Dashboard Tabs

| Tab | Content |
|-----|---------|
| **Overview** | 4 KPI cards + monthly price trend by type |
| **Seasonality** | Price seasonality line, average volume by month, price heatmaps |
| **Regional** | Top/Bottom N regions by price / revenue / volume, split by type |
| **Volume vs Price** | Scatter plots with OLS trendlines + live Pearson correlation |
| **Product Mix** | PLU size breakdown + bag size preferences, split by type |

All tabs respond to the **global filter bar**: year range, avocado type, and region(s).

---

## Data

**Source:** Hass Avocado Board via Kaggle  
**URL:** https://www.kaggle.com/datasets/vakhariapujan/avocado-prices-and-sales-volume-2015-2023  
**Coverage:** 2015–2023 · 59 US regions · Weekly granularity
