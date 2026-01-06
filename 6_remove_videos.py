"""
Cap long videos at 4 hours and keep chronological order.
"""

import pandas as pd


def run(df):
    df = df.copy()
    df.columns = df.columns.str.strip().str.lower()
    df["duration_seconds"] = pd.to_numeric(df["duration_seconds"], errors="coerce")
    df["duration_seconds"] = df["duration_seconds"].clip(upper=14400)

    df_clean = df.sort_values("watched_at").reset_index(drop=True)
    return df_clean
