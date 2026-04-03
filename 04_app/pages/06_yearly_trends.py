# Yearly trends page — uses notebook export yearly_trends_city_year.csv.

# ── Imports ───────────────────────────────────────────────────────────────────
import pandas as pd
import plotly.express as px
import streamlit as st

from components.filters import default_year_selection
from services.notebook_outputs import load_export_df

# ── Page setup ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Yearly Trends — Urban Cycling",
    page_icon="📅",
    layout="wide",
)
st.header("📅 Yearly Trends")

# ── Load export and validate contract ─────────────────────────────────────────
export_filename = "yearly_trends_city_year.csv"
df = load_export_df(export_filename)

if df.empty:
    st.info(
        "No yearly trends export found yet. Run the notebook "
        "03_processing/workspace/06_yearly_trends.ipynb and export the dataframe first."
    )
    st.stop()

required_cols = {"city_name", "year", "trips"}
missing = sorted(required_cols - set(df.columns))
if missing:
    st.error(
        "The yearly trends export is missing required columns: "
        f"{', '.join(missing)}. Re-run the notebook export."
    )
    st.stop()

# ── Type cleanup ──────────────────────────────────────────────────────────────
df = df.copy()
df["year"] = pd.to_numeric(df["year"], errors="coerce")
df["trips"] = pd.to_numeric(df["trips"], errors="coerce")
df = df.dropna(subset=["city_name", "year", "trips"]).copy()
df["year"] = df["year"].astype(int)

# ── Sidebar filters ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📅 Yearly filters")
    cities = sorted(df["city_name"].dropna().unique().tolist())
    all_years = sorted(df["year"].dropna().astype(int).unique().tolist())
    selected_cities = st.multiselect("City", options=cities, default=cities)
    selected_years = st.multiselect("Year", options=all_years, default=default_year_selection(all_years))

if not selected_years:
    st.warning("Select at least one year to display yearly trends.")
    st.stop()

plot_df = (
    df[df["city_name"].isin(selected_cities) & df["year"].isin(selected_years)].copy()
    if selected_cities
    else pd.DataFrame()
)
if plot_df.empty:
    st.warning("Select at least one city to display yearly trends.")
    st.stop()

# ── Render chart ──────────────────────────────────────────────────────────────
fig = px.bar(
    plot_df.sort_values(["year", "city_name"]),
    x="year",
    y="trips",
    color="city_name",
    barmode="group",
    title="Trips per Year by City",
    labels={"year": "Year", "trips": "Trips", "city_name": "City"},
)
fig.update_layout(plot_bgcolor="white", legend_title_text="City")
fig.update_xaxes(type="category")

st.plotly_chart(fig, width="stretch")

# ── Optional table ────────────────────────────────────────────────────────────
with st.expander("Show yearly trend data"):
    st.dataframe(
        plot_df.sort_values(["city_name", "year"]),
        width="stretch",
        hide_index=True,
    )
