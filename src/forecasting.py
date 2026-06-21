import pandas as pd
from prophet import Prophet

from src.analysis import alerts_by_date
from src.data_loader import load_and_prepare


def run_forecast_alert_count_next_days(df, forecast_days, cutoff_date="2025-10-31"):
    print(f"\n--- FORECASTING (Prophet) until {cutoff_date} + {forecast_days} days ---")

    daily_df = alerts_by_date(df)
    daily_df["date"] = pd.to_datetime(daily_df["date"])
    filtered_df = daily_df[daily_df["date"] <= cutoff_date].copy()

    print(f"Data for training: {len(filtered_df)} days")

    prophet_df = filtered_df.rename(columns={"date": "ds", "alert_count": "y"})
    model = Prophet(yearly_seasonality=True, weekly_seasonality=True)
    model.fit(prophet_df)

    future = model.make_future_dataframe(periods=forecast_days, freq="D")
    forecast = model.predict(future)

    predictions = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(
        forecast_days
    )

    print(f"\nForecast for {forecast_days} next days:")
    predictions_formatted = predictions.copy()
    predictions_formatted["ds"] = predictions_formatted["ds"].dt.date
    predictions_formatted["yhat"] = predictions_formatted["yhat"].round(0).astype(int)
    predictions_formatted["yhat_lower"] = (
        predictions_formatted["yhat_lower"].round(0).astype(int)
    )
    predictions_formatted["yhat_upper"] = (
        predictions_formatted["yhat_upper"].round(0).astype(int)
    )

    print(predictions_formatted.to_string(index=False))

    return forecast


if __name__ == "__main__":
    df = load_and_prepare()
    cutoff_date = "2025-09-30"
    forecast_days = 14

    run_forecast_alert_count_next_days(
        df, forecast_days=forecast_days, cutoff_date=cutoff_date
    )

    daily_df = alerts_by_date(df)
    daily_df["date"] = pd.to_datetime(daily_df["date"])

    print(f"\n--- REAL DATA (Next {forecast_days} Days after {cutoff_date}) ---")
    real_future_days = daily_df[daily_df["date"] > cutoff_date].head(forecast_days)
    print(real_future_days.to_string(index=False))
