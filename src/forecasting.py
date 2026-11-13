"""
Forecasting module using Prophet.
Predicts daily alert counts / average duration and compares with actual data.
"""

import logging

import pandas as pd
from prophet import Prophet

from src.analysis import alerts_by_date, to_local
from src.data_loader import load_and_prepare
from src.config import (
    COL_DURATION,
    COL_STARTED,
    DEFAULT_CUTOFF_DATE,
    FORECAST_DAYS,
)

MIN_TRAIN_DAYS = 60

# cmdstanpy logs every fit at INFO level
logging.getLogger("cmdstanpy").setLevel(logging.WARNING)


def _prepare_daily(df: pd.DataFrame) -> pd.DataFrame:
    """Daily alert count (local dates, empty days = 0), sorted by date."""
    return alerts_by_date(df).sort_values("date").reset_index(drop=True)


def _prepare_daily_duration(df: pd.DataFrame) -> pd.DataFrame:
    """Daily mean alert duration in seconds; days without alerts are absent."""
    day = to_local(df[COL_STARTED]).dt.tz_localize(None).dt.normalize().rename("date")
    daily = (
        df.groupby(day)[COL_DURATION]
        .mean()
        .reset_index()
        .rename(columns={COL_DURATION: "avg_duration_s"})
    )
    return daily.sort_values("date").reset_index(drop=True)


def _train_test(
    daily_df: pd.DataFrame, cutoff_date: str | pd.Timestamp
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Timestamp]:
    """Split daily data into train (<=cutoff) and test (next FORECAST_DAYS)."""
    cutoff = pd.Timestamp(cutoff_date)
    train = daily_df[daily_df["date"] <= cutoff].copy()
    test = daily_df[
        (daily_df["date"] > cutoff)
        & (daily_df["date"] <= cutoff + pd.Timedelta(days=FORECAST_DAYS))
    ].copy()
    if len(train) < MIN_TRAIN_DAYS:
        raise ValueError(
            f"Not enough training data before {cutoff.date()}: "
            f"{len(train)} days (need at least {MIN_TRAIN_DAYS})."
        )
    return train, test, cutoff


def _fit_prophet(train: pd.DataFrame, y_col: str, clip_at_zero: bool = True) -> pd.DataFrame:
    """Train Prophet on `train` (columns date, y_col) and predict FORECAST_DAYS ahead.

    Returns a frame with ds, yhat, yhat_lower, yhat_upper. Values are clipped
    at zero because counts and durations cannot be negative.
    """
    prophet_df = train.rename(columns={"date": "ds", y_col: "y"})
    model = Prophet(
        yearly_seasonality=False,
        weekly_seasonality=True,
        changepoint_prior_scale=1,
        daily_seasonality=False,
    )
    model.add_seasonality(
        name="yearly",
        period=365.25,
        fourier_order=25,
        prior_scale=40,
    )

    model.add_country_holidays("UA")
    model.fit(prophet_df)
    future = model.make_future_dataframe(periods=FORECAST_DAYS, freq="D")
    forecast = model.predict(future)
    prediction = (
        forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(FORECAST_DAYS).copy()
    )
    if clip_at_zero:
        cols = ["yhat", "yhat_lower", "yhat_upper"]
        prediction[cols] = prediction[cols].clip(lower=0)
    return prediction


def run_forecast(df: pd.DataFrame, cutoff_date: str | pd.Timestamp) -> dict:
    """
    Forecast daily alert count.
    Returns {history, prediction, actual} with 'alert_count' as the value column.
    """
    daily_df = _prepare_daily(df)
    train, test, _ = _train_test(daily_df, cutoff_date)
    prediction = _fit_prophet(train, "alert_count")
    return {"history": train, "prediction": prediction, "actual": test}


def run_duration_forecast(df: pd.DataFrame, cutoff_date: str | pd.Timestamp) -> dict:
    """
    Forecast average alert duration (seconds) per day.
    Returns {history, prediction, actual} with 'avg_duration_s' as the value column.
    """
    daily_dur = _prepare_daily_duration(df)
    train, test, _ = _train_test(daily_dur, cutoff_date)
    prediction = _fit_prophet(train, "avg_duration_s")
    return {"history": train, "prediction": prediction, "actual": test}


def holdout_metrics(result: dict, value_col: str) -> dict | None:
    """Compare a forecast with the real values after the cutoff.

    Returns MAE, MAPE (days with an actual value of 0 are skipped) and the MAE
    of a naive baseline (mean of the last FORECAST_DAYS training days), plus
    the number of compared days. None if there are no actual days to compare.
    """
    merged = result["prediction"].merge(
        result["actual"], left_on="ds", right_on="date", how="inner"
    )
    if merged.empty:
        return None
    err = (merged["yhat"] - merged[value_col]).abs()
    nonzero = merged[value_col] != 0
    naive = result["history"][value_col].tail(FORECAST_DAYS).mean()
    return {
        "days": int(len(merged)),
        "mae": float(err.mean()),
        "mape_pct": float((err[nonzero] / merged.loc[nonzero, value_col]).mean() * 100),
        "naive_mae": float((naive - merged[value_col]).abs().mean()),
    }


def backtest(
    df: pd.DataFrame, value_col: str = "alert_count", n_windows: int = 6, step_days: int = 30
) -> pd.DataFrame:
    """Evaluate the forecast on `n_windows` holdout windows ending at DEFAULT_CUTOFF_DATE.

    Window i uses the cutoff DEFAULT_CUTOFF_DATE - i * step_days. One row per window.
    """
    func = run_forecast if value_col == "alert_count" else run_duration_forecast
    last = pd.Timestamp(DEFAULT_CUTOFF_DATE)
    rows = []
    for i in range(n_windows):
        cutoff = last - pd.Timedelta(days=i * step_days)
        metrics = holdout_metrics(func(df, cutoff), value_col)
        if metrics:
            rows.append({"cutoff": cutoff.date(), **metrics})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = load_and_prepare()
    for name, func, col in [
        ("Count", run_forecast, "alert_count"),
        ("Duration", run_duration_forecast, "avg_duration_s"),
    ]:
        result = func(df, DEFAULT_CUTOFF_DATE)
        print(f"\n=== {name} Forecast (cutoff {DEFAULT_CUTOFF_DATE}) ===")
        print(f"Training data: {len(result['history'])} days")
        pred = result["prediction"].copy()
        pred["ds"] = pred["ds"].dt.date
        pred[["yhat", "yhat_lower", "yhat_upper"]] = (
            pred[["yhat", "yhat_lower", "yhat_upper"]].round(0).astype(int)
        )
        print(pred.to_string(index=False))
        print("Actual data:")
        if len(result["actual"]) > 0:
            print(result["actual"].to_string(index=False))
        else:
            print("(none)")
        m = holdout_metrics(result, col)
        if m:
            print(
                f"Holdout ({m['days']} days): MAE={m['mae']:.1f}, "
                f"MAPE={m['mape_pct']:.1f}%, naive baseline MAE={m['naive_mae']:.1f}"
            )
        bt = backtest(df, col)
        print(f"\nBacktest, {len(bt)} windows of {FORECAST_DAYS} days:")
        print(bt.round(1).to_string(index=False))
        print(
            f"Mean: MAE={bt['mae'].mean():.1f}, MAPE={bt['mape_pct'].mean():.1f}%, "
            f"naive baseline MAE={bt['naive_mae'].mean():.1f}"
        )
