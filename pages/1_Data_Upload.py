import streamlit as st
import pandas as pd
from db import engine, schema

st.title("Upload Historian Data")

file = st.file_uploader("Upload Wide PI Excel", type="xlsx")

if file:

    # -------------------------
    # Read uploaded Excel
    # -------------------------
    wide_df = pd.read_excel(file)

    # Convert Timestamp
    wide_df["Timestamp"] = pd.to_datetime(
        wide_df["Timestamp"],
        format="mixed",
        errors="coerce"
    )

    # -------------------------
    # Convert wide → long
    # -------------------------
    long_df = wide_df.melt(
        id_vars=["Timestamp"],
        var_name="PI Tags",
        value_name="Value"
    )

    # Remove hidden spaces
    long_df["PI Tags"] = long_df["PI Tags"].astype(str).str.strip()

    st.subheader("Long Format Preview")
    st.dataframe(long_df.head())

    # -------------------------
    # Load Tag Mapping
    # -------------------------
    tag_map_df = pd.read_sql(
        f'SELECT * FROM "{schema}"."Tag_Mapping"',
        engine
    )

    tag_map_df["PI Tags"] = tag_map_df["PI Tags"].astype(str).str.strip()

    # -------------------------
    # Merge Tag Mapping
    # -------------------------
    mapped_df = long_df.merge(
        tag_map_df[["PI Tags", "Generic Tag", "Plant"]],
        on="PI Tags",
        how="left"
    )

    mapped_df["Tag Name"] = mapped_df["Generic Tag"]
    mapped_df.drop(columns=["Generic Tag"], inplace=True)

    # -------------------------
    # Preview mapped data
    # -------------------------
    st.subheader("Merged Data Preview")
    st.dataframe(mapped_df.head())

    # -------------------------
    # Detect unmapped tags
    # -------------------------
    unmapped = mapped_df[mapped_df["Tag Name"].isna()]["PI Tags"].unique()

    if len(unmapped) > 0:
        st.warning("Some PI Tags are not mapped yet")
        st.write(unmapped)

    # -------------------------
    # Select required columns
    # -------------------------
    mapped_df = mapped_df[
        ["Timestamp", "PI Tags", "Tag Name", "Plant", "Value"]
    ]

    # -------------------------
    # Upload to database
    # -------------------------
    if st.button("Upload to Database"):

        with engine.begin() as conn:

            mapped_df.to_sql(
                "Input_data",
                conn,
                schema=schema,
                if_exists="append",
                index=False,
                method="multi"
            )

        st.success("Input data uploaded successfully")

        st.write("Rows inserted:", len(mapped_df))