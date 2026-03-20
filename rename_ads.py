"""
rename_ads.py — Adorix Ad File Migration Script
================================================
One-time utility to rename existing .mp4 and .json ad files in backend/ads/
from the OLD 6-bucket naming scheme to the NEW 4-bucket naming scheme.

OLD Buckets: 10-15, 16-29, 30-39, 40-49, 50-59, above-60
NEW Buckets: under-20, 20-40, 40-60, above-60

Usage:
    # Dry-run (default — no files are changed, just shows what WOULD happen):
    python rename_ads.py

    # Execute the actual rename:
    python rename_ads.py --execute
"""

import os
import sys
import shutil

# ── Configuration ─────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ADS_DIR    = os.path.join(SCRIPT_DIR, "backend", "ads")

# Map: OLD filename stem → NEW filename stem
# Where multiple old files collapse into one new bucket,
# we pick the LARGEST file (best quality) as the canonical source.
# The mapping below is explicit — every old stem gets a new stem.
RENAME_MAP = {
    # OLD                 NEW
    "10-15_female":  "under-20_female",
    "10-15_male":    "under-20_male",
    "16-29_female":  "20-40_female",
    "16-29_male":    "20-40_male",
    "30-39_female":  "20-40_female",   # consolidation: 30-39 → 20-40 (see note below)
    "30-39_male":    "20-40_male",     # consolidation: 30-39 → 20-40
    "40-49_female":  "40-60_female",
    "40-49_male":    "40-60_male",
    "50-59_female":  "40-60_female",   # consolidation: 50-59 → 40-60
    "50-59_male":    "40-60_male",     # consolidation: 50-59 → 40-60
    "above-60_female": "above-60_female",
    "above-60_male":   "above-60_male",
}
# Note on consolidation: when two old files map to the same new file,
# the script automatically PICKS THE LARGEST ONE as the winner and
# renames it, skipping the smaller duplicate. This maximises video quality.

EXTENSIONS = [".mp4", ".json"]
# ──────────────────────────────────────────────────────────────────────────────


def get_candidates():
    """
    Scan ads/ for old-format files and build a list of (old_path, new_path, size_bytes).
    Groups by target new name so we can resolve conflicts.
    """
    if not os.path.isdir(ADS_DIR):
        print(f"[ERROR] Ads directory not found: {ADS_DIR}")
        sys.exit(1)

    # target_new_name → list of (old_path, size)
    mp4_candidates: dict[str, list] = {}

    for filename in os.listdir(ADS_DIR):
        stem, ext = os.path.splitext(filename)
        if ext.lower() != ".mp4":
            continue
        if stem not in RENAME_MAP:
            continue  # already renamed or unknown — skip

        new_stem = RENAME_MAP[stem]
        old_path = os.path.join(ADS_DIR, filename)
        size     = os.path.getsize(old_path)

        if new_stem not in mp4_candidates:
            mp4_candidates[new_stem] = []
        mp4_candidates[new_stem].append((old_path, size))

    return mp4_candidates


def resolve_conflicts(mp4_candidates):
    """
    For each new name bucket, if multiple old files compete, keep the largest.
    Returns: list of (old_mp4_path, new_mp4_path) tuples to process.
    """
    operations = []
    skipped    = []

    for new_stem, candidates in mp4_candidates.items():
        # Sort by size descending → winner is first
        candidates.sort(key=lambda x: x[1], reverse=True)

        winner_path, winner_size = candidates[0]
        new_mp4_path = os.path.join(ADS_DIR, f"{new_stem}.mp4")
        operations.append((winner_path, new_mp4_path))

        # Losers (smaller duplicates) — mark for skip/delete
        for loser_path, loser_size in candidates[1:]:
            skipped.append((loser_path, winner_path, winner_size, loser_size))

    return operations, skipped


def build_json_op(old_mp4_path, new_mp4_path):
    """Given an mp4 rename pair, return the corresponding JSON rename pair (may be None)."""
    old_json = old_mp4_path.replace(".mp4", ".json")
    new_json = new_mp4_path.replace(".mp4", ".json")
    if os.path.exists(old_json):
        return (old_json, new_json)
    return None


def run(dry_run=True):
    print("=" * 60)
    print("  ADORIX AD RENAME MIGRATION SCRIPT")
    print(f"  Mode: {'DRY-RUN (no files changed)' if dry_run else '*** EXECUTE — FILES WILL BE RENAMED ***'}")
    print(f"  Ads Directory: {ADS_DIR}")
    print("=" * 60)

    mp4_candidates = get_candidates()

    if not mp4_candidates:
        print("\n[INFO] No old-format .mp4 files found. Nothing to rename.")
        print("       (Files may already be renamed, or the ads/ directory is empty.)")
        return

    operations, skipped = resolve_conflicts(mp4_candidates)

    print(f"\n[PLAN] {len(operations)} rename operation(s):")
    all_ops = []
    for old_mp4, new_mp4 in operations:
        old_name = os.path.basename(old_mp4)
        new_name = os.path.basename(new_mp4)
        size_kb  = os.path.getsize(old_mp4) // 1024
        status   = ""
        if os.path.exists(new_mp4) and old_mp4 != new_mp4:
            status = "  ⚠️  TARGET ALREADY EXISTS — will overwrite"
        print(f"  MP4 : {old_name:30} →  {new_name}  ({size_kb} KB){status}")
        all_ops.append(("mp4", old_mp4, new_mp4))

        json_op = build_json_op(old_mp4, new_mp4)
        if json_op:
            old_json, new_json = json_op
            print(f"  JSON: {os.path.basename(old_json):30} →  {os.path.basename(new_json)}")
            all_ops.append(("json", old_json, new_json))

    if skipped:
        print(f"\n[SKIP] {len(skipped)} duplicate(s) discarded (smaller file loses):")
        for loser, winner, w_size, l_size in skipped:
            print(f"  SKIP  {os.path.basename(loser):30}  ({l_size//1024} KB)  — winner: {os.path.basename(winner)} ({w_size//1024} KB)")

    if dry_run:
        print("\n[DRY-RUN] No files were changed.")
        print("          Run with --execute to apply the above renames.")
        return

    # ── Execute ──────────────────────────────────────────────────────────────
    print("\n[EXEC] Applying renames...")
    success = 0
    failures = 0
    for kind, old_path, new_path in all_ops:
        if old_path == new_path:
            print(f"  SKIP (same name): {os.path.basename(old_path)}")
            continue
        try:
            shutil.move(old_path, new_path)
            print(f"  OK  : {os.path.basename(old_path)} → {os.path.basename(new_path)}")
            success += 1
        except Exception as e:
            print(f"  FAIL: {os.path.basename(old_path)} — {e}")
            failures += 1

    print(f"\n[DONE] {success} file(s) renamed, {failures} failure(s).")
    if failures == 0:
        print("       ✅ All ad files are now in the new 4-bucket format.")
        print("       ⚠️  Remember to re-upload the renamed files to your Supabase storage bucket")
        print("          and update the 'ads' table with the new filenames.")


if __name__ == "__main__":
    execute = "--execute" in sys.argv
    run(dry_run=not execute)
