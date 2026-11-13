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
    LOCAL_TZ,
)


def to_local(started: pd.Series) -> pd.Series:
    """Convert UTC start timestamps to Europe/Kyiv local time (tz-aware)."""
    return started.dt.tz_convert(LOCAL_TZ)


def hour_label(h: int) -> str:
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
    """Daily alert count (local dates) across all oblasts; days with no alerts get 0."""
    local = to_local(df[COL_STARTED])
    counts = local.dt.tz_localize(None).dt.normalize().value_counts()
    full_range = pd.date_range(counts.index.min(), counts.index.max(), freq="D")
    daily = counts.reindex(full_range, fill_value=0).sort_index()
    return daily.rename_axis("date").reset_index(name="alert_count")


def alerts_by_hour(df: pd.DataFrame) -> pd.DataFrame:
    """Alert count by hour interval [hour, hour+1)."""
    hour = to_local(df[COL_STARTED]).dt.hour
    df = df.copy()
    df["hour"] = hour
    df["hour_label"] = hour.map(hour_label)
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
    dow = to_local(df[COL_STARTED]).dt.dayofweek
    return (
        df.groupby(dow, observed=True)
        .size()
        .reset_index(name="alert_count")
        .rename(columns={COL_STARTED: "dayofweek"})
    )


def alerts_by_month(df: pd.DataFrame) -> pd.DataFrame:
    """Alert count by month (1-12), aggregated across all years."""
    month = to_local(df[COL_STARTED]).dt.month
    return (
        df.groupby(month, observed=True)
        .size()
        .reset_index(name="alert_count")
        .rename(columns={COL_STARTED: "month"})
    )


def alerts_by_season(df: pd.DataFrame) -> pd.DataFrame:
    """Alert count by season (Winter/Spring/Summer/Autumn)."""
    month = to_local(df[COL_STARTED]).dt.month
    df = df.copy()
    df["season"] = month.map(SEASON_MAP)
    return df.groupby("season", observed=True).size().reset_index(name="alert_count")


def alerts_by_timeofday(df: pd.DataFrame) -> pd.DataFrame:
    """Alert count: Night (22:00-06:00) vs Day (06:00-22:00)."""
    hour = to_local(df[COL_STARTED]).dt.hour
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
    hour = to_local(df[COL_STARTED]).dt.hour
    df = df.copy()
    df["hour"] = hour
    df["hour_label"] = hour.map(hour_label)
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


def alerts_by_dayofweek_hour(df: pd.DataFrame) -> pd.DataFrame:
    """Alert count per (day of week, start hour) cell in local time."""
    local = to_local(df[COL_STARTED])
    return (
        df.groupby(
            [local.dt.dayofweek.rename("dayofweek"), local.dt.hour.rename("hour")],
            observed=True,
        )
        .size()
        .reset_index(name="alert_count")
    )


def key_insights(df: pd.DataFrame, results: dict) -> list[str]:
    """Plain-language highlights computed from the data (nothing hardcoded)."""
    total = len(df)
    top3 = results["by_oblast"].head(3)
    share = top3["alert_count"].sum() / total * 100
    names = ", ".join(top3[COL_OBLAST].str.replace(" oblast", "", regex=False))

    hour = to_local(df[COL_STARTED]).dt.hour
    mean_s = df[COL_DURATION].mean()
    evening = df.loc[(hour >= 18) & (hour < 22), COL_DURATION].mean()
    night_mask = (hour >= NIGHT_START_HOUR) | (hour < NIGHT_END_HOUR)
    night_mean = df.loc[night_mask, COL_DURATION].mean()
    day_mean = df.loc[~night_mask, COL_DURATION].mean()

    tod = results["by_timeofday"].set_index("time_of_day")["alert_count"]
    seasons = results["by_season"].sort_values("alert_count", ascending=False)
    top_day = results["top_days"].iloc[0]

    return [
        f"{names} account for {share:.0f}% of all {total:,} alerts.",
        f"Alerts starting 18:00-22:00 last {evening / 60:.0f} min on average, "
        f"versus {mean_s / 60:.0f} min overall.",
        f"The busiest season is {seasons['season'].iloc[0]} "
        f"({seasons['alert_count'].iloc[0]:,} alerts) and the quietest is "
        f"{seasons['season'].iloc[-1]} ({seasons['alert_count'].iloc[-1]:,}).",
        f"{tod['Day'] / total * 100:.0f}% of alerts start during the day "
        f"({NIGHT_END_HOUR:02d}:00-{NIGHT_START_HOUR:02d}:00), but night alerts last "
        f"{night_mean / 60:.0f} min on average versus {day_mean / 60:.0f} min by day.",
        f"{top_day['date']:%d %B %Y} was the busiest single day "
        f"({int(top_day['alert_count'])} oblast-level alerts).",
    ]


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
