import streamlit as st
import json
import pandas as pd
from pipeline import load_step
import visualizations

# Page Config
st.set_page_config(
    layout="wide",
    page_title="YouTube Watch History Analysis",
    initial_sidebar_state="expanded",
)

# Custom CSS for dark theme to match the plots
st.markdown(
    """
<style>
    .stApp {
        background-color: #0f0f0f;
        color: white;
    }
    .block-container {
        padding-left: 5rem;
        padding-right: 5rem;
    }
</style>
""",
    unsafe_allow_html=True,
)

st.title("YouTube Watch History Analysis")
st.markdown(
    "Upload your `watch-history.json` file to generate the dashboard. It may take a minute or two fetching data from the YouTube API. All processing is done in memory."
)

uploaded_file = st.file_uploader("Upload watch-history.json", type="json")

if uploaded_file is not None:
    try:
        # Check if data is already processed in session state for this file
        if (
            "processed_data" not in st.session_state
            or st.session_state.get("file_name") != uploaded_file.name
        ):
            # Load Steps dynamically using the existing pipeline helper
            step1 = load_step("step1", "1_yt_vid_metadata.py")
            step2 = load_step("step2", "2_merged_data.py")
            step3 = load_step("step3", "3_deduplicate.py")
            step4 = load_step("step4", "4_remove_live.py")
            step5 = load_step("step5", "5_remove_unavailable.py")
            step6 = load_step("step6", "6_remove_videos.py")
            step7 = load_step("step7", "7_to_the_hour.py")
            step8 = load_step("step8", "8_the_finishing.py")

            # Read JSON
            data = json.load(uploaded_file)

            # Progress Bar
            progress_bar = st.progress(0)
            status_text = st.empty()

            # Run Pipeline
            status_text.text(
                "[1/8] Fetching metadata and filtering watch history (2025)..."
            )
            progress_bar.progress(40)
            history_2025, cache_list = step1.run(data)
            progress_bar.progress(50)

            status_text.text("[2/8] Merging watch history with metadata...")
            df = step2.run(history_2025, cache_list)
            progress_bar.progress(57)

            status_text.text("[3/8] Deduplicating non-music videos...")
            df = step3.run(df)
            progress_bar.progress(64)

            status_text.text("[4/8] Removing live streams...")
            df = step4.run(df)
            progress_bar.progress(71)

            status_text.text("[5/8] Removing unavailable/deleted videos...")
            df = step5.run(df)
            progress_bar.progress(78)

            status_text.text("[6/8] Capping long videos and sorting...")
            df = step6.run(df)
            progress_bar.progress(85)

            status_text.text("[7/8] Flooring timestamps...")
            df = step7.run(df)
            progress_bar.progress(92)

            status_text.text("[8/8] Finishing touches...")
            df = step8.run(df)
            progress_bar.progress(100)

            status_text.text("Processing complete!")

            # Store in session state
            st.session_state["processed_data"] = df
            st.session_state["file_name"] = uploaded_file.name

        else:
            df = st.session_state["processed_data"]
            st.info("Using cached data from previous run.")

        # Visualizations
        st.divider()
        st.subheader("Dashboard")

        figs = visualizations.create_charts(df)

        # Display charts

        # KPI
        st.plotly_chart(figs["kpi"], use_container_width=True)

        # Mixed (Donut + Treemap)
        st.plotly_chart(figs["mixed"], use_container_width=True)

        # Trend
        st.plotly_chart(figs["trend"], use_container_width=True)

        # Middle section: Channels
        st.plotly_chart(figs["channels"], use_container_width=True)

        # Bottom section: Hour and DOW
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(figs["hour"], use_container_width=True)
        with col2:
            st.plotly_chart(figs["dow"], use_container_width=True)

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.exception(e)
