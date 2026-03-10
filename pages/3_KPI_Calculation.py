import streamlit as st
import pandas as pd
from db import engine, schema
import plotly.express as px
import re

# -----------------------------
# Helper Function
# -----------------------------
def extract_variables(formula):
    tokens = re.findall(r"[A-Za-z_]\w*", formula)
    return set(tokens)


st.title("Run KPI Calculation")

# ----------------------------------
# Upload KPI Formula CSV
# ----------------------------------

st.header("Upload KPI Calculation File")

formula_file = st.sidebar.file_uploader(
    "Upload KPI Formula CSV",
    type=["csv"]
)

if formula_file:

    formula_df = pd.read_csv(formula_file)

    # st.write("Preview KPI Formula")
    # st.dataframe(formula_df)

    if st.button("Save KPI Formulas to DB"):

        formula_df.to_sql(
            "KPI_Calculation",
            engine,
            schema=schema,
            if_exists="replace",
            index=False
        )

        st.success("KPI formulas saved to database")


input_df = pd.read_sql(
    f'SELECT * FROM "{schema}"."Input_data"',
    engine
)

tag_map = pd.read_sql(
    f'SELECT * FROM "{schema}"."Tag_Mapping"',
    engine
)

formula_df = pd.read_sql(
    f'SELECT * FROM "{schema}"."KPI_Calculation"',
    engine
)
# -----------------------------
# Add New KPI Formula
# -----------------------------
st.subheader("Add New KPI Formula")

kpi_name = st.text_input("KPI Name (Inferred Tag Name)")
formula = st.text_area("KPI Formula")
uom = st.text_input("UOM")

if st.button("Add KPI Formula"):

    if kpi_name and formula:

        variables = extract_variables(formula)

        available_tags = set(tag_map["Generic Tag"].dropna())
        existing_kpis = set(formula_df["KPI_Name"].dropna())

        allowed_variables = available_tags.union(existing_kpis)

        missing_variables = variables - allowed_variables

        if missing_variables:

            st.error(
                f"Unknown variables in formula: {', '.join(missing_variables)}"
            )

        else:

            new_kpi = pd.DataFrame({
                "KPI_Name":[kpi_name],
                "FORMULA":[formula],
                "UOM":[uom]
            })

            with engine.begin() as conn:

                new_kpi.to_sql(
                    "KPI_Calculation",
                    conn,
                    schema=schema,
                    if_exists="append",
                    index=False
                )

            st.success(f"KPI '{kpi_name}' added successfully")

            st.rerun()

    else:

        st.warning("Please enter KPI Name and Formula")


edited_formula = st.data_editor(formula_df)

if st.button("Update KPI Formulas"):

    with engine.begin() as conn:

        edited_formula.to_sql(
            "KPI_Calculation",
            conn,
            schema=schema,
            if_exists="replace",
            index=False
        )

    st.success("KPI formulas updated")

mapped_df = input_df.merge(
    tag_map[["PI Tags","Generic Tag","Plant"]],
    on="PI Tags",
    how="left"
)
# fix duplicate plant columns
if "Plant_y" in mapped_df.columns:
    mapped_df.rename(columns={"Plant_y": "Plant"}, inplace=True)

if "Plant_x" in mapped_df.columns:
    mapped_df.drop(columns=["Plant_x"], inplace=True)

plant_list = mapped_df["Plant"].dropna().unique()

plant = st.selectbox("Select Plant", plant_list)

plant_df = mapped_df[mapped_df["Plant"] == plant]

if st.button("Run KPI Calculation"):

    results = []

    for ts, df_group in plant_df.groupby("Timestamp"):

        tag_values = dict(zip(df_group["Generic Tag"], df_group["Value"]))

        for _, row in formula_df.iterrows():

            try:
                value = eval(row["FORMULA"], {}, tag_values)
                tag_values[row["Inferred Tag Name"]] = value
            except:
                value = None

            results.append({
                "Plant": plant,
                "kpi_name" = row["KPI_Name"],
                "UOM": row["UOM"],
                "Value": value,
                "Timestamp": ts
            })

    out = pd.DataFrame(results)

    with engine.begin() as conn:

        out.to_sql(
            "Output_Tag",
            conn,
            schema=schema,
            if_exists="append",
            index=False
        )

    st.success("KPI calculation completed")
