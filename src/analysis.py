"""
Statistical analysis of air raid alert patterns.
"""

import pandas as pd
import numpy as np
from src.config import (
    COL_OBLAST,
    COL_STARTED,
    COL_DURATION,
    SEASON_MAP,
    NIGHT_START_HOUR,
    NIGHT_END_HOUR,
)


def _hour_label(h: int) -> str:
    """Format hour as '7:00-8:00' interval."""
    return f"{h}:00-{h+1}:00"


def alerts_by_oblast(df: pd.DataFrame) -> pd.DataFrame:
    """Total alert count and avg duration per oblast, sorted descending."""
    return (
        df.groupby(COL_OBLAST, observed=True)
        .agg(alert_count=(COL_STARTED, "count"), avg_duration_s=(COL_DURATION, "mean"))
        .sort_values("alert_count", ascending=False)
        .reset_index()
    )


def alerts_by_date(df: pd.DataFrame) -> pd.DataFrame:
    """Daily alert count across all oblasts."""
    date_col = df[COL_STARTED].dt.tz_convert(None).dt.date
    return (
        df.groupby(date_col, observed=True)
        .size()
        .reset_index(name="alert_count")
        .rename(columns={COL_STARTED: "date"})
    )


def alerts_by_hour(df: pd.DataFrame) -> pd.DataFrame:
    """Alert count by hour interval [hour, hour+1)."""
    hour = df[COL_STARTED].dt.tz_convert(None).dt.hour
    df = df.copy()
    df["hour"] = hour
    df["hour_label"] = hour.map(_hour_label)
    result = (
        df.groupby(["hour", "hour_label"], observed=True)
        .size()
        .reset_index(name="alert_count")
        .sort_values("hour")
        .reset_index(drop=True)
    )
    return result


def alerts_by_dayofweek(df: pd.DataFrame) -> pd.DataFrame:
    """Alert count by day of week (0=Monday, 6=Sunday)."""
    dow = df[COL_STARTED].dt.tz_convert(None).dt.dayofweek
    return (
        df.groupby(dow, observed=True)
        .size()
        .reset_index(name="alert_count")
        .rename(columns={COL_STARTED: "dayofweek"})
    )


def alerts_by_month(df: pd.DataFrame) -> pd.DataFrame:
    """Alert count by month (1-12), aggregated across all years."""
    month = df[COL_STARTED].dt.tz_convert(None).dt.month
    return (
        df.groupby(month, observed=True)
        .size()
        .reset_index(name="alert_count")
        .rename(columns={COL_STARTED: "month"})
    )


def alerts_by_season(df: pd.DataFrame) -> pd.DataFrame:
    """Alert count by season (Winter/Spring/Summer/Autumn)."""
    month = df[COL_STARTED].dt.tz_convert(None).dt.month
    df = df.copy()
    df["season"] = month.map(SEASON_MAP)
    return df.groupby("season", observed=True).size().reset_index(name="alert_count")


def alerts_by_timeofday(df: pd.DataFrame) -> pd.DataFrame:
    """Alert count: Night (22:00-06:00) vs Day (06:00-22:00)."""
    hour = df[COL_STARTED].dt.tz_convert(None).dt.hour
    df = df.copy()
    df["time_of_day"] = np.where(
        (hour >= NIGHT_START_HOUR) | (hour < NIGHT_END_HOUR),
        "Night",
        "Day",
    )
    return (
        df.groupby("time_of_day", observed=True).size().reset_index(name="alert_count")
    )


def duration_stats(df: pd.DataFrame) -> dict:
    """Basic duration statistics."""
    return {
        "min_s": float(df[COL_DURATION].min()),
        "max_s": float(df[COL_DURATION].max()),
        "mean_s": float(df[COL_DURATION].mean()),
        "median_s": float(df[COL_DURATION].median()),
        "std_s": float(df[COL_DURATION].std()),
        "p25_s": float(df[COL_DURATION].quantile(0.25)),
        "p75_s": float(df[COL_DURATION].quantile(0.75)),
    }


