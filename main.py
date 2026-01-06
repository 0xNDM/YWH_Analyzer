"""
Pipeline runner that chains steps 1–8 entirely in memory.
"""

import sys
from importlib import util
from pathlib import Path


ROOT = Path(__file__).parent


def load_step(module_name, filename):
    path = ROOT / filename
    spec = util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {filename}")
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main(watch_file):
    step1 = load_step("step1", "1_yt_vid_metadata.py")
    step2 = load_step("step2", "2_merged_data_to_csv.py")
    step3 = load_step("step3", "3_deduplicate.py")
    step4 = load_step("step4", "4_remove_live.py")
    step5 = load_step("step5", "5_remove_unavailable.py")
    step6 = load_step("step6", "6_remove_videos.py")
    step7 = load_step("step7", "7_to_the_hour.py")
    step8 = load_step("step8", "8_the_finishing.py")

    print("[1/8] Fetching metadata and filtering watch history (2025)…")
    history_2025, cache_list = step1.run(watch_file)

    print("[2/8] Merging watch history with metadata…")
    df = step2.run(history_2025, cache_list)

    print("[3/8] Deduplicating non-music videos…")
    df = step3.run(df)

    print("[4/8] Removing live streams…")
    df = step4.run(df)

    print("[5/8] Removing unavailable/deleted videos…")
    df = step5.run(df)

    print("[6/8] Capping long videos and sorting…")
    df = step6.run(df)

    print("[7/8] Flooring timestamps to the hour…")
    df = step7.run(df)

    print("[8/8] Adding day-of-week…")
    final_df = step8.run(df)

    final_path = ROOT / "ywh_final.csv"
    final_df.to_csv(final_path, index=False)

    print(f"Pipeline complete. Final file: {final_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <watch-history.json>")
        sys.exit(1)

    main(sys.argv[1])
