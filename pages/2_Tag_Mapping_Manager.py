import streamlit as st
import pandas as pd
from db import engine, schema

st.set_page_config(page_title="Tag Mapping Manager", layout="wide")
st.title("Tag Mapping Manager")

# -----------------------------
# 1. Upload Tag Mapping (Sidebar)
# -----------------------------
st.sidebar.header("Upload Data")

mapping_file = st.sidebar.file_uploader(
    "Upload Tag Mapping (with Plant column)",
    type=["csv", "xlsx"]
)

if mapping_file is not None:
    if mapping_file.name.endswith("csv"):
        upload_df = pd.read_csv(mapping_file)
    else:
        upload_df = pd.read_excel(mapping_file)

    if st.sidebar.button("Upload Tag Mapping to DB"):
        with engine.begin() as conn:
            upload_df.to_sql(
                "Tag_Mapping",
                conn,
                schema=schema,
                if_exists="replace",
                index=False
            )
        st.sidebar.success("Tag_Mapping table updated")
        st.rerun()

# -----------------------------
# 2. Fetch Current Mapping & Show Warnings
# -----------------------------
# Read the current state of the mapping table
tag_map_df = pd.read_sql(
    f'SELECT * FROM "{schema}"."Tag_Mapping"',
    engine
)

# LOGIC: Check if a Generic Tag exists but the PI Tag is empty/null
unmapped_generic = tag_map_df[
    (tag_map_df["Generic Tag"].notna()) & (tag_map_df["Generic Tag"].astype(str).str.strip() != "") &
    (tag_map_df["PI Tags"].isna() | (tag_map_df["PI Tags"].astype(str).str.strip() == ""))
]

if not unmapped_generic.empty:
    st.subheader("⚠️ Mapping Alerts")
    for g_tag in unmapped_generic["Generic Tag"].unique():
        st.warning(f"Generic Tag **{g_tag}** has no PI Tag mapping (Empty).")

# -----------------------------
# 3. View / Edit Full Mapping Table
# -----------------------------
with st.expander("View / Edit Tag Mapping Table", expanded=False):
    # Added unique key to prevent DuplicateElementId error
    edited = st.data_editor(
        tag_map_df,
        use_container_width=True,
        key="main_mapping_editor"
    )

    if st.button("Update Mapping", key="save_main_table"):
        with engine.begin() as conn:
            edited.to_sql(
                "Tag_Mapping",
                conn,
                schema=schema,
                if_exists="replace",
                index=False
            )
        st.success("Mapping Updated")
        st.rerun()

# -----------------------------
# 4. Detect & Fix Unmapped PI Tags from Input Data
# -----------------------------
input_df = pd.read_sql(
    f'SELECT * FROM "{schema}"."Input_data"',
    engine
)

# Find PI Tags in Input_data that are NOT in the Tag_Mapping table
missing_tags = list(set(input_df["PI Tags"].unique()) - set(tag_map_df["PI Tags"].unique()))

if missing_tags:
    st.divider()
    st.subheader("New PI Tags Detected")
    st.info("The following tags were found in your Input Data but are not yet mapped.")

    missing_df = pd.DataFrame({
        "PI Tags": missing_tags,
        "Generic Tag": ["" for _ in missing_tags],
        "Plant": ["" for _ in missing_tags]
    })

    # Added unique key to prevent DuplicateElementId error
    edited_new_tags = st.data_editor(
        missing_df,
        num_rows="dynamic",
        use_container_width=True,
        key="missing_tags_editor"
    )

    if st.button("Add New Tag Mappings", key="add_new_tags_btn"):
        new_tags = edited_new_tags[
            (edited_new_tags["Generic Tag"] != "") & 
            (edited_new_tags["Plant"] != "")
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
            st.success("New PI tags added successfully!")
            st.rerun()
        else:
            st.error("Please provide both a Generic Tag and a Plant name before saving.")
