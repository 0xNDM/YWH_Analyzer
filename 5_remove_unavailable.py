"""
Remove deleted or unavailable videos.
"""

import pandas as pd


def run(df):
    df = df.copy()
    df["watched_at"] = pd.to_datetime(df["watched_at"], errors="coerce")

    valid_videos = df[df["channel"].notna() & df["duration_seconds"].notna()].copy()

    return valid_videos
