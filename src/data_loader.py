"""
Load, parse, and filter the air raid alert dataset.
Supports caching: if processed CSV exists, loads it directly (fast).
"""

import pandas as pd
from src.config import (
    RAW_DATA_PATH,
    PROCESSED_FILE,
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
    print("AIR RAID ALERT DATASET — OBLAST LEVEL")
    print("=" * 60)
    print(f"Records:        {len(df):,}")
    print(f"Date range:     {df[COL_STARTED].min()}  →  {df[COL_STARTED].max()}")
    print(f"Unique oblasts: {df[COL_OBLAST].nunique()}")
    print(
        f"Duration range: {df[COL_DURATION].min():.0f}s  →  {df[COL_DURATION].max():.0f}s"
    )
    print(f"Duration mean:  {df[COL_DURATION].mean():.0f}s")
    print(f"Duration median:{df[COL_DURATION].median():.0f}s")
    print(f"\nOblasts ({df[COL_OBLAST].nunique()}):")
    for o in sorted(df[COL_OBLAST].unique()):
        count = len(df[df[COL_OBLAST] == o])
        print(f"  {o}: {count:,} alerts")
    print("=" * 60)


def load_and_prepare() -> pd.DataFrame:
    """
    Full pipeline with caching.
    If processed CSV exists → load it directly.
    Otherwise → load raw → filter → clean → save processed CSV.
    """
    if PROCESSED_FILE.exists():
        print(f"Loading cached data from {PROCESSED_FILE}")
        df = pd.read_csv(
            PROCESSED_FILE,
            parse_dates=[COL_STARTED, COL_FINISHED],
        )
        print_summary(df)
        return df

    print("Processing raw data (this may take a moment)...")
    df = load_raw_data()
    df = filter_oblast_level(df)
    df = compute_duration(df)
    df = remove_excluded_oblasts(df)
    df = remove_extreme_durations(df)

    # Save processed CSV for next time
    PROCESSED_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(PROCESSED_FILE, index=False)
    print(f"Saved processed data to {PROCESSED_FILE}")

    print_summary(df)
    return df


if __name__ == "__main__":
    df = load_and_prepare()
