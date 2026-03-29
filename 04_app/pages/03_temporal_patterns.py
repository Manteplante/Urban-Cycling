"""Temporal patterns page driven by notebook exports."""

import pandas as pd
import plotly.express as px
import streamlit as st

from components.filters import default_year_selection
from services.notebook_outputs import load_export_df

st.set_page_config(
    page_title="Temporal Patterns - Urban Cycling",
    page_icon="⏱️",
    layout="wide",
)
st.header("⏱️ Temporal Patterns")

hourly = load_export_df("temporal_patterns_hourly.csv")
daily = load_export_df("temporal_patterns_daily.csv")
monthly = load_export_df("temporal_patterns_monthly.csv")

if hourly.empty or daily.empty or monthly.empty:
    st.info(
        "Temporal pattern exports are missing. Run "
        "03_processing/workspace/02_temporal_patterns.ipynb to create them."
    )
    st.stop()

required_hourly = {"city_name", "year", "start_hour", "trips"}
required_daily = {"city_name", "year", "day_of_week", "day_name", "trips"}
required_monthly = {"city_name", "year", "month", "month_name", "trips"}

missing_hourly = sorted(required_hourly - set(hourly.columns))
missing_daily = sorted(required_daily - set(daily.columns))
missing_monthly = sorted(required_monthly - set(monthly.columns))

if missing_hourly or missing_daily or missing_monthly:
    details = []
    if missing_hourly:
        details.append(f"hourly: {', '.join(missing_hourly)}")
    if missing_daily:
        details.append(f"daily: {', '.join(missing_daily)}")
    if missing_monthly:
        details.append(f"monthly: {', '.join(missing_monthly)}")

    st.error("Temporal exports have missing columns - " + " | ".join(details))
    st.stop()

for frame in [hourly, daily, monthly]:
    frame["year"] = pd.to_numeric(frame["year"], errors="coerce")

hourly = hourly.dropna(subset=["year", "city_name", "start_hour", "trips"]).copy()
daily = daily.dropna(subset=["year", "city_name", "day_of_week", "day_name", "trips"]).copy()
monthly = monthly.dropna(subset=["year", "city_name", "month", "month_name", "trips"]).copy()

hourly["year"] = hourly["year"].astype(int)
daily["year"] = daily["year"].astype(int)
monthly["year"] = monthly["year"].astype(int)

daily["day_of_week"] = pd.to_numeric(daily["day_of_week"], errors="coerce")
monthly["month"] = pd.to_numeric(monthly["month"], errors="coerce")

all_cities = sorted(set(hourly["city_name"]) | set(daily["city_name"]) | set(monthly["city_name"]))
all_years = sorted(set(hourly["year"]) | set(daily["year"]) | set(monthly["year"]))

with st.sidebar:
    st.markdown("### ⏱️ Temporal filters")
    selected_city = st.selectbox("City", options=["All Cities"] + all_cities, index=0)
    selected_years = st.multiselect("Year", options=all_years, default=default_year_selection(all_years))

if not selected_years:
    st.warning("Select at least one year to display charts.")
    st.stop()

if selected_city == "All Cities":
    hourly_plot = hourly[hourly["year"].isin(selected_years)].copy()
    daily_plot = daily[daily["year"].isin(selected_years)].copy()
    monthly_plot = monthly[monthly["year"].isin(selected_years)].copy()
else:
    hourly_plot = hourly[(hourly["year"].isin(selected_years)) & (hourly["city_name"] == selected_city)].copy()
    daily_plot = daily[(daily["year"].isin(selected_years)) & (daily["city_name"] == selected_city)].copy()
    monthly_plot = monthly[(monthly["year"].isin(selected_years)) & (monthly["city_name"] == selected_city)].copy()

if hourly_plot.empty or daily_plot.empty or monthly_plot.empty:
    st.info("No temporal data found for the selected filters.")
    st.stop()

hourly_view = hourly_plot.groupby("start_hour", as_index=False)["trips"].sum().sort_values("start_hour")
daily_view = daily_plot.groupby(["day_of_week", "day_name"], as_index=False)["trips"].sum().sort_values("day_of_week")
monthly_view = monthly_plot.groupby(["year", "month", "month_name"], as_index=False)["trips"].sum().sort_values(["year", "month"])
monthly_view["period"] = monthly_view["year"].astype(str) + "-" + monthly_view["month"].astype(int).astype(str).str.zfill(2)

st.caption(
    f"Source rows - hourly: {len(hourly_plot):,}, daily: {len(daily_plot):,}, monthly: {len(monthly_plot):,}"
)

left, right = st.columns(2)

with left:
    fig_hourly = px.bar(
        hourly_view,
        x="start_hour",
        y="trips",
        title="Trips by Hour of Day",
        labels={"start_hour": "Hour", "trips": "Trips"},
        color="trips",
        color_continuous_scale="Reds",
    )
    fig_hourly.update_layout(showlegend=False, coloraxis_showscale=False, plot_bgcolor="white")
    fig_hourly.update_xaxes(tickmode="linear", dtick=1)
    st.plotly_chart(fig_hourly, use_container_width=True)

with right:
    fig_daily = px.bar(
        daily_view,
        x="day_name",
        y="trips",
        title="Trips by Day of Week",
        labels={"day_name": "Day", "trips": "Trips"},
        color="trips",
        color_continuous_scale="Blues",
    )
    fig_daily.update_layout(showlegend=False, coloraxis_showscale=False, plot_bgcolor="white")
    st.plotly_chart(fig_daily, use_container_width=True)

fig_monthly = px.line(
    monthly_view,
    x="period",
    y="trips",
    markers=True,
    title="Monthly Trip Volume",
    labels={"period": "Month", "trips": "Trips"},
)
fig_monthly.update_layout(plot_bgcolor="white")
fig_monthly.update_xaxes(tickangle=-45)
st.plotly_chart(fig_monthly, use_container_width=True)

with st.expander("Show aggregated tables"):
    st.markdown("**Hourly**")
    st.dataframe(hourly_view, use_container_width=True, hide_index=True)
    st.markdown("**Daily**")
    st.dataframe(daily_view[["day_name", "trips"]], use_container_width=True, hide_index=True)
    st.markdown("**Monthly**")
    st.dataframe(monthly_view[["year", "month_name", "trips"]], use_container_width=True, hide_index=True)
