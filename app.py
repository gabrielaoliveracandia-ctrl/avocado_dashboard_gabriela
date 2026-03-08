"""
app.py  —  Avocado Sales Explorer
Dash dashboard converting Gabriela Olivera's HW1 notebook analysis.
Run:  python app.py
"""

import os
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import dash
from dash import dcc, html, Input, Output

from data_loader import (
    load_data,
    apply_filters,
    get_overview_data,
    get_seasonality_data,
    get_regional_data,
    get_volume_price_data,
    get_product_mix_data,
    MONTH_ORDER,
)

# ── Colour palette ────────────────────────────────────────────────────────────
C_CONVENTIONAL = "#2A9D8F"
C_ORGANIC      = "#E9C46A"
C_CRIMSON      = "#E63946"
C_SLATE        = "#264653"
C_CORAL        = "#E76F51"
C_MINT         = "#57CC99"
C_AMBER_BAR    = "#F4A261"
C_BG           = "#F4F6F8"
C_CARD         = "#FFFFFF"
C_BORDER       = "#DEE2E6"
C_MUTED        = "#6C757D"

TYPE_COLORS = {"conventional": C_CONVENTIONAL, "organic": C_ORGANIC}
PLU_COLORS  = {"Small (4046)": C_SLATE, "Large (4225)": C_CORAL, "XLarge (4770)": C_MINT}
BAG_COLORS  = {"Small": C_SLATE, "Large": C_CORAL, "XLarge": C_MINT}

PLOTLY_LAYOUT = dict(
    font_family="DM Sans, sans-serif",
    paper_bgcolor=C_CARD,
    plot_bgcolor=C_BG,
    margin=dict(l=12, r=12, t=40, b=12),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=C_BORDER, borderwidth=1, font_size=11),
    xaxis=dict(gridcolor=C_BORDER, linecolor=C_BORDER),
    yaxis=dict(gridcolor=C_BORDER, linecolor=C_BORDER),
)

# ── Load data ─────────────────────────────────────────────────────────────────
CSV_PATH = os.environ.get("AVOCADO_CSV", "data/avocado.csv")
DF          = load_data(CSV_PATH)
ALL_REGIONS = sorted(DF["region"].unique().tolist())
YEAR_MIN    = int(DF["year"].min())
YEAR_MAX    = int(DF["year"].max())

# ── App ───────────────────────────────────────────────────────────────────────
app = dash.Dash(__name__, title="Avocado Sales Explorer",
                meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}])
server = app.server


def style_fig(fig, title=""):
    fig.update_layout(**PLOTLY_LAYOUT, title_text=title, title_font_size=14)
    return fig


