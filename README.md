# YouTube Watch History Analysis

Interactive Streamlit app that turns your Google Takeout `watch-history.json` into a polished analytics dashboard. It fetches fresh metadata from the YouTube Data API v3, processes everything fully in memory, and renders clean, dark-themed Plotly visuals.

- Upload your `watch-history.json` and get KPIs, channel/category breakdowns, monthly trends, time-of-day and day-of-week insights.

> Note: The current pipeline filters the watch history to the year 2025. See “Change analysis year” to adjust.

## Features

- KPI cards: total hours, total videos, daily average.
- Category mix: donut (Short vs Long-form) + treemap of top categories by watch hours.
- Trends: monthly watch-hours area chart.
- Channels: top channels by hours and by views (side-by-side bars).
- Temporal patterns: watch hours by hour of day (GMT+0) and by day of week (polar).
- Data cleaning steps: deduplicate non-music videos, remove long live streams, drop unavailable/deleted videos, cap very long videos (4h), floor timestamps to the hour.

## Tech Stack

- Streamlit, Plotly (visuals)
- Pandas, NumPy (data)
- Requests, python-dotenv (API + config)
- Python 3.11 (see Dockerfile)

## Project Structure

- App entry: [app.py](app.py)
- In-memory pipeline helper: [pipeline.py](pipeline.py)
- Visualization factory: [visualizations.py](visualizations.py)
- Step modules (executed by the app):
  - [1_yt_vid_metadata.py](1_yt_vid_metadata.py): fetch YouTube metadata (API v3), select entries for 2025
  - [2_merged_data.py](2_merged_data.py): merge raw history with metadata
  - [3_deduplicate.py](3_deduplicate.py): deduplicate non-music videos by title
  - [4_remove_live.py](4_remove_live.py): remove long live streams
  - [5_remove_unavailable.py](5_remove_unavailable.py): drop unavailable/deleted videos
  - [6_remove_videos.py](6_remove_videos.py): cap duration at 4h, sort chronologically
  - [7_to_the_hour.py](7_to_the_hour.py): floor timestamps to the hour
  - [8_the_finishing.py](8_the_finishing.py): add day-of-week
- Deployment: [Dockerfile](Dockerfile), [fly.toml](fly.toml)

## Prerequisites

- Python 3.11+
- One or more YouTube Data API v3 keys
- A Google Takeout export of YouTube watch history (JSON format)

### Get your watch history (Google Takeout)

1. Go to https://takeout.google.com/
2. Deselect all, then choose “YouTube and YouTube Music”.
3. Click “All YouTube data included” → select only “history”.
4. Under “Multiple formats”, set history to JSON.
5. Create export, download, unzip, and locate `watch-history.json`.

### Configure YouTube API keys

Create a `.env` file in the project root with one or more keys. The app rotates across keys and marks daily exhaustion in `api_key_status.json`.

```
YT_API_1=your_api_key_1
YT_API_2=your_api_key_2
# Add more as YT_API_3, YT_API_4, ... if needed
```

If no keys are found, the app will error with “No YT_API keys found in .env file”. If keys are rate-limited/exhausted (HTTP 403/429), the app will automatically try the next available key.

## Quickstart (Local)

Using venv (recommended):

```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
# ensure .env is created with YT_API_* keys
streamlit run app.py
```

Using Conda (optional):

```bash
conda create -n ywh python=3.11 -y
conda activate ywh
pip install -r requirements.txt
streamlit run app.py
```

Then open the app URL (Streamlit shows it in the terminal, and upload `watch-history.json` via the UI.

## Change analysis year

The pipeline currently filters to entries where the watch timestamp year is 2025.
To analyze a different year:

- Update the filter in these places:
  - [1_yt_vid_metadata.py](1_yt_vid_metadata.py) → `entry_year(e) == 2025`
  - [pipeline.py](pipeline.py) → `_prepare_metadata_in_memory()` uses the same filter
- Or remove the filter entirely to analyze all years.

## Troubleshooting

- 403/429 errors or missing data: your API key(s) may be exhausted for today. Add more keys or try again tomorrow.
- Empty charts after upload: ensure the file contains entries for 2025 (or adjust the year filter as above).
- Time zone: time-of-day chart labels are shown in GMT+0.
- Unavailable/deleted videos: these are removed by design in step 5.

## Privacy

- Local runs: processing is in-memory; no watch history is persisted.
- Deployed runs: the app processes uploaded data in-memory for the session. No database is used. A small `api_key_status.json` file tracks API key usage/exhaustion by day.


