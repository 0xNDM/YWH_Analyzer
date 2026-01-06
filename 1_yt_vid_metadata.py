"""
Use youtube data API v3 to get metadata for the videos in watdh history
"""

from pathlib import Path
from datetime import datetime, timezone
import os
import re
import json
import requests
from dotenv import load_dotenv


CACHE_FILE = "youtube_video_cache_full.json"

load_dotenv()
API_KEYS = [
    key
    for key in (
        os.getenv("YT_API_1"),
        os.getenv("YT_API_2"),
        os.getenv("YT_API_3"),
        os.getenv("YT_API_4"),
    )
    if key
]

if not API_KEYS:
    raise RuntimeError("No YT_API keys found in .env file")


def iso8601_to_seconds(duration):
    """
    Convert ISO 8601 YouTube duration
    """
    if not duration or "D" in duration:
        return None

    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration)
    if not match:
        return None

    h = int(match.group(1) or 0)
    m = int(match.group(2) or 0)
    s = int(match.group(3) or 0)

    return h * 3600 + m * 60 + s


def load_cache():
    if Path(CACHE_FILE).exists():
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return {v["video_id"]: v for v in json.load(f)}
    return {}


def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(list(cache.values()), f, indent=2)


def iso_to_mysql(ts):
    """
    Convert ISO-8601 timestamp to MySQL DATETIME format.
    """
    if not ts:
        return ""

    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return ""


def entry_year(entry):
    """
    Return the year component of the watch history entry timestamp.
    """
    raw_time = entry.get("time")
    if not raw_time:
        return None

    try:
        return datetime.fromisoformat(raw_time.replace("Z", "+00:00")).year
    except ValueError:
        return None


# ------------------ API FETCH ------------------


def fetch_metadata(video_ids, watch_times=None):
    watch_times = watch_times or {}
    results = {}
    batch = []

    def query(ids):
        url = "https://www.googleapis.com/youtube/v3/videos"
        params = {
            "id": ",".join(ids),
            "part": "snippet,contentDetails,statistics,topicDetails",
        }

        last_err = None

        for idx, key in enumerate(API_KEYS):
            params["key"] = key

            try:
                r = requests.get(url, params=params, timeout=30)

                quota_hit = r.status_code in (403, 429)
                if quota_hit and idx + 1 < len(API_KEYS):
                    continue

                r.raise_for_status()
                break
            except requests.RequestException as exc:
                last_err = exc
                if idx + 1 < len(API_KEYS):
                    continue
                raise

        if last_err:
            # All keys failed; surface the last error
            raise last_err

        for item in r.json().get("items", []):
            results[item["id"]] = {
                "video_id": item["id"],
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "watched_at_sql": watch_times.get(item["id"], {}).get("watched_at_sql"),
                "snippet": {
                    "title": item["snippet"]["title"],
                    "channelTitle": item["snippet"]["channelTitle"],
                    "publishedAt_sql": iso_to_mysql(item["snippet"]["publishedAt"]),
                    "categoryId": item["snippet"]["categoryId"],
                },
                "contentDetails": {
                    "duration_seconds": iso8601_to_seconds(
                        item["contentDetails"]["duration"]
                    ),
                    "definition": item["contentDetails"].get("definition"),
                    "caption": item["contentDetails"].get("caption"),
                },
                "statistics": {
                    "viewCount": int(item["statistics"].get("viewCount", 0)),
                    "likeCount": int(item["statistics"].get("likeCount", 0)),
                },
                "topicDetails": item.get("topicDetails", {}),
            }

    for vid in video_ids:
        batch.append(vid)
        if len(batch) == 50:
            query(batch)
            batch.clear()

    if batch:
        query(batch)

    return results


def run(watch_data):
    if isinstance(watch_data, str) and os.path.exists(watch_data):
        with open(watch_data, "r", encoding="utf-8") as f:
            history = json.load(f)
    else:
        history = watch_data

    history_2025 = [e for e in history if entry_year(e) == 2025]

    watch_times = {}
    video_ids = set()

    for e in history_2025:
        if "titleUrl" not in e or "watch?v=" not in e["titleUrl"]:
            continue

        vid = e["titleUrl"].replace("\\u003d", "=").split("watch?v=")[1].split("&")[0]
        video_ids.add(vid)

        iso_time = e.get("time")
        if vid not in watch_times:
            watch_times[vid] = {
                "watched_at_sql": iso_to_mysql(iso_time),
            }

    cache = load_cache()
    missing = [vid for vid in video_ids if vid not in cache]

    if missing:
        fetched = fetch_metadata(missing, watch_times)
        cache.update(fetched)

    # Backfill watch and SQL time fields for cached entries we already had
    for vid in video_ids:
        if vid not in cache:
            continue

        wt = watch_times.get(vid)
        if wt:
            cache[vid]["watched_at_sql"] = wt.get("watched_at_sql")

        snippet = cache[vid].get("snippet")
        if snippet:
            if "publishedAt" in snippet:
                snippet["publishedAt_sql"] = iso_to_mysql(snippet["publishedAt"])
                snippet.pop("publishedAt", None)
            elif "publishedAt_sql" not in snippet:
                snippet["publishedAt_sql"] = ""

    save_cache(cache)

    return history_2025, list(cache.values())
