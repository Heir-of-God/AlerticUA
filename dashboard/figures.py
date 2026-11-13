"""Plotly figure builders. Each takes prepared data and returns a figure."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.analysis import alerts_by_date, alerts_by_dayofweek_hour, hour_label
from src.config import COL_DURATION, FORECAST_DAYS
from dashboard.theme import CFG, format_date

TZ_NOTE = "Kyiv time"


def _style(fig: go.Figure, height: int | None = None, plot_bg: bool = True) -> go.Figure:
    """Apply the shared height and background."""
    layout = {"height": height or CFG["chart_height"]}
    if plot_bg:
        layout["plot_bgcolor"] = CFG["plot_bg"]
    return fig.update_layout(**layout)


def fig_oblasts(by_oblast: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart of alert counts per oblast."""
    fig = px.bar(
        by_oblast,
        x="alert_count",
        y="oblast",
        orientation="h",
        title="All Oblasts by Alert Count",
        labels={"alert_count": "Alerts", "oblast": ""},
        color="alert_count",
        color_continuous_scale=CFG["bar_scale"],
        text="alert_count",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    return _style(fig, CFG["oblast_height"])


def fig_daily_trend(df: pd.DataFrame) -> go.Figure:
    """Daily alert counts with a rolling average."""
    daily = alerts_by_date(df)
    daily["rolling_avg"] = daily["alert_count"].rolling(CFG["rolling_window"]).mean()
    daily["date_fmt"] = daily["date"].apply(format_date)
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=daily["date"],
            y=daily["alert_count"],
            mode="markers",
            marker=dict(size=2, color="rgba(200,50,50,0.3)"),
            name="Daily",
            hovertemplate="%{customdata}<br>Alerts: %{y}<extra></extra>",
            customdata=daily["date_fmt"],
        )
    )
    fig.add_trace(
        go.Scatter(
            x=daily["date"],
            y=daily["rolling_avg"],
            mode="lines",
            line=dict(color="red", width=2),
            name=f"{CFG['rolling_window']}-day avg",
            hovertemplate="%{customdata}<br>Avg: %{y:.1f}<extra></extra>",
            customdata=daily["date_fmt"],
        )
    )
    fig.update_layout(
        title="Daily Alerts Over Time",
        xaxis_title="Date",
        yaxis_title="Alerts",
        hovermode="x unified",
    )
    return _style(fig, CFG["daily_height"])


def fig_hourly(by_hour: pd.DataFrame) -> go.Figure:
    """Alert count per start hour."""
    fig = px.bar(
        by_hour,
        x="hour_label",
        y="alert_count",
        title=f"Alerts by Hour Interval ({TZ_NOTE})",
        labels={"hour_label": "", "alert_count": "Alerts"},
        color="alert_count",
        color_continuous_scale=CFG["bar_scale"],
    )
    fig.update_layout(
        xaxis={"categoryorder": "array", "categoryarray": by_hour["hour_label"]}
    )
    return _style(fig)


def fig_duration_by_hour(duration_by_hour: pd.DataFrame) -> go.Figure:
    """Average duration per start hour (bars sorted by duration)."""
    data = duration_by_hour.copy()
    data["avg_duration_min"] = data["avg_duration_s"] / 60
    fig = px.bar(
        data,
        x="interval",
        y="avg_duration_min",
        title=f"Avg Alert Duration by Start Hour ({TZ_NOTE})",
        labels={"interval": "", "avg_duration_min": "Avg Duration (minutes)"},
        color="avg_duration_min",
        color_continuous_scale=CFG["bar_duration_scale"],
        text=data["avg_duration_min"].apply(lambda s: f"{s:.0f}m"),
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        xaxis={"categoryorder": "array", "categoryarray": data["interval"]}
    )
    return _style(fig)


def fig_season(by_season: pd.DataFrame) -> go.Figure:
    """Donut chart of alerts by season."""
    fig = px.pie(
        by_season,
        values="alert_count",
        names="season",
        title="Alerts by Season",
        color="season",
        color_discrete_map=CFG["season_colors"],
        hole=CFG["pie_hole"],
    )
    fig.update_traces(textinfo="percent+label")
    return fig


def fig_day_night(by_timeofday: pd.DataFrame) -> go.Figure:
    """Donut chart of day vs night alerts."""
    fig = px.pie(
        by_timeofday,
        values="alert_count",
        names="time_of_day",
        title=f"Day vs Night ({TZ_NOTE})",
        color="time_of_day",
        color_discrete_map=CFG["day_night_colors"],
        hole=CFG["pie_hole"],
    )
    fig.update_traces(textinfo="percent+label")
    return fig


def fig_duration_hist(df: pd.DataFrame) -> go.Figure:
    """Histogram of durations up to histogram_max_minutes with mean/median lines."""
    max_min = CFG["histogram_max_minutes"]
    dur_min = df[COL_DURATION] / 60
    dur_min = dur_min[dur_min <= max_min]
    fig = px.histogram(
        dur_min,
        nbins=CFG["histogram_nbins"],
        title=f"Alert Duration Distribution (<={max_min // 60}h, excl. outliers)",
        labels={"value": "Duration (minutes)", "count": "Alerts"},
        color_discrete_sequence=[CFG["accent"]],
    )
    fig.update_layout(bargap=0.02)
    mean_val, median_val = dur_min.mean(), dur_min.median()
    fig.add_vline(
        x=mean_val,
        line_dash="dash",
        line_color="blue",
        annotation_text=f"Mean: {mean_val:.0f}m",
    )
    fig.add_vline(
        x=median_val,
        line_dash="dot",
        line_color="green",
        annotation_text=f"Median: {median_val:.0f}m",
    )
    return _style(fig)


