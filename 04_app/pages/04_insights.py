"""
04_insights.py — Notebook Insights page

Displays artefacts (DataFrames + figures) that were exported from
Jupyter notebooks in 03_processing/workspace/ via the workspace utils toolkit.

HOW TO PUBLISH AN ANALYSIS FROM A NOTEBOOK
───────────────────────────────────────────
In any notebook cell, add:

    import sys; sys.path.insert(0, "..")
    from utils import load_app_ready, export_df, export_figure

    df = load_app_ready(city="Oslo", years=[2024])
    # ... your analysis ...

    export_df("oslo_top_routes_2024", result_df)       # → shows as a table
    export_figure("oslo_top_routes_2024", fig)         # → shows as an image

After saving the notebook and re-running the cells, refresh this page
(or press the Reload button below) to see the new export appear.
"""

import streamlit as st

from services.notebook_outputs import exports_exist, list_exports, load_export_df

st.set_page_config(
    page_title="Notebook Insights — Urban Cycling",
    page_icon="📓",
    layout="wide",
)

st.header("📓 Notebook Insights")
st.markdown(
    "This page automatically displays DataFrames and figures that have been "
    "exported from Jupyter notebooks via **`03_processing/workspace/utils.py`**."
)

# ── Reload / cache-bust button ─────────────────────────────────────────────────
sidebar_col, _ = st.columns([1, 4])
with sidebar_col:
    if st.button("🔄 Reload exports"):
        st.cache_data.clear()
        st.rerun()

st.divider()

# ── No exports yet ──────────────────────────────────────────────────────────────
if not exports_exist():
    st.info(
        "**No notebook exports found yet.**\n\n"
        "To publish an analysis from a notebook:\n\n"
        "```python\n"
        "import sys; sys.path.insert(0, '..')\n"
        "from utils import load_app_ready, export_df, export_figure\n\n"
        "df = load_app_ready(city='Oslo', years=[2024])\n"
        "# ... your analysis ...\n"
        "export_df('my_analysis_name', result_df)\n"
        "export_figure('my_analysis_name', fig)\n"
        "```\n\n"
        "Exports are saved to `02_data/gold/notebook_exports/` and will "
        "appear here after you press **Reload exports** above."
    )
    st.stop()

# ── List of exports ────────────────────────────────────────────────────────────
artefacts = list_exports()

# Sidebar: filter by kind
with st.sidebar:
    st.markdown("### 📓 Notebook Insights")
    st.divider()
    show_kind = st.radio(
        "Show",
        options=["All", "Tables only", "Figures only"],
        index=0,
    )

kind_filter = {"All": None, "Tables only": "dataframe", "Figures only": "figure"}[show_kind]
filtered = [a for a in artefacts if kind_filter is None or a["kind"] == kind_filter]

if not filtered:
    st.warning(f"No exports of type '{show_kind}' found.")
    st.stop()

st.caption(f"{len(filtered)} artefact(s) found in `02_data/gold/notebook_exports/`")

# ── Render each artefact ───────────────────────────────────────────────────────
for art in filtered:
    # Human-readable title from filename (underscores → spaces, title-cased)
    title = art["name"].replace("_", " ").title()
    icon  = "📊" if art["kind"] == "dataframe" else "🖼️"

    with st.expander(f"{icon}  {title}  —  last updated {art['modified']}", expanded=True):
        st.caption(f"`{art['filename']}`")

        if art["kind"] == "dataframe":
            df = load_export_df(art["filename"])
            if not df.empty:
                st.dataframe(df, use_container_width=True, hide_index=True)

                # Offer a CSV download
                st.download_button(
                    label="⬇️  Download CSV",
                    data=df.to_csv(index=False).encode("utf-8"),
                    file_name=art["filename"],
                    mime="text/csv",
                    key=f"dl_{art['name']}",
                )
            else:
                st.warning("Could not load this table.")

        elif art["kind"] == "figure":
            st.image(str(art["path"]), use_container_width=True)
