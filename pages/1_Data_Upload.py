import streamlit as st
import pandas as pd
from db import engine, schema

st.title("Upload Historian Data")

file = st.file_uploader("Upload Wide PI Excel", type="xlsx")

if file:

    wide_df = pd.read_excel(file)

    wide_df["Timestamp"] = pd.to_datetime(
        wide_df["Timestamp"],
        format="mixed",
        errors="coerce"
    )

    long_df = wide_df.melt(
        id_vars=["Timestamp"],
        var_name="PI Tags",
        value_name="Value"
    )

    st.dataframe(long_df.head())

    if st.button("Upload to Database"):

        with engine.begin() as conn:

            long_df.to_sql(
                "Input_data",
                conn,
                schema=schema,
                if_exists="append",
                index=False,
                method="multi"
            )

        st.success("Input data uploaded")
