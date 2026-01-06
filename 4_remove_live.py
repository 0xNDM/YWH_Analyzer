"""
Remove live streams longer than the duration threshold.
"""

import pandas as pd


def run(df, duration_threshold=3600):
    df = df.copy()
    df["duration_seconds"] = pd.to_numeric(df["duration_seconds"], errors="coerce")

    mask = df["title"].astype(str).str.lower().str.contains(
        r"live|stream", regex=True, na=False
    ) & (df["duration_seconds"] > duration_threshold)

    return df.loc[~mask].copy()
