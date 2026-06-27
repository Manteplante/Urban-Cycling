import streamlit as st

def headline_metrics(df):
    c1, c2, c3 = st.columns(3)

    c1.metric("example", len(df))
    c2.metric("example", df["country"].nunique())
    c3.metric("example", df["date"].max())
