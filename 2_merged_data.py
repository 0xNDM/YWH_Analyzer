"""
Merge watch history entries with cached video metadata and return a DataFrame.
"""

import pandas as pd


# Category mapping
CATEGORY_MAP = {
    "1": "Film & Animation",
    "2": "Autos & Vehicles",
    "10": "Music",
    "15": "Pets & Animals",
    "17": "Sports",
    "19": "Travel & Events",
    "20": "Gaming",
    "22": "People & Blogs",
    "23": "Comedy",
    "24": "Entertainment",
    "25": "News & Politics",
    "26": "Howto & Style",
    "27": "Education",
    "28": "Science & Technology",
    "29": "Nonprofits & Activism",
    "30": "Movies",
    "31": "Anime/Animation",
    "32": "Action/Adventure",
    "33": "Classics",
    "34": "Comedy",
    "35": "Documentary",
    "36": "Drama",
    "37": "Family",
    "38": "Foreign",
    "39": "Horror",
    "40": "Sci-Fi/Fantasy",
    "41": "Thriller",
    "42": "Shorts",
    "43": "Shows",
    "44": "Trailers",
}


def run(watch_history, cache_list):
    cache_by_id = {v["video_id"]: v for v in cache_list}

    merged_rows = []

    for entry in watch_history:
        if "titleUrl" not in entry or "watch?v=" not in entry["titleUrl"]:
            continue

        video_id = (
            entry["titleUrl"].replace("\\u003d", "=").split("watch?v=")[1].split("&")[0]
        )

        watched_at = entry.get("time")
        video_meta = cache_by_id.get(video_id)

        duration_seconds = (
            video_meta["contentDetails"]["duration_seconds"]
            if video_meta and video_meta.get("contentDetails")
            else None
        )

        video_type = (
            "Short" if duration_seconds and duration_seconds <= 90 else "Long-form"
        )

        category_id = (
            video_meta["snippet"].get("categoryId")
            if video_meta and video_meta.get("snippet")
            else None
        )
        category_name = (
            CATEGORY_MAP.get(str(category_id), "Unknown") if category_id else None
        )

        channel_title = (
            video_meta["snippet"].get("channelTitle")
            if video_meta and video_meta.get("snippet")
            else None
        )

        merged_rows.append(
            {
                "title": (
                    video_meta["snippet"].get("title")
                    if video_meta and video_meta.get("snippet")
                    else entry.get("title")
                ),
                "channel": channel_title,
                "watched_at": watched_at,
                "published_at": (
                    video_meta["snippet"].get("publishedAt_sql")
                    if video_meta and video_meta.get("snippet")
                    else None
                ),
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "video_id": video_id,
                "category_id": category_id,
                "category": category_name,
                "duration_seconds": duration_seconds,
                "views": (
                    video_meta["statistics"].get("viewCount")
                    if video_meta and video_meta.get("statistics")
                    else None
                ),
                "likes": (
                    video_meta["statistics"].get("likeCount")
                    if video_meta and video_meta.get("statistics")
                    else None
                ),
                "type": video_type,
            }
        )

    return pd.DataFrame(merged_rows)
