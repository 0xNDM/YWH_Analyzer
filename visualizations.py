import pandas as pd


def create_dashboard_data(df: pd.DataFrame) -> dict:
    """Return JSON-serializable aggregates for the frontend (no Plotly/Streamlit).

    The output is intentionally simple: numbers + arrays of objects.
    """

    if df is None or df.empty:
        return {
            "kpis": {
                "total_watch_hours": 0.0,
                "total_videos": 0,
                "daily_average": {"hours": 0, "minutes": 0},
            },
            "type_counts": [],
            "top_categories": [],
            "monthly_trend": [],
            "channels": {"watch_hours": [], "watch_count": []},
            "hourly": [],
            "day_of_week": [],
        }

    df = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df["watched_at"]):
        df["watched_at"] = pd.to_datetime(df["watched_at"], errors="coerce")

    df["duration_seconds"] = pd.to_numeric(df.get("duration_seconds"), errors="coerce")
    df["watch_hours"] = df["duration_seconds"].fillna(0) / 3600

    # KPIs
    total_watch_hours = float(df["watch_hours"].sum())
    total_video_count = int(len(df))
    daily_avg_total_hours = total_watch_hours / 365 if total_video_count else 0
    daily_avg_hours_int = int(daily_avg_total_hours)
    daily_avg_minutes = int(round((daily_avg_total_hours - daily_avg_hours_int) * 60))

    # Short vs long-form
    type_counts = (
        df.get("type")
        .fillna("Unknown")
        .value_counts()
        .reset_index()
        .rename(columns={"index": "type", "type": "count"})
    )

    # Top categories by watch hours
    top_categories = (
        df.groupby(df.get("category").fillna("Unknown"))["watch_hours"]
        .sum()
        .reset_index()
        .rename(columns={"category": "category"})
        .sort_values("watch_hours", ascending=False)
        .head(6)
    )
    # The grouping above can create a non-standard column name when df.get("category") is used
    if top_categories.columns[0] != "category":
        top_categories = top_categories.rename(
            columns={top_categories.columns[0]: "category"}
        )

    # Monthly trend
    df["month"] = df["watched_at"].dt.strftime("%b")
    df["month_num"] = df["watched_at"].dt.month
    monthly_trend = (
        df.groupby(["month_num", "month"], dropna=False)["watch_hours"]
        .sum()
        .reset_index()
        .sort_values("month_num")
        .loc[:, ["month", "watch_hours"]]
    )

    # Channels (top by watch hours and counts)
    chan_hours = (
        df.groupby(df.get("channel").fillna("Unknown"))["watch_hours"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )
    if chan_hours.columns[0] != "channel":
        chan_hours = chan_hours.rename(columns={chan_hours.columns[0]: "channel"})

    n_head = min(10, len(chan_hours))
    chan_count = (
        df.groupby(df.get("channel").fillna("Unknown"))["title"]
        .count()
        .sort_values(ascending=False)
        .head(n_head)
        .reset_index()
        .rename(columns={"title": "count"})
    )
    if chan_count.columns[0] != "channel":
        chan_count = chan_count.rename(columns={chan_count.columns[0]: "channel"})

    # Hourly watch hours
    hourly = df.copy()
    hourly["hour"] = hourly["watched_at"].dt.hour
    hourly_summary = (
        hourly.groupby("hour")["watch_hours"]
        .sum()
        .reindex(range(24), fill_value=0)
        .reset_index()
        .rename(columns={"watch_hours": "watch_hours"})
    )

    # Day of week watch hours
    dow_order = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    if "day_of_week" in df.columns:
        dow_summary = (
            df.groupby("day_of_week")["watch_hours"]
            .sum()
            .reindex(dow_order, fill_value=0)
            .reset_index()
            .rename(columns={"day_of_week": "day", "watch_hours": "watch_hours"})
        )
    else:
        dow_summary = pd.DataFrame({"day": dow_order, "watch_hours": [0] * 7})

    return {
        "kpis": {
            "total_watch_hours": round(total_watch_hours, 2),
            "total_videos": total_video_count,
            "daily_average": {
                "hours": daily_avg_hours_int,
                "minutes": daily_avg_minutes,
            },
        },
        "type_counts": type_counts.to_dict(orient="records"),
        "top_categories": top_categories.to_dict(orient="records"),
        "monthly_trend": monthly_trend.to_dict(orient="records"),
        "channels": {
            "watch_hours": chan_hours.to_dict(orient="records"),
            "watch_count": chan_count.to_dict(orient="records"),
        },
        "hourly": hourly_summary.to_dict(orient="records"),
        "day_of_week": dow_summary.to_dict(orient="records"),
    }
