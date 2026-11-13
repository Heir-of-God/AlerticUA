"""
Forecasting module using Facebook Prophet.
Predicts daily alert counts / avg duration and compares with actual data.
"""

import pandas as pd
from prophet import Prophet

from src.analysis import alerts_by_date, to_local
from src.data_loader import load_and_prepare
from src.config import COL_DURATION, COL_STARTED

FORECAST_DAYS = 14


def _prepare_daily(df):
    """Get daily alert count DataFrame."""
    daily = alerts_by_date(df)
    daily["date"] = pd.to_datetime(daily["date"])
    daily = daily.sort_values("date").reset_index(drop=True)
    return daily


def _train_test(daily_df, cutoff_date):
    """Split daily data into train (<=cutoff) and test (next FORECAST_DAYS)."""
    cutoff = pd.Timestamp(cutoff_date)
    train = daily_df[daily_df["date"] <= cutoff].copy()
    test = daily_df[
        (daily_df["date"] > cutoff)
        & (daily_df["date"] <= cutoff + pd.Timedelta(days=FORECAST_DAYS))
    ].copy()
    return train, test, cutoff


def _fit_prophet(train, y_col):
    """Train Prophet on train data with column y_col as target."""
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
    return prediction


def run_forecast(df, cutoff_date):
    """
    Forecast daily alert count.
    Returns {history, prediction, actual} with 'alert_count' as the value column.
    """
    daily_df = _prepare_daily(df)
    train, test, _ = _train_test(daily_df, cutoff_date)
    prediction = _fit_prophet(train, "alert_count")
    return {"history": train, "prediction": prediction, "actual": test}


def run_duration_forecast(df, cutoff_date):
    """
    Forecast average alert duration (seconds) per day.
    Returns {history, prediction, actual} with 'avg_duration_s' as the value column.
    """
    df = df.copy()
    day = to_local(df[COL_STARTED]).dt.tz_localize(None).dt.normalize()
    daily_dur = (
        df.groupby(day, observed=True)[COL_DURATION]
        .mean()
        .reset_index()
        .rename(columns={COL_STARTED: "date", COL_DURATION: "avg_duration_s"})
    )
    daily_dur["date"] = pd.to_datetime(daily_dur["date"])
    daily_dur = daily_dur.sort_values("date").reset_index(drop=True)

    train, test, _ = _train_test(daily_dur, cutoff_date)
    prediction = _fit_prophet(train, "avg_duration_s")
    return {"history": train, "prediction": prediction, "actual": test}


if __name__ == "__main__":
    df = load_and_prepare()
    for name, func in [("Count", run_forecast), ("Duration", run_duration_forecast)]:
        result = func(df, "2025-09-30")
        print(f"\n=== {name} Forecast ===")
        print(f"Training data: {len(result['history'])} days")
        pred = result["prediction"].copy()
        pred["ds"] = pred["ds"].dt.date
        pred["yhat"] = pred["yhat"].round(0).astype(int)
        print(pred.to_string(index=False))
        print(f"Actual data:")
        if len(result["actual"]) > 0:
            print(result["actual"].to_string(index=False))
        else:
            print("(none)")
