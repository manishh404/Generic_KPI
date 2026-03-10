import streamlit as st
import pandas as pd
from db import engine, schema

st.title("Tag Mapping Manager")

# -----------------------------
# Upload Tag Mapping
# -----------------------------

st.sidebar.header("Upload Data")

mapping_file = st.sidebar.file_uploader(
    "Upload Tag Mapping (with Plant column)",
    type=["csv","xlsx"]
)

if mapping_file is not None:

    if mapping_file.name.endswith("csv"):
        tag_map_df = pd.read_csv(mapping_file)
    else:
        tag_map_df = pd.read_excel(mapping_file)

    # st.subheader("Tag Mapping Preview")
    # st.dataframe(tag_map_df)

    if st.button("Upload Tag Mapping to DB"):

        with engine.begin() as conn:

            tag_map_df.to_sql(
                "Tag_Mapping",
                conn,
                schema=schema,
                if_exists="replace",
                index=False
            )

        st.success("Tag_Mapping table updated")
tag_map_df = pd.read_sql(
    f'SELECT * FROM "{schema}"."Tag_Mapping"',
    engine
)
# 1. Filter rows where Generic Tag is present but PI Tag is empty/null
unmapped_generic = tag_map_df[
    (tag_map_df["Generic Tag"].notna()) & (tag_map_df["Generic Tag"].astype(str).str.strip() != "") &
    (tag_map_df["PI Tags"].isna() | (tag_map_df["PI Tags"].astype(str).str.strip() == ""))
]

# 2. Display the warnings
if not unmapped_generic.empty:
    for g_tag in unmapped_generic["Generic Tag"].unique():
        st.warning(f"⚠️ Warning: Generic Tag **{g_tag}** has no PI Tag mapping (Empty).")
# ---------------------------------------------------------

# --- CONTINUE WITH YOUR EXISTING CODE ---
with st.expander("View / Edit Tag Mapping Table"):
    edited = st.data_editor(
        tag_map_df,
        use_container_width=True
    )
with st.expander("View / Edit Tag Mapping Table"):

    edited = st.data_editor(
        tag_map_df,
        use_container_width=True
    )

    if st.button("Update Mapping"):

        with engine.begin() as conn:

            edited.to_sql(
                "Tag_Mapping",
                conn,
                schema=schema,
                if_exists="replace",
                index=False
            )

        st.success("Mapping Updated")

input_df = pd.read_sql(
    f'SELECT * FROM "{schema}"."Input_data"',
    engine
)
# -----------------------------
# Detect Unmapped PI Tags
# -----------------------------

missing_tags = set(input_df["PI Tags"].unique()) - set(tag_map_df["PI Tags"].unique())

missing_tags = list(missing_tags)

if missing_tags:

    st.subheader("Unmapped PI Tags - Add Generic Tag Mapping")

    missing_df = pd.DataFrame({
        "PI Tags": missing_tags,
        "Generic Tag": ["" for _ in missing_tags],
        "Plant": ["" for _ in missing_tags]
    })

    edited_df = st.data_editor(
        missing_df,
        num_rows="dynamic",
        use_container_width=True
    )

    if st.button("Add New Tag Mappings"):

        new_tags = edited_df[
            (edited_df["Generic Tag"] != "") &
            (edited_df["Plant"] != "")
        ]

        if not new_tags.empty:

            new_tags = new_tags.drop_duplicates(subset=["PI Tags"])

            with engine.begin() as conn:

                new_tags.to_sql(
                    "Tag_Mapping",
                    conn,
                    schema=schema,
                    if_exists="append",
                    index=False,
                    method="multi"
                )

            st.success("New PI tags added to Tag_Mapping table")

            st.rerun()

        else:
            st.warning("Please enter Generic Tag and Plant for new PI tags")