# ── Layout — ALL controls permanently in DOM ──────────────────────────────────
app.layout = html.Div([

    html.Div([
        html.H1("🥑 Avocado Sales Explorer"),
        html.P("Hass Avocado Board · 2015–2023 · GreenGrocer Strategic Analysis",
               className="subtitle"),
    ], className="dash-header"),

    # ── Global filters (always visible) ──────────────────────────────────────
    html.Div([
        html.Div([
            html.Div("Year range", className="filter-label"),
            html.Div([
                dcc.RangeSlider(
                    id="year-slider", min=YEAR_MIN, max=YEAR_MAX, step=1,
                    value=[YEAR_MIN, YEAR_MAX],
                    marks={y: str(y) for y in range(YEAR_MIN, YEAR_MAX + 1)},
                    tooltip={"placement": "bottom", "always_visible": False},
                ),
            ], style={"width": "420px"}),
        ]),
        html.Div([
            html.Div("Type", className="filter-label"),
            dcc.Checklist(
                id="type-checklist",
                options=[{"label": " Conventional", "value": "conventional"},
                         {"label": " Organic",      "value": "organic"}],
                value=["conventional", "organic"], inline=True,
                inputStyle={"marginRight": "5px", "accentColor": C_CONVENTIONAL},
                labelStyle={"marginRight": "18px", "fontSize": "0.88rem", "fontWeight": "500"},
            ),
        ]),
        html.Div([
            html.Div("Region(s)", className="filter-label"),
            dcc.Dropdown(
                id="region-dropdown",
                options=[{"label": r, "value": r} for r in ALL_REGIONS],
                value=[], multi=True, placeholder="All regions",
                style={"minWidth": "260px", "fontSize": "0.88rem"}, clearable=True,
            ),
        ]),
    ], className="filter-bar"),

    # ── Tabs ──────────────────────────────────────────────────────────────────
    dcc.Tabs(id="main-tabs", value="overview", className="custom-tabs", children=[
        dcc.Tab(label="Overview",        value="overview",     className="custom-tab", selected_className="custom-tab--selected"),
        dcc.Tab(label="Seasonality",     value="seasonality",  className="custom-tab", selected_className="custom-tab--selected"),
        dcc.Tab(label="Regional",        value="regional",     className="custom-tab", selected_className="custom-tab--selected"),
        dcc.Tab(label="Volume vs Price", value="volume_price", className="custom-tab", selected_className="custom-tab--selected"),
        dcc.Tab(label="Product Mix",     value="product_mix",  className="custom-tab", selected_className="custom-tab--selected"),
    ]),

    # ── Regional sub-controls — ALWAYS in DOM, shown/hidden via style ─────────
    html.Div([
        html.Div([
            html.Div("Metric", className="filter-label"),
            dcc.RadioItems(
                id="regional-metric",
                options=[{"label": " Average Price", "value": "Average Price"},
                         {"label": " Total Revenue", "value": "Total Revenue"},
                         {"label": " Total Volume",  "value": "Total Volume"}],
                value="Average Price", inline=True,
                inputStyle={"marginRight": "5px", "accentColor": C_CONVENTIONAL},
                labelStyle={"marginRight": "20px", "fontSize": "0.88rem", "fontWeight": "500"},
            ),
        ]),
        html.Div([
            html.Div("Top N regions", className="filter-label"),
            html.Div([
                dcc.Slider(
                    id="topn-slider", min=5, max=20, step=1, value=10,
                    marks={5: "5", 10: "10", 15: "15", 20: "20"},
                    tooltip={"placement": "bottom", "always_visible": False},
                ),
            ], style={"width": "280px"}),
        ]),
    ], id="regional-controls-bar", className="regional-controls",
       style={"display": "none", "margin": "12px 40px 0 40px"}),

    html.Div(id="tab-content", className="tab-content"),

], style={"minHeight": "100vh", "backgroundColor": C_BG})


# ── Show/hide regional controls based on active tab ───────────────────────────
@app.callback(
    Output("regional-controls-bar", "style"),
    Input("main-tabs", "value"),
)
def toggle_regional_controls(tab):
    base = {"margin": "12px 40px 0 40px"}
    if tab == "regional":
        return {**base, "display": "flex"}
    return {**base, "display": "none"}


# ── Master render callback ────────────────────────────────────────────────────
@app.callback(
    Output("tab-content", "children"),
    Input("main-tabs",       "value"),
    Input("year-slider",     "value"),
    Input("type-checklist",  "value"),
    Input("region-dropdown", "value"),
    Input("regional-metric", "value"),
    Input("topn-slider",     "value"),
)
def render_tab(tab, year_range, types, regions, metric, top_n):
    filtered = apply_filters(DF, year_range, types or [], regions or [])
    if filtered.empty:
        return html.Div("No data matches the current filters.",
                        style={"color": C_MUTED, "padding": "40px", "textAlign": "center"})

    if tab == "overview":
        return build_overview(filtered)
    elif tab == "seasonality":
        return build_seasonality(filtered)
    elif tab == "regional":
        return build_regional(filtered, metric or "Average Price", top_n or 10)
    elif tab == "volume_price":
        return build_volume_price(filtered)
    elif tab == "product_mix":
        return build_product_mix(filtered)
    return html.Div()


# ═══════════════════════════════════════════════════════════════════════════════
#  TAB 1 — OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════════