def fig_heatmap(df: pd.DataFrame) -> go.Figure:
    """Heatmap: day of week x hour interval, colored by alert count."""
    labels = CFG["day_names"]
    cells = alerts_by_dayofweek_hour(df)
    cells["day_label"] = cells["dayofweek"].map(lambda i: labels[i])
    cells["hour_label"] = cells["hour"].map(hour_label)
    fig = px.density_heatmap(
        cells,
        x="day_label",
        y="hour_label",
        z="alert_count",
        title=f"Alert Density: Day of Week x Hour ({TZ_NOTE})",
        labels={"day_label": "", "hour_label": "", "alert_count": "Alerts"},
        color_continuous_scale="Reds",
        nbinsx=7,
        nbinsy=24,
    )
    fig.update_layout(
        xaxis={"categoryorder": "array", "categoryarray": labels},
        yaxis={
            "categoryorder": "array",
            "categoryarray": [hour_label(h) for h in range(23, -1, -1)],
        },
    )
    return _style(fig, 600)


def fig_dayofweek(by_dayofweek: pd.DataFrame) -> go.Figure:
    """Bar chart of alerts by weekday."""
    labels = CFG["day_names"]
    data = by_dayofweek.copy()
    data["day_label"] = data["dayofweek"].map(lambda i: labels[i])
    fig = px.bar(
        data,
        x="day_label",
        y="alert_count",
        title=f"Alerts by Day of Week ({TZ_NOTE})",
        labels={"day_label": "", "alert_count": "Alerts"},
        color="alert_count",
        color_continuous_scale=CFG["bar_scale"],
    )
    fig.update_layout(xaxis={"categoryorder": "array", "categoryarray": labels})
    return _style(fig)


def fig_monthly(by_month: pd.DataFrame) -> go.Figure:
    """Bar chart of alerts by calendar month (all years combined)."""
    labels = CFG["month_names"]
    data = by_month.copy()
    data["month_label"] = data["month"].map(lambda i: labels[i - 1])
    fig = px.bar(
        data,
        x="month_label",
        y="alert_count",
        title=f"Alerts by Month, All Years ({TZ_NOTE})",
        labels={"month_label": "", "alert_count": "Alerts"},
        color="alert_count",
        color_continuous_scale=CFG["bar_scale"],
    )
    fig.update_layout(xaxis={"categoryorder": "array", "categoryarray": labels})
    return _style(fig)


def fig_duration_oblast(duration_by_oblast: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart of average duration per oblast."""
    data = duration_by_oblast.copy()
    data["avg_duration_min"] = data["avg_duration_s"] / 60
    fig = px.bar(
        data,
        x="avg_duration_min",
        y="oblast",
        orientation="h",
        title="All Oblasts by Avg Alert Duration",
        labels={"avg_duration_min": "Avg Duration (minutes)", "oblast": ""},
        color="avg_duration_min",
        color_continuous_scale=CFG["bar_duration_scale"],
        text=data["avg_duration_min"].apply(lambda s: f"{s:.0f}m"),
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    return _style(fig, CFG["oblast_height"])


def fig_forecast(
    history: pd.DataFrame,
    pred: pd.DataFrame,
    actual: pd.DataFrame,
    value_col: str,
    cutoff: pd.Timestamp,
    ylabel: str,
) -> go.Figure:
    """Training data, forecast with interval and (if available) the actual values."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=history["date"],
            y=history[value_col],
            mode="lines",
            line=dict(color="red", width=1.5),
            name="Training data",
            hovertemplate="%{x|%d-%m-%Y}<br>%{y}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=pd.concat([pred["ds"], pred["ds"][::-1]]),
            y=pd.concat([pred["yhat_upper"], pred["yhat_lower"][::-1]]),
            fill="toself",
            fillcolor="rgba(68, 100, 255, 0.2)",
            line=dict(color="rgba(255,255,255,0)"),
            name="Confidence interval",
            showlegend=True,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=pred["ds"],
            y=pred["yhat"],
            mode="lines+markers",
            line=dict(color="blue", width=2),
            marker=dict(size=6),
            name="Prediction",
            hovertemplate="%{x|%d-%m-%Y}<br>Predicted: %{y:.0f}<extra></extra>",
        )
    )
    af = actual[actual["date"] > cutoff].head(FORECAST_DAYS)
    if len(af) > 0:
        fig.add_trace(
            go.Scatter(
                x=af["date"],
                y=af[value_col],
                mode="lines+markers",
                line=dict(color="green", width=2, dash="dash"),
                marker=dict(size=6),
                name="Actual",
                hovertemplate="%{x|%d-%m-%Y}<br>Actual: %{y}<extra></extra>",
            )
        )
    fig.add_vline(
        x=cutoff,
        line_dash="dot",
        line_color="gray",
        annotation_text=f"Cutoff: {cutoff.strftime('%d-%m-%Y')}",
    )
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title=ylabel,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return _style(fig, 500)
