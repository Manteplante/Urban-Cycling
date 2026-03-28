"""
Shared sidebar filter widgets.

Each function renders widgets in the sidebar and returns a pre-seeded
GoldQuery object.  Call .load() on it to get the DataFrame:

    from components.filters import sidebar_filters

    query = sidebar_filters(key_prefix="maps")
    df    = query.load()

That's it.  No city IDs, no path logic, no cache keys to manage.
"""

import streamlit as st
from services.gold import gold, GoldQuery


def sidebar_filters(
    key_prefix: str = "",
    include_city: bool = True,
    default_cities: list[str] | None = None,
    default_years: list[int] | None = None,
) -> GoldQuery:
    """Render city, year, and optional month filters in the sidebar.

    Returns a GoldQuery pre-seeded with the user's selections.
    Call .load() to execute and get the denormalised DataFrame.

    Example::

        query = sidebar_filters(key_prefix="analysis")
        df    = query.load()
    """
    all_cities = gold.available_cities() or ["Oslo", "Bergen", "Trondheim"]
    all_years  = gold.available_years()  or list(range(2020, 2026))

    with st.sidebar:
        st.markdown("### ⚙️ Filters")

        selected_cities: list[str] = []
        if include_city:
            city_defaults = (
                default_cities
                if default_cities is not None
                else (["Oslo"] if "Oslo" in all_cities else all_cities[:1])
            )
            selected_cities = st.multiselect(
                "City",
                options=all_cities,
                default=[c for c in city_defaults if c in all_cities],
                key=f"{key_prefix}_cities",
            )
        selected_years = st.multiselect(
            "Year",
            options=all_years,
            default=(
                [y for y in default_years if y in all_years]
                if default_years is not None
                else ([max(all_years)] if all_years else [])
            ),
            key=f"{key_prefix}_years",
        )

        with st.expander("Month (optional)", expanded=False):
            month_map = {
                "January": 1, "February": 2, "March":    3, "April":   4,
                "May":     5, "June":     6, "July":     7, "August":  8,
                "September":9,"October": 10, "November":11, "December":12,
            }
            selected_months = st.multiselect(
                "Month",
                options=list(month_map.keys()),
                default=[],
                key=f"{key_prefix}_months",
                label_visibility="collapsed",
            )

        st.divider()

    query = gold.query()
    if selected_cities:
        query = query.cities(selected_cities)
    if selected_years:
        query = query.years(selected_years)
    if selected_months:
        query = query.months([month_map[m] for m in selected_months])

    return query


# ── Backwards-compatible shim (used by existing pages) ────────────────────────
def city_year_filters(key_prefix: str = "") -> tuple:
    """Legacy helper — prefer sidebar_filters() for new pages.

    Returns (selected_cities: list[str], selected_years: tuple[int]).
    """
    all_cities = gold.available_cities() or ["Oslo", "Bergen", "Trondheim"]
    all_years  = gold.available_years()  or list(range(2020, 2026))

    with st.sidebar:
        st.markdown("### ⚙️ Filters")
        selected_cities = st.multiselect(
            "City",
            options=all_cities,
            default=["Oslo"] if "Oslo" in all_cities else all_cities[:1],
            key=f"{key_prefix}_cities",
        )
        selected_years = st.multiselect(
            "Year",
            options=all_years,
            default=[max(all_years)] if all_years else [],
            key=f"{key_prefix}_years",
        )
        st.divider()

    return selected_cities, tuple(selected_years)