def build_overview(df):
    data = get_overview_data(df)
    kpis = data["kpis"]
    mdf  = data["monthly_price"]

    def kpi_card(label, value):
        return html.Div([html.Div(label, className="kpi-label"),
                         html.Div(value, className="kpi-value")], className="kpi-card")

    def fmt_vol(v):
        if v >= 1e9: return f"{v/1e9:.1f}B lbs"
        if v >= 1e6: return f"{v/1e6:.1f}M lbs"
        return f"{v:,.0f} lbs"

    def fmt_rev(v):
        if v >= 1e9: return f"${v/1e9:.2f}B"
        if v >= 1e6: return f"${v/1e6:.1f}M"
        return f"${v:,.0f}"

    fig = px.line(mdf, x="date", y="average_price", color="type",
                  color_discrete_map=TYPE_COLORS,
                  labels={"average_price": "Avg Price ($)", "date": "", "type": "Type"})
    fig.update_traces(line_width=1.8)
    style_fig(fig, "Monthly Average Price by Type")

    return html.Div([
        html.Div([
            kpi_card("Avg Price",      f"${kpis['avg_price']:.2f}"),
            kpi_card("Total Volume",   fmt_vol(kpis["total_volume"])),
            kpi_card("Est. Revenue",   fmt_rev(kpis["est_revenue"])),
            kpi_card("Weeks in range", f"{kpis['weeks']:,}"),
        ], className="kpi-row"),
        html.Div([dcc.Graph(figure=fig, config={"displayModeBar": False})], className="chart-card"),
    ])


# ═══════════════════════════════════════════════════════════════════════════════
#  TAB 2 — SEASONALITY
# ═══════════════════════════════════════════════════════════════════════════════

def build_seasonality(df):
    data = get_seasonality_data(df)

    fig_price = px.line(data["monthly_avg"], x="month_name", y="average_price", color="type",
                        color_discrete_map=TYPE_COLORS, markers=True,
                        labels={"average_price": "Avg Price ($)", "month_name": "Month", "type": "Type"},
                        category_orders={"month_name": MONTH_ORDER})
    fig_price.update_traces(line_width=2)
    style_fig(fig_price, "Price Seasonality")

    fig_vol = px.bar(data["monthly_vol"], x="month_name", y="total_volume",
                     labels={"total_volume": "Avg Volume (lbs)", "month_name": "Month"},
                     category_orders={"month_name": MONTH_ORDER})
    fig_vol.update_traces(marker_color=C_AMBER_BAR)
    style_fig(fig_vol, "Average Volume by Month")

    heatmap_cards = []
    for t, pivot in data["heatmap"].items():
        if pivot.empty:
            continue
        fig_h = px.imshow(pivot, color_continuous_scale="YlOrRd", aspect="auto",
                          labels={"color": "Avg Price ($)", "x": "Month", "y": "Year"})
        fig_h.update_layout(**PLOTLY_LAYOUT,
                            title_text=f"Price Heatmap: Year × Month — {t.capitalize()}",
                            title_font_size=13)
        heatmap_cards.append(
            html.Div([dcc.Graph(figure=fig_h, config={"displayModeBar": False})], className="chart-card"))

    return html.Div([
        html.Div([
            html.Div([dcc.Graph(figure=fig_price, config={"displayModeBar": False})], className="chart-card"),
            html.Div([dcc.Graph(figure=fig_vol,   config={"displayModeBar": False})], className="chart-card"),
        ], className="two-col"),
        *heatmap_cards,
    ])


# ═══════════════════════════════════════════════════════════════════════════════
#  TAB 3 — REGIONAL
# ═══════════════════════════════════════════════════════════════════════════════

def build_regional(df, metric, top_n):
    data = get_regional_data(df, metric, top_n)
    x_label = {"Average Price": "Avg Price ($)",
                "Total Revenue": "Est. Revenue ($)",
                "Total Volume": "Total Volume (lbs)"}[metric]

    def make_bar(df_sub, title):
        col = df_sub.columns[1]
        fig = px.bar(df_sub, x=col, y="region", orientation="h",
                     labels={col: x_label, "region": ""})
        fig.update_traces(marker_color=C_CRIMSON)
        style_fig(fig, title)
        fig.update_layout(height=36 * top_n + 80)
        return fig

    rows = []
    for section, label in [("top", f"Top {top_n} Regions"), ("bottom", f"Bottom {top_n} Regions")]:
        rows.append(html.Div([
            html.Div([dcc.Graph(figure=make_bar(data["conventional"][section], f"Conventional — {label}"),
                                config={"displayModeBar": False})], className="chart-card"),
            html.Div([dcc.Graph(figure=make_bar(data["organic"][section],      f"Organic — {label}"),
                                config={"displayModeBar": False})], className="chart-card"),
        ], className="two-col"))

    return html.Div(rows)


