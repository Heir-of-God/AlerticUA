"""Forecast tab callback."""

import pandas as pd
import plotly.graph_objects as go
from dash import Dash, Input, Output, html

from src.config import FORECAST_DAYS
from src.forecasting import holdout_metrics, run_duration_forecast, run_forecast
from dashboard import figures as figs
from dashboard.theme import simple_table


def _forecast_table(result: dict, value_col: str) -> html.Table:
    """Predicted value, interval and (if known) actual value for each forecast day."""
    table = result["prediction"].merge(
        result["actual"], left_on="ds", right_on="date", how="left"
    )
    rows = []
    for _, r in table.iterrows():
        actual = "-" if pd.isna(r[value_col]) else f"{r[value_col]:,.0f}"
        rows.append(
            [
                r["ds"].strftime("%d-%m-%Y"),
                f"{r['yhat']:.0f}",
                f"{r['yhat_lower']:.0f}",
                f"{r['yhat_upper']:.0f}",
                actual,
            ]
        )
    return simple_table(["Date", "Predicted", "Lower", "Upper", "Actual"], rows)


def _metrics_text(result: dict, value_col: str, unit: str) -> str:
    m = holdout_metrics(result, value_col)
    if m is None:
        return "no actual data after the cutoff to compare with"
    return (
        f"over {m['days']} days MAE {m['mae']:,.0f}{unit}, MAPE {m['mape_pct']:.0f}% "
        f"(naive baseline MAE {m['naive_mae']:,.0f}{unit})"
    )


def register_callbacks(app: Dash, df: pd.DataFrame) -> None:
    """Attach the forecast callback to `app`, using the cleaned data `df`."""

    @app.callback(
        [
            Output("forecast-graph", "figure"),
            Output("forecast-table", "children"),
            Output("forecast-status", "children"),
            Output("forecast-duration-graph", "figure"),
            Output("forecast-duration-table", "children"),
        ],
        Input("cutoff-date-picker", "date"),
    )
    def update_forecast(cutoff_date: str | None):
        if not cutoff_date:
            msg = html.P("Select a date above.")
            return go.Figure(), msg, "", go.Figure(), msg
        cutoff = pd.Timestamp(cutoff_date)
        start = cutoff + pd.Timedelta(days=1)
        try:
            r1 = run_forecast(df, cutoff)
        except ValueError as e:
            err = html.P(f"Cannot forecast: {e}")
            return go.Figure(), err, "", go.Figure(), err

        fig1 = figs.fig_forecast(
            r1["history"], r1["prediction"], r1["actual"], "alert_count", cutoff,
            "Number of Alerts",
        )  # fmt: skip
        status = (
            f"Count: trained on {len(r1['history'])} days, predicting {FORECAST_DAYS} "
            f"days from {start:%d-%m-%Y}; {_metrics_text(r1, 'alert_count', '')}."
        )
        table1 = _forecast_table(r1, "alert_count")
        try:
            r2 = run_duration_forecast(df, cutoff)
        except ValueError as e:
            return fig1, table1, status, go.Figure(), html.P(f"Cannot forecast: {e}")
        fig2 = figs.fig_forecast(
            r2["history"], r2["prediction"], r2["actual"], "avg_duration_s", cutoff,
            "Avg Duration (seconds)",
        )  # fmt: skip
        status += f" Duration: {_metrics_text(r2, 'avg_duration_s', ' s')}."
        return fig1, table1, status, fig2, _forecast_table(r2, "avg_duration_s")
