import pandas as pd
import pytest

from src import analysis as an
from src.config import COL_DURATION, COL_OBLAST, COL_STARTED


def make_df(starts, oblasts=None, durations=None):
    n = len(starts)
    return pd.DataFrame(
        {
            COL_OBLAST: oblasts or ["A oblast"] * n,
            COL_STARTED: pd.to_datetime(starts, utc=True),
            COL_DURATION: durations or [600.0] * n,
        }
    )


def test_hours_use_kyiv_time_with_dst():
    # 21:30 UTC is 23:30 in winter (UTC+2) and 00:30 next day in summer (UTC+3)
    df = make_df(["2024-01-15 21:30", "2024-07-15 21:30"])
    by_hour = an.alerts_by_hour(df).set_index("hour")["alert_count"]
    assert by_hour.to_dict() == {0: 1, 23: 1}


def test_daily_counts_use_local_date_and_fill_empty_days():
    # 22:30 UTC on Jan 1 is already Jan 2 in Kyiv; Jan 3 has no alerts
    df = make_df(["2024-01-01 22:30", "2024-01-02 08:00", "2024-01-04 08:00"])
    daily = an.alerts_by_date(df).set_index("date")["alert_count"]
    assert daily.to_dict() == {
        pd.Timestamp("2024-01-02"): 2,
        pd.Timestamp("2024-01-03"): 0,
        pd.Timestamp("2024-01-04"): 1,
    }


def test_time_of_day_split_is_22_to_06_local():
    # local hours: 05 (night), 06 (day), 21 (day), 22 (night)
    df = make_df(
        ["2024-01-15 03:00", "2024-01-15 04:00", "2024-01-15 19:00", "2024-01-15 20:00"]
    )
    counts = an.alerts_by_timeofday(df).set_index("time_of_day")["alert_count"]
    assert counts.to_dict() == {"Day": 2, "Night": 2}


def test_alerts_by_oblast_sorted_with_mean_duration():
    df = make_df(
        ["2024-01-01 10:00"] * 3,
        oblasts=["B oblast", "A oblast", "A oblast"],
        durations=[100.0, 200.0, 400.0],
    )
    out = an.alerts_by_oblast(df)
    assert list(out[COL_OBLAST]) == ["A oblast", "B oblast"]
    assert out["avg_duration_s"].tolist() == [300.0, 100.0]


def test_holdout_metrics():
    pytest.importorskip("prophet")
    from src.forecasting import holdout_metrics

    ds = pd.date_range("2024-01-01", periods=2)
    result = {
        "prediction": pd.DataFrame({"ds": ds, "yhat": [10.0, 20.0]}),
        "actual": pd.DataFrame({"date": ds, "alert_count": [20, 0]}),
        "history": pd.DataFrame({"alert_count": [10.0, 10.0]}),
    }
    m = holdout_metrics(result, "alert_count")
    assert m["days"] == 2
    assert m["mae"] == 15.0  # (|10-20| + |20-0|) / 2
    assert m["mape_pct"] == 50.0  # zero actuals are skipped: |10-20| / 20
    assert m["naive_mae"] == 10.0  # baseline 10: (|10-20| + |10-0|) / 2


def test_train_test_requires_enough_history():
    pytest.importorskip("prophet")
    from src.forecasting import _train_test

    daily = pd.DataFrame(
        {"date": pd.date_range("2024-01-01", periods=10), "alert_count": range(10)}
    )
    with pytest.raises(ValueError):
        _train_test(daily, "2024-01-10")
