"""
Floor watched_at and published_at to the hour.
"""

import pandas as pd


def run(df):
    df = df.copy()
    df["watched_at"] = pd.to_datetime(
        df["watched_at"], errors="coerce", utc=True
    ).dt.tz_convert(None)
    df["published_at"] = pd.to_datetime(
        df.get("published_at"), errors="coerce", utc=True
    ).dt.tz_convert(None)

    df["watched_at"] = df["watched_at"].dt.floor("h")
    if "published_at" in df.columns:
        df["published_at"] = df["published_at"].dt.floor("h")

    return df
