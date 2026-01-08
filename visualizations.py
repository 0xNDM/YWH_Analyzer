import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def clean_layout(fig):
    """Removes gridlines, axis lines, and background clutter."""
    fig.update_xaxes(showgrid=False, zeroline=False, showline=False)
    fig.update_yaxes(showgrid=False, zeroline=False, showline=False)
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="#0f0f0f", font_color="white"
    )
    return fig


def create_charts(df):
    """
    Generates all Plotly charts from the dataframe.
    Returns a dictionary of figures.
    """

    # Pre-processing for Plotly charts
    # Ensure date column is datetime
    if not pd.api.types.is_datetime64_any_dtype(df["watched_at"]):
        df["watched_at"] = pd.to_datetime(df["watched_at"])

    df["watch_hours"] = df["duration_seconds"] / 3600
    df["month"] = df["watched_at"].dt.strftime("%b")
    df["month_num"] = df["watched_at"].dt.month

    figs = {}

    # 1. KPI HERO (3 Cols)
    total_watch_hours = df["watch_hours"].sum()
    total_video_count = len(df)

    # Avoid division by zero if empty
    daily_avg_total_hours = total_watch_hours / 365
    daily_avg_hours_int = int(daily_avg_total_hours)
    daily_avg_minutes = int(round((daily_avg_total_hours - daily_avg_hours_int) * 60))

    fig_kpi = make_subplots(
        rows=1,
        cols=3,
        specs=[[{"type": "indicator"}, {"type": "indicator"}, {"type": "indicator"}]],
        horizontal_spacing=0.05,
    )
    fig_kpi.add_trace(
        go.Indicator(
            mode="number",
            value=total_watch_hours,
            number={"suffix": " hrs", "valueformat": ".1f", "font": {"size": 50}},
            title={"text": "Total Watch Hours", "font": {"size": 16}},
        ),
        row=1,
        col=1,
    )
    fig_kpi.add_trace(
        go.Indicator(
            mode="number",
            value=total_video_count,
            number={"valueformat": ",.0f", "font": {"size": 50}},
            title={"text": "Total Videos", "font": {"size": 16}},
        ),
        row=1,
        col=2,
    )
    fig_kpi.add_trace(
        go.Indicator(
            mode="number",
            value=daily_avg_hours_int,
            number={
                "suffix": f" hrs {daily_avg_minutes} min",
                "valueformat": "d",
                "font": {"size": 50},
            },
            title={"text": "Daily Average", "font": {"size": 16}},
        ),
        row=1,
        col=3,
    )
    fig_kpi.update_layout(
        paper_bgcolor="#0f0f0f",
        plot_bgcolor="#0f0f0f",
        font_color="white",
        margin=dict(t=40, b=20, l=60, r=20),
        height=250,
    )
    figs["kpi"] = fig_kpi

    # 2. Donut + Treemap (1 Row)
    type_counts = df["type"].value_counts().reset_index()
    type_counts.columns = ["type", "count"]

    cat_summary = (
        df.groupby("category")["watch_hours"]
        .sum()
        .reset_index()
        .sort_values("watch_hours", ascending=False)
        .head(6)
    )

    # Create Treemap using px to get the trace with correct colors
    treemap_colors = ["#2b2b2b", "#3a3a3a", "#4a4a4a", "#5a5a5a", "#6a6a6a", "#7a7a7a"]
    # Map colors to categories explicitly to ensure order (Largest -> Darkest/First)
    color_map = dict(zip(cat_summary["category"], treemap_colors))

    fig_tm_temp = px.treemap(
        cat_summary,
        path=["category"],
        values="watch_hours",
        color="category",
        color_discrete_map=color_map,
    )
    fig_tm_temp.update_traces(
        hovertemplate="<b>%{label}</b><br>Watch Hours: %{value:.1f}<extra></extra>",
        textfont=dict(size=18),
    )

    fig_mixed = make_subplots(
        rows=1,
        cols=2,
        specs=[[{"type": "domain"}, {"type": "treemap"}]],
        column_widths=[0.3, 0.7],
        subplot_titles=("Short vs Long-form", "Top 6 Categories by Watch Hours"),
    )

    fig_mixed.add_trace(
        go.Pie(
            labels=type_counts["type"],
            values=type_counts["count"],
            hole=0.6,
            marker=dict(colors=["#ff0000", "#A11212"]),
            textinfo="percent+label",
            pull=[0.05, 0],
            showlegend=False,
            hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Percent: %{percent}<extra></extra>",
        ),
        row=1,
        col=1,
    )

    fig_mixed.add_trace(fig_tm_temp.data[0], row=1, col=2)

    fig_mixed.update_layout(
        paper_bgcolor="#0f0f0f",
        plot_bgcolor="#0f0f0f",
        font_color="white",
        margin=dict(t=60, b=20, l=20, r=20),
        height=400,
    )
    figs["mixed"] = fig_mixed

    # 3. Monthly Trend (Area)
    monthly = (
        df.groupby(["month_num", "month"])["watch_hours"]
        .sum()
        .reset_index()
        .sort_values("month_num")
    )
    fig_trend = px.area(
        monthly, x="month", y="watch_hours", title="Monthly Watch Hours Trend"
    )
    fig_trend.update_traces(
        line_color="#3498db",
        fillcolor="rgba(52, 152, 219, 0.2)",
        line_shape="spline",
        hovertemplate="<b>%{x}</b><br>Watch Hours: %{y:.1f} hrs<extra></extra>",
    )
    clean_layout(fig_trend)
    figs["trend"] = fig_trend

    # 4. Watch Hours and Watch Count by Channel (facing bars)
    chan_hours = df.groupby("channel")["watch_hours"].sum().nlargest(10).reset_index()
    # Handle cases where we might have fewer than 10 channels
    n_head = min(10, len(chan_hours))
    chan_count = df.groupby("channel")["title"].count().nlargest(n_head).reset_index()

    fig_channels = make_subplots(
        rows=1,
        cols=2,
        shared_yaxes=False,
        horizontal_spacing=0.12,
        subplot_titles=("Watch Hours by Channel", "Watch Count by Channel"),
    )
    fig_channels.add_trace(
        go.Bar(
            y=chan_hours["channel"],
            x=chan_hours["watch_hours"],
            orientation="h",
            marker_color="#4a5e7d",
            name="Watch Hours",
            hovertemplate="<b>%{y}</b><br>Watch Hours: %{x:.1f}<extra></extra>",
        ),
        row=1,
        col=1,
    )
    fig_channels.add_trace(
        go.Bar(
            y=chan_count["channel"],
            x=chan_count["title"],
            orientation="h",
            marker_color="#6c7a89",
            name="Watch Count",
            hovertemplate="<b>%{y}</b><br>Count: %{x}<extra></extra>",
        ),
        row=1,
        col=2,
    )
    fig_channels.update_layout(
        paper_bgcolor="#0f0f0f",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="white",
        showlegend=False,
        margin=dict(t=60, b=40, l=40, r=40),
    )
    fig_channels.update_xaxes(showgrid=False, title_text="Watch Hours", row=1, col=1)
    fig_channels.update_xaxes(
        showgrid=False, title_text="Watch Count", autorange="reversed", row=1, col=2
    )
    fig_channels.update_yaxes(
        showgrid=False, categoryorder="total ascending", row=1, col=1
    )
    fig_channels.update_yaxes(
        showgrid=False, categoryorder="total ascending", side="right", row=1, col=2
    )
    figs["channels"] = fig_channels

    # 5. Time of Day (Watch Hours)
    hourly = df.copy()
    hourly["hour"] = hourly["watched_at"].dt.hour
    hourly_summary = hourly.groupby("hour")["watch_hours"].sum()
    hourly_summary = hourly_summary.reindex(range(24), fill_value=0).reset_index()
    hourly_summary.columns = ["hour", "watch_hours"]
    fig_hour = px.bar(
        hourly_summary,
        x="hour",
        y="watch_hours",
        title="Watch Hours by Time of Day (GMT + 0)",
        color_discrete_sequence=["#6fa3ef"],
    )
    clean_layout(fig_hour)
    fig_hour.update_traces(
        hovertemplate="<b>%{x}:00</b><br>Watch Hours: %{y:.1f}<extra></extra>"
    )
    fig_hour.update_layout(margin=dict(t=60, b=40, l=30, r=20), xaxis=dict(dtick=1))
    figs["hour"] = fig_hour

    # 6. Day of Week by Watch Hours (Polar)
    dow_order = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    dow_summary = (
        df.groupby(df["watched_at"].dt.day_name())["watch_hours"]
        .sum()
        .reindex(dow_order)
        .reset_index()
    )
    dow_summary.columns = ["day_of_week", "watch_hours"]
    fig_dow = px.bar_polar(
        dow_summary,
        r="watch_hours",
        theta="day_of_week",
        category_orders={"day_of_week": dow_order},
        template="plotly_dark",
    )
    fig_dow.update_traces(
        marker_line_width=0,
        hovertemplate="<b>%{theta}</b><br>Watch Hours: %{r:.1f}<extra></extra>",
    )
    fig_dow.update_layout(
        title="Watch Hours by Day of Week (Polar)",
        paper_bgcolor="#0f0f0f",
        font_color="white",
    )
    figs["dow"] = fig_dow

    return figs
