"""
data_loader.py
All pandas loading and feature-engineering logic, preserved verbatim
from Gabriela_Olivera_HW1_Avocados.ipynb (cells 4-5, 30, 33, 40, 43).
No analytical logic has been modified.
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Try to import janitor; fall back gracefully if not installed
# ---------------------------------------------------------------------------
try:
    import janitor  # noqa: F401
    HAS_JANITOR = True
except ImportError:
    HAS_JANITOR = False


def _clean_names(df: pd.DataFrame) -> pd.DataFrame:
    """Replicate janitor.clean_names(): lowercase + replace spaces/special chars with _."""
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(r"[\s\-/]", "_", regex=True)
        .str.replace(r"[^\w]", "", regex=True)
    )
    return df


def load_data(csv_path: str = "data/avocado.csv") -> pd.DataFrame:
    """
    Load and clean the avocado CSV.
    Mirrors notebook cell 4 exactly.
    """
    raw = pd.read_csv(csv_path)

    if HAS_JANITOR:
        import janitor  # noqa: F811
        avocado = (
            raw
            .clean_names()
            .assign(
                type=lambda d: d["type"].astype("category"),
                region=lambda d: d["region"].astype("category"),
                date=lambda d: pd.to_datetime(d["date"], dayfirst=True),
            )
            .query('region != "TotalUS"')
            .sort_values(["date", "region", "type"])
            .reset_index(drop=True)
        )
    else:
        avocado = _clean_names(raw)
        avocado = avocado.assign(
            type=lambda d: d["type"].astype("category"),
            region=lambda d: d["region"].astype("category"),
            date=lambda d: pd.to_datetime(d["date"], dayfirst=True),
        )
        avocado = avocado.query('region != "TotalUS"')
        avocado = avocado.sort_values(["date", "region", "type"]).reset_index(drop=True)

    # Derived temporal columns (cell 4)
    avocado["year"] = avocado["date"].dt.year
    avocado["month"] = avocado["date"].dt.month
    avocado["month_name"] = avocado["date"].dt.month_name()
    avocado["quarter"] = avocado["date"].dt.quarter
    avocado["week_of_year"] = avocado["date"].dt.isocalendar().week.astype(int)

    # Revenue / unit calculations (cell 33)
    avocado["units_plu4046"] = (avocado["plu4046"] * 16) / 4       # small ~4oz
    avocado["units_plu4225"] = (avocado["plu4225"] * 16) / 9       # large ~9oz
    avocado["units_plu4770"] = (avocado["plu4770"] * 16) / 12.5    # xlarge ~12.5oz
    avocado["total_units"] = (
        avocado["units_plu4046"]
        + avocado["units_plu4225"]
        + avocado["units_plu4770"]
    )
    avocado["revenue"] = avocado["total_units"] * avocado["average_price"]

    # Normalise the bag column name (notebook has a typo: smal_bags)
    if "smal_bags" in avocado.columns and "small_bags" not in avocado.columns:
        avocado = avocado.rename(columns={"smal_bags": "small_bags"})

    return avocado


# ---------------------------------------------------------------------------
# Filtering helper (called from callbacks)
# ---------------------------------------------------------------------------

def apply_filters(
    df: pd.DataFrame,
    year_range: list,
    types: list,
    regions: list,
) -> pd.DataFrame:
    """Return a subset of df based on global filter bar values."""
    mask = (
        (df["year"] >= year_range[0])
        & (df["year"] <= year_range[1])
    )
    if types:
        mask &= df["type"].isin(types)
    if regions:
        mask &= df["region"].isin(regions)
    return df[mask].copy()


# ---------------------------------------------------------------------------
# Per-tab data prep functions (analytical logic from notebook)
# ---------------------------------------------------------------------------

MONTH_ORDER = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def get_overview_data(df: pd.DataFrame) -> dict:
    """KPIs + monthly price trend. Mirrors Q4 logic."""
    monthly_price = (
        df.groupby(["date", "type"])["average_price"]
        .mean()
        .reset_index()
    )
    kpis = {
        "avg_price": df["average_price"].mean(),
        "total_volume": df["total_volume"].sum(),
        "est_revenue": df["revenue"].sum(),
        "weeks": df["date"].nunique(),
    }
    return {"monthly_price": monthly_price, "kpis": kpis}


def get_seasonality_data(df: pd.DataFrame) -> dict:
    """Monthly price & volume patterns. Mirrors Q5 logic."""
    # Monthly average price by type
    monthly_avg = (
        df.groupby(["month", "month_name", "type"])["average_price"]
        .mean()
        .reset_index()
    )
    monthly_avg["month_name"] = pd.Categorical(
        monthly_avg["month_name"], categories=MONTH_ORDER, ordered=True
    )
    monthly_avg = monthly_avg.sort_values("month_name")

    # Monthly average volume (all types combined)
    monthly_vol = (
        df.groupby(["month", "month_name"])["total_volume"]
        .mean()
        .reset_index()
    )
    monthly_vol["month_name"] = pd.Categorical(
        monthly_vol["month_name"], categories=MONTH_ORDER, ordered=True
    )
    monthly_vol = monthly_vol.sort_values("month_name")

    # Heatmap: year x month, avg price, per type
    heatmap_data = {}
    for t in df["type"].cat.categories if hasattr(df["type"], "cat") else df["type"].unique():
        sub = df[df["type"] == t]
        pivot = (
            sub.groupby(["year", "month_name"])["average_price"]
            .mean()
            .reset_index()
            .pivot(index="year", columns="month_name", values="average_price")
        )
        # Reorder columns to calendar order
        cols = [m for m in MONTH_ORDER if m in pivot.columns]
        heatmap_data[t] = pivot[cols]

    return {
        "monthly_avg": monthly_avg,
        "monthly_vol": monthly_vol,
        "heatmap": heatmap_data,
    }


def get_regional_data(df: pd.DataFrame, metric: str, top_n: int) -> dict:
    """Top/Bottom N regions by metric, split by type. Mirrors Q6 & Q9."""
    metric_map = {
        "Average Price": ("average_price", "mean"),
        "Total Revenue": ("revenue", "sum"),
        "Total Volume": ("total_volume", "sum"),
    }
    col, agg = metric_map.get(metric, ("average_price", "mean"))

    result = {}
    for t in ["conventional", "organic"]:
        sub = df[df["type"] == t]
        grp = (
            sub.groupby("region")[col]
            .agg(agg)
            .reset_index()
            .sort_values(col, ascending=False)
        )
        result[t] = {
            "top": grp.head(top_n),
            "bottom": grp.tail(top_n).sort_values(col, ascending=True),
            "col": col,
            "metric_label": metric,
        }
    return result


def get_volume_price_data(df: pd.DataFrame) -> dict:
    """Scatter data + Pearson correlation. Mirrors Q7 logic."""
    from scipy.stats import pearsonr

    result = {}
    for t in ["conventional", "organic"]:
        sub = df[df["type"] == t][["total_volume", "average_price"]].dropna()
        if len(sub) > 1:
            r, _ = pearsonr(sub["total_volume"], sub["average_price"])
        else:
            r = float("nan")
        result[t] = {"data": sub, "correlation": round(r, 3)}
    return result


def get_product_mix_data(df: pd.DataFrame) -> dict:
    """PLU and bag size breakdown. Mirrors Q8 & Q9 logic."""
    result = {}
    for t in ["conventional", "organic"]:
        sub = df[df["type"] == t]

        # PLU volumes
        plu = pd.DataFrame({
            "PLU": ["Small (4046)", "Large (4225)", "XLarge (4770)"],
            "volume": [
                sub["plu4046"].sum(),
                sub["plu4225"].sum(),
                sub["plu4770"].sum(),
            ],
        })
        plu["pct"] = (plu["volume"] / plu["volume"].sum() * 100).round(1)

        # Bag volumes (cell 30 melt logic)
        bag_cols = [c for c in ["small_bags", "large_bags", "xlarge_bags"] if c in sub.columns]
        bag = pd.DataFrame({
            "Bag": ["Small", "Large", "XLarge"],
            "volume": [sub[c].sum() if c in sub.columns else 0 for c in
                       ["small_bags", "large_bags", "xlarge_bags"]],
        })
        bag["pct"] = (bag["volume"] / bag["volume"].sum() * 100).round(1)

        result[t] = {"plu": plu, "bag": bag}
    return result
