"""
Analysis page — modular, tabbed analysis of bike-sharing data.

HOW TO ADD A NEW ANALYSIS TAB:
  1. Add a label string to the st.tabs([...]) list.
  2. Unpack the extra tab variable (e.g. tab5).
  3. Write your analysis inside the new `with tab5:` block.
  4. Add any reusable helpers to components/charts.py or services/transform.py.
"""

import numpy as np
import streamlit as st
from sklearn.linear_model import LinearRegression

from components.charts import (
    bar_daily,
    bar_hourly,
    bar_top_routes,
    histogram_duration,
    line_monthly,
    scatter_regression,
)
from components.filters import sidebar_filters
from services.transform import (
    daily_trips,
    duration_stats,
    hourly_trips,
    monthly_trips,
    top_routes,
)

st.set_page_config(
    page_title="Analysis — Urban Cycling",
    page_icon="📈",
    layout="wide",
)
st.header("📈 Cycling Data Analysis")

# ── Filters ────────────────────────────────────────────────────────────────────
query = sidebar_filters(key_prefix="analysis")

# ── Load data ──────────────────────────────────────────────────────────────────
with st.spinner("Loading trip data…"):
    df = query.load()

if df.empty:
    st.info(
        "No data found for the selected filters. "
        "Make sure you have run: `python 03_processing/transform.py`"
    )
    st.stop()

st.caption(f"Analysing **{len(df):,} trips** across the selected filters.")
st.divider()

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "⏱️ Temporal Patterns",
    "🔝 Top Routes & Stations",
    "📏 Trip Duration",
    "📉 Trend Analysis",
])

# ── Tab 1 : Temporal Patterns ──────────────────────────────────────────────────
with tab1:
    st.subheader("When do people ride?")

    col_l, col_r = st.columns(2)
    with col_l:
        hourly_df = hourly_trips(df)
        if not hourly_df.empty:
            st.plotly_chart(bar_hourly(hourly_df), use_container_width=True)

    with col_r:
        daily_df = daily_trips(df)
        if not daily_df.empty:
            st.plotly_chart(bar_daily(daily_df), use_container_width=True)

    monthly_df = monthly_trips(df)
    if not monthly_df.empty:
        st.plotly_chart(line_monthly(monthly_df), use_container_width=True)
    else:
        st.info("No month dimension data available — run the ETL pipeline first.")

# ── Tab 2 : Top Routes & Stations ─────────────────────────────────────────────
with tab2:
    st.subheader("Most popular routes")
    n_routes = st.slider("Show top N routes", 5, 25, 10, key="n_routes")
    routes_df = top_routes(df, n=n_routes)
    if not routes_df.empty:
        st.plotly_chart(bar_top_routes(routes_df), use_container_width=True)
        with st.expander("Route data table"):
            st.dataframe(routes_df, use_container_width=True, hide_index=True)
    else:
        st.info("Station name columns not available in current dataset.")

    st.subheader("Top 10 departure stations")
    if "start_station_name" in df.columns:
        top_dep = (
            df["start_station_name"]
            .value_counts()
            .head(10)
            .reset_index()
        )
        top_dep.columns = ["Station", "Departures"]
        st.dataframe(top_dep, use_container_width=True, hide_index=True)

# ── Tab 3 : Trip Duration ──────────────────────────────────────────────────────
with tab3:
    st.subheader("How long are trips?")
    if "duration_seconds" in df.columns:
        stats = duration_stats(df)
        if stats:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Mean",           f"{stats['mean_minutes']} min")
            m2.metric("Median",         f"{stats['median_minutes']} min")
            m3.metric("90th Percentile",f"{stats['p90_minutes']} min")
            m4.metric("Max",            f"{stats['max_minutes']} min")

        cutoff = st.slider(
            "Histogram cutoff (minutes)", 10, 120, 60, key="dur_cutoff"
        )
        st.plotly_chart(histogram_duration(df, max_minutes=cutoff), use_container_width=True)
    else:
        st.info("Duration data is not available in this dataset.")

# ── Tab 4 : Trend Analysis ─────────────────────────────────────────────────────
with tab4:
    st.subheader("Monthly trip volume trend")
    monthly_df = monthly_trips(df)

    if monthly_df.empty or len(monthly_df) < 2:
        st.info("Need at least 2 months of data to compute a trend.")
    else:
        X     = np.arange(len(monthly_df)).reshape(-1, 1)
        y     = monthly_df["trips"].values
        model = LinearRegression().fit(X, y)
        r2    = model.score(X, y)
        slope = float(model.coef_[0])

        col_m1, col_m2 = st.columns(2)
        col_m1.metric(
            "Monthly Growth Trend",
            f"{slope:+.0f} trips / month",
            delta_color="normal",
        )
        col_m2.metric("R² (fit quality)", f"{r2:.3f}")

        x_labels = [
            f"{row['month_name'][:3]} {row['year']}"
            for _, row in monthly_df.iterrows()
        ]
        fig = scatter_regression(
            x_vals=list(range(len(monthly_df))),
            y_vals=y.tolist(),
            slope=slope,
            intercept=float(model.intercept_),
            r2=r2,
            x_labels=x_labels,
            title="Monthly Trip Volume with Trend Line",
        )
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("Monthly data table"):
            st.dataframe(monthly_df, use_container_width=True, hide_index=True)

# ───────────────────────────────────────────────────────────────────────────────
# Add new analysis tabs above this line — see the docstring at the top of file.
# ───────────────────────────────────────────────────────────────────────────────
