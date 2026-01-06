"""
Deduplicate non-music videos by title.
"""

import pandas as pd


def run(df):
    df = df.copy()
    df["watched_at"] = pd.to_datetime(df["watched_at"], errors="coerce")

    df["title_norm"] = df["title"].fillna("").str.strip().str.lower()

    df["category_norm"] = df["category"].fillna("").str.strip().str.lower()

    music_df = df[df["category_norm"] == "music"]
    non_music_df = df[df["category_norm"] != "music"]

    non_music_dedup = non_music_df.sort_values("watched_at").drop_duplicates(
        subset=["title_norm"], keep="last"
    )

    final_df = pd.concat([music_df, non_music_dedup], ignore_index=True)
    final_df = final_df.sort_values("watched_at")

    final_df = final_df.drop(columns=["title_norm", "category_norm"])

    return final_df
