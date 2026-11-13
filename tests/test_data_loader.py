import pandas as pd

from src import data_loader as dl
from src.config import COL_DURATION, COL_FINISHED, COL_STARTED, MAX_DURATION_SECONDS


def make_df(rows):
    df = pd.DataFrame(
        rows, columns=["oblast", "level", "started_at", "finished_at"]
    )
    df[COL_STARTED] = pd.to_datetime(df[COL_STARTED], utc=True)
    df[COL_FINISHED] = pd.to_datetime(df[COL_FINISHED], utc=True)
    return df


def test_drop_duplicate_rows_removes_exact_copies_only():
    df = make_df(
        [
            ["Lvivska oblast", "oblast", "2024-01-01 10:00", "2024-01-01 11:00"],
            ["Lvivska oblast", "oblast", "2024-01-01 10:00", "2024-01-01 11:00"],
            ["Lvivska oblast", "oblast", "2024-01-02 10:00", "2024-01-02 11:00"],
        ]
    )
    assert len(dl.drop_duplicate_rows(df)) == 2


def test_filter_oblast_level_keeps_only_oblast_rows():
    df = make_df(
        [
            ["A oblast", "oblast", "2024-01-01 10:00", "2024-01-01 11:00"],
            ["A oblast", "raion", "2024-01-01 10:00", "2024-01-01 11:00"],
            ["A oblast", "hromada", "2024-01-01 10:00", "2024-01-01 11:00"],
        ]
    )
    out = dl.filter_oblast_level(df)
    assert list(out["level"]) == ["oblast"]


def test_compute_duration_is_finished_minus_started_in_seconds():
    df = make_df([["A oblast", "oblast", "2024-01-01 10:00", "2024-01-01 10:30"]])
    assert dl.compute_duration(df)[COL_DURATION].iloc[0] == 1800.0


def test_remove_excluded_oblasts_drops_luhanska():
    df = make_df(
        [
            ["Luhanska oblast", "oblast", "2024-01-01 10:00", "2024-01-01 11:00"],
            ["Lvivska oblast", "oblast", "2024-01-01 10:00", "2024-01-01 11:00"],
        ]
    )
    out = dl.remove_excluded_oblasts(df)
    assert list(out["oblast"]) == ["Lvivska oblast"]


def test_remove_extreme_durations_keeps_exactly_max():
    df = pd.DataFrame(
        {COL_DURATION: [60.0, float(MAX_DURATION_SECONDS), MAX_DURATION_SECONDS + 1.0]}
    )
    out = dl.remove_extreme_durations(df)
    assert list(out[COL_DURATION]) == [60.0, float(MAX_DURATION_SECONDS)]
