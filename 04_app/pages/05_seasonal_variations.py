# Seasonal variations page — uses notebook export seasonal_trends_city_year.csv.

# ── Imports ───────────────────────────────────────────────────────────────────
import pandas as pd
import plotly.express as px
import streamlit as st

from components.filters import default_year_selection
from services.notebook_outputs import load_export_df

# ── Page setup ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Seasonal Variations — Urban Cycling",
    page_icon="🍂",
    layout="wide",
)
st.header("🍂 Seasonal Variations")

# ── Load export and validate required columns ─────────────────────────────────
export_filename = "seasonal_trends_city_year.csv"
df = load_export_df(export_filename)

if df.empty:
    st.info(
        "No seasonal export found yet. Run the notebook "
        "03_processing/workspace/04_seasonal_trends.ipynb and export the dataframe first."
    )
    st.stop()

required_cols = {"city_name", "year", "season", "trips"}
missing = sorted(required_cols - set(df.columns))
if missing:
    st.error(
        "The seasonal export is missing required columns: "
        f"{', '.join(missing)}. Re-run the notebook export."
    )
    st.stop()

# ── Type cleanup and quick metrics ────────────────────────────────────────────
df = df.copy()
df["year"] = pd.to_numeric(df["year"], errors="coerce")
df = df.dropna(subset=["year", "city_name", "season", "trips"])
df["year"] = df["year"].astype(int)
df["season"] = pd.Categorical(df["season"], categories=["Winter", "Summer"], ordered=True)

a1, a2, a3 = st.columns(3)
a1.metric("Rows", f"{len(df):,}")
a2.metric("Cities", f"{df['city_name'].nunique():,}")
a3.metric("Years", f"{df['year'].nunique():,}")

# ── Sidebar filters ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🍂 Seasonal filters")
    all_cities = sorted(df["city_name"].dropna().unique().tolist())
    all_years = sorted(df["year"].dropna().astype(int).unique().tolist())
    selected_city = st.selectbox("City", options=["All Cities"] + all_cities, index=0)
    selected_years = st.multiselect("Year", options=all_years, default=default_year_selection(all_years))

if not selected_years:
    st.warning("Select at least one year to display seasonal trends.")
    st.stop()

year_filtered = df[df["year"].isin(selected_years)]
plot_df = year_filtered if selected_city == "All Cities" else year_filtered[year_filtered["city_name"] == selected_city]
if plot_df.empty:
    st.warning("No data available for this city selection.")
    st.stop()

# ── Render charts ─────────────────────────────────────────────────────────────
if selected_city == "All Cities":
    fig = px.bar(
        plot_df,
        x="year",
        y="trips",
        color="season",
        facet_col="city_name",
        barmode="group",
        category_orders={"season": ["Winter", "Summer"]},
        title="Winter vs Summer trips by city and year",
        labels={"year": "Year", "trips": "Trips", "city_name": "City", "season": "Season"},
    )
    fig.for_each_annotation(lambda ann: ann.update(text=ann.text.split("=")[-1]))
    fig.update_layout(height=560, legend_title_text="Season")
else:
    fig = px.bar(
        plot_df,
        x="year",
        y="trips",
        color="season",
        barmode="group",
        category_orders={"season": ["Winter", "Summer"]},
        title=f"Winter vs Summer trips in {selected_city}",
        labels={"year": "Year", "trips": "Trips", "season": "Season"},
    )
    fig.update_layout(height=520, legend_title_text="Season")

st.plotly_chart(fig, use_container_width=True)

# ── Table output ──────────────────────────────────────────────────────────────
st.subheader("Seasonal data")
st.dataframe(
    plot_df.sort_values(["city_name", "year", "season"]),
    use_container_width=True,
    hide_index=True,
)
