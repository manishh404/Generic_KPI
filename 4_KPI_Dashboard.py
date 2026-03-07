import streamlit as st
import pandas as pd
import plotly.express as px
from db import engine, schema

st.title("KPI Dashboard")

input_df = pd.read_sql(
    f'SELECT * FROM "{schema}"."Input_data"',
    engine
)
tag_map_df = pd.read_sql(
    f'SELECT * FROM "{schema}"."Tag_Mapping"',
    engine
)
mapped_df = input_df.merge(
    tag_map_df[["PI Tags","Generic Tag","Plant"]],
    on="PI Tags",
    how="left"
)

mapped_df["Timestamp"] = pd.to_datetime(
    mapped_df["Timestamp"],
    format="mixed",
    errors="coerce"
)
# fix duplicate plant columns
if "Plant_y" in mapped_df.columns:
    mapped_df.rename(columns={"Plant_y": "Plant"}, inplace=True)

if "Plant_x" in mapped_df.columns:
    mapped_df.drop(columns=["Plant_x"], inplace=True)

plant_list = mapped_df["Plant"].dropna().unique()
selected_plant = st.sidebar.selectbox(
    "Select Plant",
    plant_list
)

# -----------------------------
# KPI Trend Chart
# -----------------------------

kpi_history = pd.read_sql(
    f'''
    SELECT *
    FROM "{schema}"."Output_Tag"
    WHERE "Plant" = '{selected_plant}'
    ORDER BY "Timestamp"
    ''',
    engine,
    # params=(selected_plant,)
)
kpi_history["Timestamp"] = pd.to_datetime(kpi_history["Timestamp"])

kpi_history["Date"] = kpi_history["Timestamp"].dt.date
date_range = st.slider(
    "Select Date Range",
    min_value=kpi_history["Timestamp"].min().to_pydatetime(),
    max_value=kpi_history["Timestamp"].max().to_pydatetime(),
    value=(
        kpi_history["Timestamp"].min().to_pydatetime(),
        kpi_history["Timestamp"].max().to_pydatetime()
    )
)
#if len(date_range) == 2:

    #start_date, end_date = date_range

kpi_history = kpi_history[
    (kpi_history["Timestamp"] >= date_range[0]) &
    (kpi_history["Timestamp"] <= date_range[1])
]
if not kpi_history.empty:

    kpi_list = kpi_history["Inferred Tag Name"].unique()

    selected_kpi = st.selectbox(
        "Select KPI for Trend",
        kpi_list
    )

    kpi_filtered = kpi_history[
        kpi_history["Inferred Tag Name"] == selected_kpi
    ]
    timestamp_list = sorted(
        kpi_filtered["Timestamp"].unique()
    )

    selected_timestamp = st.selectbox(
        "Select Timestamp",
        timestamp_list
    )

    value_df = kpi_filtered[
        kpi_filtered["Timestamp"] == selected_timestamp
    ]
    if not value_df.empty:

        kpi_value = value_df["Value"].iloc[0]

        st.metric(
            label=f"{selected_kpi} Value",
            value=round(kpi_value,4)
    )
    st.subheader("KPI Value at Selected Timestamp")
    st.dataframe(value_df) 
    fig = px.line(
        kpi_filtered,
        x="Timestamp",
        y="Value",
        markers=True,
        title=f"{selected_kpi} Trend - {selected_plant}"
    )

    st.plotly_chart(fig, use_container_width=True)

else:

    st.warning("No KPI trend data available")