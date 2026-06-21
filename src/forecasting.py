"""
Forecasting module using Facebook Prophet.
Predicts daily alert counts and compares with actual data.
"""

import pandas as pd
from prophet import Prophet

from src.analysis import alerts_by_date
from src.data_loader import load_and_prepare

FORECAST_DAYS = 14


def run_forecast(df, cutoff_date):
    """
    Train Prophet on data up to cutoff_date, predict next FORECAST_DAYS.
    Returns dict with:
      - history: DataFrame (date, alert_count) for training period
      - prediction: DataFrame (ds, yhat, yhat_lower, yhat_upper) for forecast period
      - actual: DataFrame (date, alert_count) for the same forecast period (if exists)
    """
    daily_df = alerts_by_date(df)
    daily_df["date"] = pd.to_datetime(daily_df["date"])
    daily_df = daily_df.sort_values("date").reset_index(drop=True)

    cutoff = pd.Timestamp(cutoff_date)
    train = daily_df[daily_df["date"] <= cutoff].copy()
    test = daily_df[
        (daily_df["date"] > cutoff)
        & (daily_df["date"] <= cutoff + pd.Timedelta(days=FORECAST_DAYS))
    ].copy()

    # Train Prophet
    prophet_df = train.rename(columns={"date": "ds", "alert_count": "y"})
    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        changepoint_prior_scale=0.1,
        daily_seasonality=False,
    )

    model.add_country_holidays("UA")
    model.fit(prophet_df)

    # Predict
    future = model.make_future_dataframe(periods=FORECAST_DAYS, freq="D")
    forecast = model.predict(future)
    prediction = (
        forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(FORECAST_DAYS).copy()
    )

    return {
        "history": train,
        "prediction": prediction,
        "actual": test,
        "model": model,
    }


if __name__ == "__main__":
    df = load_and_prepare()
    result = run_forecast(df, "2025-09-30")

    print(f"Training data: {len(result['history'])} days")
    print(f"\nPrediction for next {FORECAST_DAYS} days:")
    pred = result["prediction"].copy()
    pred["ds"] = pred["ds"].dt.date
    pred["yhat"] = pred["yhat"].round(0).astype(int)
    print(pred.to_string(index=False))

    print(f"\nActual data for same period:")
    if len(result["actual"]) > 0:
        print(result["actual"].to_string(index=False))
    else:
        print("(no actual data available yet)")
