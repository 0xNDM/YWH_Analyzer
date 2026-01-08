"""In-memory pipeline for API usage.

- Accepts watch-history JSON (already loaded or bytes/string)
- Runs the existing step modules entirely in memory (no CSV writes)
- Returns the final DataFrame
"""

from importlib import util
from pathlib import Path
import json
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

ROOT = Path(__file__).parent


def load_step(module_name: str, filename: str):
    path = ROOT / filename
    spec = util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {filename}")
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


def _prepare_metadata_in_memory(
    history: List[dict], cache: Optional[Dict[str, dict]] = None
) -> Tuple[List[dict], List[dict]]:
    """Mimic step1 logic without touching disk. Returns (history_2025, cache_list)."""
    step1 = load_step("step1", "1_yt_vid_metadata.py")

    cache = cache or {}
    history_2025 = [e for e in history if step1.entry_year(e) == 2025]

    watch_times: Dict[str, Dict[str, Any]] = {}
    video_ids = set()

    for e in history_2025:
        url = e.get("titleUrl", "")
        if "watch?v=" not in url:
            continue
        vid = url.replace("\\u003d", "=").split("watch?v=")[1].split("&")[0]
        video_ids.add(vid)
        iso_time = e.get("time")
        if vid not in watch_times:
            watch_times[vid] = {"watched_at_sql": step1.iso_to_mysql(iso_time)}

    missing = [vid for vid in video_ids if vid not in cache]
    if missing:
        fetched = step1.fetch_metadata(missing, watch_times)
        cache.update(fetched)

    for vid in video_ids:
        if vid not in cache:
            continue
        wt = watch_times.get(vid)
        if wt:
            cache[vid]["watched_at_sql"] = wt.get("watched_at_sql")
        snippet = cache[vid].get("snippet")
        if snippet:
            if "publishedAt" in snippet:
                snippet["publishedAt_sql"] = step1.iso_to_mysql(snippet["publishedAt"])
                snippet.pop("publishedAt", None)
            elif "publishedAt_sql" not in snippet:
                snippet["publishedAt_sql"] = ""

    return history_2025, list(cache.values())


def run_pipeline(history: List[dict]) -> pd.DataFrame:
    """Run the full pipeline in memory and return final_df."""
    step2 = load_step("step2", "2_merged_data.py")
    step3 = load_step("step3", "3_deduplicate.py")
    step4 = load_step("step4", "4_remove_live.py")
    step5 = load_step("step5", "5_remove_unavailable.py")
    step6 = load_step("step6", "6_remove_videos.py")
    step7 = load_step("step7", "7_to_the_hour.py")
    step8 = load_step("step8", "8_the_finishing.py")

    history_2025, cache_list = _prepare_metadata_in_memory(history)

    df = step2.run(history_2025, cache_list)
    df = step3.run(df)
    df = step4.run(df)
    df = step5.run(df)
    df = step6.run(df)
    df = step7.run(df)
    final_df = step8.run(df)

    return final_df


def dataframes_to_csv_bytes(final_df: pd.DataFrame) -> bytes:
    """Convert DataFrame to CSV bytes (no disk writes)."""
    return final_df.to_csv(index=False).encode("utf-8")


def run_from_bytes(watch_history_bytes: bytes) -> pd.DataFrame:
    """Convenience: accept uploaded bytes and run the pipeline."""
    history = json.loads(watch_history_bytes.decode("utf-8"))
    if not isinstance(history, list):
        raise ValueError("watch-history JSON must be a list")
    return run_pipeline(history)


def run_from_str(watch_history_str: str) -> pd.DataFrame:
    return run_from_bytes(watch_history_str.encode("utf-8"))


__all__ = [
    "run_pipeline",
    "run_from_bytes",
    "run_from_str",
    "dataframes_to_csv_bytes",
]
