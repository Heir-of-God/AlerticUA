"""
Load, parse, and filter the air raid alert dataset.
Supports caching: if processed CSV exists, loads it directly (fast).
"""

import hashlib
import json

import pandas as pd
from src.config import (
    RAW_DATA_PATH,
    PROCESSED_FILE,
    PROCESSED_META_FILE,
    CLEANING_VERSION,
    COL_OBLAST,
    COL_RAION,
    COL_HROMADA,
    COL_LEVEL,
    COL_STARTED,
    COL_FINISHED,
    COL_SOURCE,
    COL_DURATION,
    LEVEL_OBLAST,
    EXCLUDED_OBLASTS,
    MAX_DURATION_SECONDS,
    LOCAL_TZ,
)


def load_raw_data() -> pd.DataFrame:
    """Load CSV with proper types."""
    df = pd.read_csv(
        RAW_DATA_PATH,
        dtype={
            COL_OBLAST: "string",
            COL_RAION: "string",
            COL_HROMADA: "string",
            COL_LEVEL: "category",
            COL_SOURCE: "string",
        },
        parse_dates=[COL_STARTED, COL_FINISHED],
    )
    return df


def drop_duplicate_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Drop exact duplicate rows.

    The bundled raw file is two snapshots of the dataset concatenated, so most
    rows appear twice and every count would be inflated roughly 2x.
    """
    before = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    removed = before - len(df)
    if removed:
        print(f"Duplicate rows removed: {removed:,}")
    return df


def filter_oblast_level(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only oblast-level alerts."""
    return df[df[COL_LEVEL] == LEVEL_OBLAST].copy()


def compute_duration(df: pd.DataFrame) -> pd.DataFrame:
    """Add duration_seconds column = finished_at - started_at."""
    duration = df[COL_FINISHED] - df[COL_STARTED]
    df[COL_DURATION] = duration.dt.total_seconds().astype("float64")
    return df


def remove_excluded_oblasts(df: pd.DataFrame) -> pd.DataFrame:
    """Remove permanent siren regions (e.g. Luhanska oblast)."""
    before = len(df)
    df = df[~df[COL_OBLAST].isin(EXCLUDED_OBLASTS)].copy()
    removed = before - len(df)
    if removed:
        print(
            f"Excluded oblasts removed: {removed} rows ({', '.join(EXCLUDED_OBLASTS)})"
        )
    return df


def remove_extreme_durations(df: pd.DataFrame) -> pd.DataFrame:
    """Remove alerts longer than MAX_DURATION_SECONDS (14 days)."""
    before = len(df)
    df = df[df[COL_DURATION] <= MAX_DURATION_SECONDS].copy()
    removed = before - len(df)
    if removed:
        print(f"Extreme durations removed: {removed} rows (>14 days)")
    return df


def print_summary(df: pd.DataFrame) -> None:
    """Print a quick overview of the dataset."""
    print("=" * 60)
    print("AIR RAID ALERT DATASET - OBLAST LEVEL")
    print("=" * 60)
    print(f"Records:        {len(df):,}")
    started = df[COL_STARTED].dt.tz_convert(LOCAL_TZ)
    print(f"Date range:     {started.min():%Y-%m-%d}  ->  {started.max():%Y-%m-%d}")
    print(f"Unique oblasts: {df[COL_OBLAST].nunique()}")
    print(
        f"Duration range: {df[COL_DURATION].min():.0f}s  ->  {df[COL_DURATION].max():.0f}s"
    )
    print(f"Duration mean:  {df[COL_DURATION].mean():.0f}s")
    print(f"Duration median:{df[COL_DURATION].median():.0f}s")
    print(f"\nOblasts ({df[COL_OBLAST].nunique()}):")
    for o in sorted(df[COL_OBLAST].unique()):
        count = len(df[df[COL_OBLAST] == o])
        print(f"  {o}: {count:,} alerts")
    print("=" * 60)


def _raw_fingerprint() -> dict:
    """Identify the raw file content and cleaning logic a cache was built from."""
    sha = hashlib.sha256(RAW_DATA_PATH.read_bytes()).hexdigest()
    return {"raw_sha256": sha, "cleaning_version": CLEANING_VERSION}


def _cache_is_fresh(fingerprint: dict) -> bool:
    """True if the processed CSV exists and matches the current raw file and logic."""
    if not (PROCESSED_FILE.exists() and PROCESSED_META_FILE.exists()):
        return False
    try:
        return json.loads(PROCESSED_META_FILE.read_text()) == fingerprint
    except (OSError, ValueError):
        return False


def load_and_prepare() -> pd.DataFrame:
    """
    Full pipeline with caching.
    If the processed CSV matches the current raw file and cleaning version,
    load it directly. Otherwise rebuild it: load raw, deduplicate, filter,
    clean and save the processed CSV.
    """
    fingerprint = _raw_fingerprint()
    if _cache_is_fresh(fingerprint):
        print(f"Loading cached data from {PROCESSED_FILE}")
        df = pd.read_csv(
            PROCESSED_FILE,
            parse_dates=[COL_STARTED, COL_FINISHED],
        )
        print_summary(df)
        return df

    print("Processing raw data (this may take a moment)...")
    df = load_raw_data()
    df = drop_duplicate_rows(df)
    df = filter_oblast_level(df)
    df = compute_duration(df)
    df = remove_excluded_oblasts(df)
    df = remove_extreme_durations(df)

    # Save processed CSV for next time
    PROCESSED_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(PROCESSED_FILE, index=False)
    PROCESSED_META_FILE.write_text(json.dumps(fingerprint))
    print(f"Saved processed data to {PROCESSED_FILE}")

    print_summary(df)
    return df


if __name__ == "__main__":
    df = load_and_prepare()
