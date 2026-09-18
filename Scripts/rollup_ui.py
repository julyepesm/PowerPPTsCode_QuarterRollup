"""Dedicated Streamlit interface for the Buick/GMC quarter rollup."""

import datetime

import pandas as pd
import streamlit as st

from main_slide_generator import process_buick_gmc_quarter_rollup


st.set_page_config(page_title="Buick/GMC Quarter Rollup", layout="centered")
st.title("Buick/GMC Executive Summary Rollup")
st.write("Generate 22 decks for the 11 markets using June-August 2026 data.")

col_start, col_end = st.columns(2)
with col_start:
    start_date = st.date_input(
        "Start month",
        value=datetime.date(2026, 6, 1),
        key="rollup_start_month",
    )
with col_end:
    end_date = st.date_input(
        "End month",
        value=datetime.date(2026, 8, 1),
        key="rollup_end_month",
    )

flatten_slides = st.checkbox(
    "Flatten slides (non-editable version)",
    value=False,
)

if st.button("GENERATE 22 ROLLUP DECKS", type="primary", use_container_width=True):
    if start_date > end_date:
        st.error("The start month must be before or equal to the end month.")
    else:
        with st.status("Generating Buick/GMC rollup decks...", expanded=True) as status:
            result = process_buick_gmc_quarter_rollup(
                start_month_year=start_date.strftime("%Y-%m-%d"),
                end_month_year=end_date.strftime("%Y-%m-%d"),
                flatten_slides=flatten_slides,
            )
            if result.get("errors", 1) == 0:
                status.update(label="Rollup completed", state="complete")
                st.success(
                    f"Generated {result['successful_decks']} decks in "
                    f"`{result['output_folder']}`"
                )
            else:
                status.update(label="Rollup completed with errors", state="error")
                st.warning(
                    f"Generated {result.get('successful_decks', 0)} of "
                    f"{result.get('expected_decks', 22)} decks."
                )
                st.dataframe(pd.DataFrame(result.get("details", [])))