def duration_by_oblast(df: pd.DataFrame) -> pd.DataFrame:
    """Average alert duration per oblast."""
    return (
        df.groupby(COL_OBLAST, observed=True)[COL_DURATION]
        .agg(["mean", "median", "count"])
        .sort_values("mean", ascending=False)
        .reset_index()
        .rename(
            columns={
                "mean": "avg_duration_s",
                "median": "median_duration_s",
                "count": "alert_count",
            }
        )
    )


def top_alert_days(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Top N days with the most alerts."""
    daily = alerts_by_date(df)
    return daily.sort_values("alert_count", ascending=False).head(n)


def duration_by_hour(df: pd.DataFrame) -> pd.DataFrame:
    """Average alert duration by start hour interval [hour, hour+1)."""
    hour = df[COL_STARTED].dt.tz_convert(None).dt.hour
    df = df.copy()
    df["hour"] = hour
    df["hour_label"] = hour.map(_hour_label)
    return (
        df.groupby(["hour", "hour_label"], observed=True)[COL_DURATION]
        .agg(["mean", "median", "count"])
        .sort_values("mean", ascending=False)
        .reset_index()
        .rename(
            columns={
                "hour_label": "interval",
                "mean": "avg_duration_s",
                "median": "median_duration_s",
                "count": "alert_count",
            }
        )
        .drop(columns=["hour"])
    )


def print_hourly_distribution(hour_df: pd.DataFrame) -> None:
    """Print all 24 hours with a visual bar chart."""
    print("\n--- HOURLY DISTRIBUTION ---")
    print("Interval     | Alerts  | Bar")
    print("-------------|---------|-----------------------------")
    for _, row in hour_df.iterrows():
        label = row["hour_label"]
        count = int(row["alert_count"])
        bar = "#" * (count // 100)
        print(f"{label:<12s} | {count:>6,} | {bar}")
    print()


def run_analysis(df: pd.DataFrame) -> dict:
    """Run all analyses and return results as a dict of DataFrames + stats."""
    print("\n--- ANALYSIS ---")

    results = {
        "by_oblast": alerts_by_oblast(df),
        "by_date": alerts_by_date(df),
        "by_hour": alerts_by_hour(df),
        "by_dayofweek": alerts_by_dayofweek(df),
        "by_month": alerts_by_month(df),
        "by_season": alerts_by_season(df),
        "by_timeofday": alerts_by_timeofday(df),
        "duration_stats": duration_stats(df),
        "duration_by_oblast": duration_by_oblast(df),
        "duration_by_hour": duration_by_hour(df),
        "top_days": top_alert_days(df),
    }

    # Print highlights
    print("Top 5 oblasts by alert count:")
    print(results["by_oblast"].head(5).to_string(index=False))

    print("\nTop 5 oblasts by avg duration:")
    print(results["duration_by_oblast"].head(5).to_string(index=False))

    print(f"\nAlerts by season:\n{results['by_season'].to_string(index=False)}")
    print(f"\nAlerts by time of day:\n{results['by_timeofday'].to_string(index=False)}")

    print_hourly_distribution(results["by_hour"])

    print("\nTop 5 busiest intervals:")
    print(
        results["by_hour"]
        .sort_values("alert_count", ascending=False)
        .head(5)
        .to_string(index=False)
    )

    print("\nTop 5 longest avg duration by start interval:")
    print(results["duration_by_hour"].head(5).to_string(index=False))

    ds = results["duration_stats"]
    print(f"\nDuration: mean={ds['mean_s']:.0f}s, median={ds['median_s']:.0f}s")
    print(f"Duration percentile: 25%={ds['p25_s']:.0f}s, 75%={ds['p75_s']:.0f}s")

    print("\nTop 3 busiest days:")
    print(results["top_days"].head(3).to_string(index=False))

    return results


if __name__ == "__main__":
    from src.data_loader import load_and_prepare

    df = load_and_prepare()
    run_analysis(df)
