"""
Add day-of-week column.
"""

import pandas as pd


def run(df):
    df = df.copy()
    df["watched_at"] = pd.to_datetime(df["watched_at"])
    df["day_of_week"] = df["watched_at"].dt.day_name()
    return df