# ═══════════════════════════════════════════════════════════════════════════════
#  TAB 4 — VOLUME VS PRICE
# ═══════════════════════════════════════════════════════════════════════════════

def build_volume_price(df):
    data   = get_volume_price_data(df)
    r_conv = data["conventional"]["correlation"]
    r_org  = data["organic"]["correlation"]

    def scatter_fig(sub_data, color, title):
        import numpy as np
        fig = px.scatter(sub_data, x="total_volume", y="average_price",
                         opacity=0.35, color_discrete_sequence=[color],
                         labels={"total_volume": "Total Volume (lbs)", "average_price": "Avg Price ($)"})
        fig.update_traces(marker_size=4)
        x = sub_data["total_volume"].values
        y = sub_data["average_price"].values
        mask = np.isfinite(x) & np.isfinite(y)
        if mask.sum() > 1:
            m, b = np.polyfit(x[mask], y[mask], 1)
            x_line = np.array([x[mask].min(), x[mask].max()])
            fig.add_scatter(x=x_line, y=m * x_line + b,
                            mode="lines", line=dict(color=color, width=2),
                            showlegend=False)
        return style_fig(fig, title)

    return html.Div([
        html.Div(
            f"Pearson correlation (price vs volume)  ·  "
            f"Conventional: {r_conv}  |  Organic: {r_org}  "
            f"— Negative values confirm the Law of Demand.",
            className="corr-banner"),
        html.Div([
            html.Div([dcc.Graph(figure=scatter_fig(data["conventional"]["data"], C_CONVENTIONAL,
                                                   "Conventional — Volume vs Price"),
                                config={"displayModeBar": False})], className="chart-card"),
            html.Div([dcc.Graph(figure=scatter_fig(data["organic"]["data"], C_ORGANIC,
                                                   "Organic — Volume vs Price"),
                                config={"displayModeBar": False})], className="chart-card"),
        ], className="two-col"),
    ])


# ═══════════════════════════════════════════════════════════════════════════════
#  TAB 5 — PRODUCT MIX
# ═══════════════════════════════════════════════════════════════════════════════

def build_product_mix(df):
    data = get_product_mix_data(df)

    def make_combined(key, color_map, x_col, title):
        fig = make_subplots(rows=1, cols=2,
                            subplot_titles=["Type = conventional", "Type = organic"],
                            shared_yaxes=True)
        seen = set()
        for col_idx, t in enumerate(["conventional", "organic"], start=1):
            for _, row in data[t][key].iterrows():
                cat  = row[x_col]
                x_lbl = "PLU Mix" if key == "plu" else "Bag Mix"
                fig.add_trace(go.Bar(
                    name=cat, x=[x_lbl], y=[row["volume"]],
                    marker_color=color_map.get(cat, "#888"),
                    text=f"{row['pct']}%", textposition="inside", insidetextanchor="middle",
                    showlegend=(cat not in seen and col_idx == 1),
                    legendgroup=cat,
                ), row=1, col=col_idx)
                seen.add(cat)
        fig.update_layout(**{k: v for k, v in PLOTLY_LAYOUT.items() if k != "legend"},
                          barmode="stack", title_text=title, title_font_size=14,
                          height=380, legend=dict(title_text="", bgcolor="rgba(0,0,0,0)",
                                                  bordercolor=C_BORDER, borderwidth=1, font_size=11))
        return fig

    return html.Div([
        html.Div([dcc.Graph(figure=make_combined("plu", PLU_COLORS, "PLU", "PLU Size Breakdown by Type"),
                            config={"displayModeBar": False})], className="chart-card"),
        html.Div([dcc.Graph(figure=make_combined("bag", BAG_COLORS, "Bag", "Bag Size Preferences by Type"),
                            config={"displayModeBar": False})], className="chart-card"),
    ])


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    app.run(debug=False, host="0.0.0.0", port=port)
