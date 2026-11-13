"""Static page layout: header, stat cards, key insights and the five tabs."""

import pandas as pd
from dash import dcc, html

from src.analysis import key_insights, to_local
from src.config import (
    COL_STARTED,
    DEFAULT_CUTOFF_DATE,
    FORECAST_DAYS,
    LOCAL_TZ,
    MIN_TRAIN_DAYS,
    RELIABLE_UNTIL,
)
from dashboard import figures as figs
from dashboard.theme import (
    CARD_SHADOW,
    CFG,
    NOTE_STYLE,
    TAB_SELECTED_STYLE,
    TAB_STYLE,
    card,
    format_date,
    simple_table,
)


def _stat_card(label: str, value: str, font_size: str = "28px") -> html.Div:
    return html.Div(
        [
            html.H4(label, style={"margin": "0 0 5px 0", "color": "#666"}),
            html.Span(
                value,
                style={
                    "fontSize": font_size,
                    "fontWeight": "bold",
                    "color": CFG["accent"],
                },
            ),
        ],
        style={
            "textAlign": "center",
            "padding": "15px",
            "backgroundColor": CFG["card_bg"],
            "borderRadius": "8px",
            "boxShadow": CARD_SHADOW,
            "flex": "1",
        },
    )


def _stat_cards(df: pd.DataFrame, results: dict) -> html.Div:
    local = to_local(df[COL_STARTED])
    n_regions = df["oblast"].nunique()
    if "Kyiv City" in set(df["oblast"]):
        regions = f"{n_regions - 1} oblasts + Kyiv city"
    else:
        regions = f"{n_regions} oblasts"
    return html.Div(
        [
            _stat_card("Total Alerts", f"{len(df):,}"),
            _stat_card(
                "Avg Duration", f"{results['duration_stats']['mean_s'] / 60:.0f} min"
            ),
            _stat_card(
                "Date Range",
                f"{local.min():%b %Y} - {local.max():%b %Y}",
                font_size="20px",
            ),
            _stat_card("Regions", regions),
        ],
        style={"display": "flex", "gap": "15px", "marginBottom": "20px"},
    )


def _insights_card(df: pd.DataFrame, results: dict) -> html.Div:
    return html.Div(
        [
            html.H3(
                "Key Insights",
                style={
                    "color": CFG["accent"],
                    "marginTop": 0,
                    "marginBottom": "10px",
                },
            ),
            html.Ul(
                [html.Li(text) for text in key_insights(df, results)],
                style={"lineHeight": "1.8", "paddingLeft": "20px", "marginBottom": 0},
            ),
        ],
        style={
            "backgroundColor": CFG["card_bg"],
            "padding": "15px 20px",
            "borderRadius": "8px",
            "boxShadow": CARD_SHADOW,
            "marginBottom": "20px",
        },
    )


def _top_days_table(results: dict) -> html.Table:
    data = results["top_days"].head(CFG["top_days_count"])
    rows = [
        [format_date(row["date"]), f"{int(row['alert_count']):,}"]
        for _, row in data.iterrows()
    ]
    return simple_table(["Date", "Alerts"], rows, right_align_from=1)


def _note(text: str) -> html.Div:
    return html.Div([html.P(text, style=NOTE_STYLE)], style={"padding": "0 8px"})


def _tab(label: str, children: list) -> dcc.Tab:
    return dcc.Tab(
        label=label,
        style=TAB_STYLE,
        selected_style=TAB_SELECTED_STYLE,
        children=children,
    )


def _forecast_tab(df: pd.DataFrame) -> dcc.Tab:
    first_cutoff = (
        df[COL_STARTED].min().tz_localize(None) + pd.Timedelta(days=MIN_TRAIN_DAYS)
    )
    disclaimer = html.Div(
        html.P(
            "This is just a statistical prediction. It cannot predict military plans, "
            "political decisions or real-world intentions: even if the war ended "
            "tomorrow, a model trained on past alerts would still forecast alerts. "
            "It is just history and statistics, nothing more.",
            style={"margin": 0, "fontSize": "18px", "lineHeight": "1.4"},
        ),
        style={
            "backgroundColor": "#fff3cd",
            "color": "#856404",
            "borderLeft": "4px solid #ffc107",
            "padding": "12px",
            "borderRadius": "4px",
            "marginTop": "10px",
            "marginBottom": "10px",
        },
    )
    settings = html.Div(
        [
            html.P(
                "Select training cutoff date:",
                style={"marginBottom": "10px", "fontWeight": "bold"},
            ),
            dcc.DatePickerSingle(
                id="cutoff-date-picker",
                min_date_allowed=first_cutoff.strftime("%Y-%m-%d"),
                max_date_allowed=DEFAULT_CUTOFF_DATE,
                initial_visible_month=pd.Timestamp(DEFAULT_CUTOFF_DATE),
                date=DEFAULT_CUTOFF_DATE,
                display_format="DD-MM-YYYY",
                style={"marginBottom": "15px"},
            ),
            html.P(
                f"Cutoffs are limited to {first_cutoff:%d-%m-%Y} - "
                f"{pd.Timestamp(DEFAULT_CUTOFF_DATE):%d-%m-%Y}: at least "
                f"{MIN_TRAIN_DAYS} days of training data, and the {FORECAST_DAYS}-day "
                f"comparison window must end by {RELIABLE_UNTIL:%d-%m-%Y}, before "
                "oblast-level data becomes sparse.",
                style={"color": "#666", "fontSize": "13px", "margin": "0 0 10px 0"},
            ),
            html.Div(
                id="forecast-status",
                style={"color": "#666", "fontSize": "14px", "marginBottom": "10px"},
            ),
        ]
    )
    return _tab(
        "Forecast",
        [
            card(disclaimer, title="Important Notice"),
            card(settings, title="Prophet Model Settings"),
            card(
                dcc.Graph(id="forecast-graph"),
                title=f"Daily Alert Forecast ({FORECAST_DAYS} days)",
            ),
            card(
                html.Div(id="forecast-table"),
                title=f"Predicted vs Actual: Alert Count (Next {FORECAST_DAYS} Days)",
            ),
            card(
                dcc.Graph(id="forecast-duration-graph"),
                title=f"Daily Average Duration Forecast ({FORECAST_DAYS} days)",
            ),
            card(
                html.Div(id="forecast-duration-table"),
                title=f"Predicted vs Actual: Avg Duration in seconds (Next {FORECAST_DAYS} Days)",
            ),
        ],
    )


def build_layout(df: pd.DataFrame, results: dict) -> html.Div:
    """Assemble the whole page from the cleaned data and analysis results."""
    max_h = CFG["histogram_max_minutes"] // 60
    tabs = dcc.Tabs(
        style={"marginBottom": "20px"},
        children=[
            _tab(
                "Overview",
                [
                    card(
                        dcc.Graph(figure=figs.fig_oblasts(results["by_oblast"])),
                        title="Regional Breakdown",
                    ),
                    card(
                        dcc.Graph(figure=figs.fig_daily_trend(df)),
                        title="Trends Over Time",
                    ),
                    _note(
                        f"Note: after about {RELIABLE_UNTIL:%B %Y} the source switched to "
                        "mostly raion- and hromada-level alerts, so oblast-level "
                        "records become very sparse and the trend drops sharply. "
                        "That is a data artifact, not a real change."
                    ),
                ],
            ),
            _tab(
                "Hourly Patterns",
                [
                    card(
                        dcc.Graph(figure=figs.fig_hourly(results["by_hour"])),
                        title="Alert Frequency by Hour (Kyiv time)",
                    ),
                    card(
                        dcc.Graph(
                            figure=figs.fig_duration_by_hour(results["duration_by_hour"])
                        ),
                        title="Duration by Start Hour (Kyiv time)",
                    ),
                    card(
                        _top_days_table(results),
                        title=f"Top {CFG['top_days_count']} Busiest Days (Kyiv dates)",
                    ),
                ],
            ),
            _tab(
                "Weekly & Monthly",
                [
                    card(
                        dcc.Graph(figure=figs.fig_heatmap(df)),
                        title="Alert Density: Day x Hour (Kyiv time)",
                    ),
                    card(
                        dcc.Graph(figure=figs.fig_dayofweek(results["by_dayofweek"])),
                        title="By Day of Week",
                    ),
                    card(
                        dcc.Graph(figure=figs.fig_monthly(results["by_month"])),
                        title="By Month (All Years)",
                    ),
                    card(dcc.Graph(figure=figs.fig_season(results["by_season"]))),
                    card(dcc.Graph(figure=figs.fig_day_night(results["by_timeofday"]))),
                ],
            ),
            _tab(
                "Duration Analysis",
                [
                    card(
                        dcc.Graph(
                            figure=figs.fig_duration_oblast(results["duration_by_oblast"])
                        ),
                        title="Avg Duration by Oblast",
                    ),
                    card(
                        dcc.Graph(figure=figs.fig_duration_hist(df)),
                        title=f"Duration Distribution (<={max_h}h)",
                    ),
                ],
            ),
            _forecast_tab(df),
        ],
    )
    return html.Div(
        style={
            "backgroundColor": CFG["bg"],
            "minHeight": "100vh",
            "padding": "20px",
            "fontFamily": "Segoe UI, sans-serif",
        },
        children=[
            html.H1("AlerticUA", style={"color": CFG["text"], "marginBottom": "5px"}),
            html.P(
                "Interactive analysis of air raid alert patterns across Ukrainian "
                "oblasts. Only oblast-level alerts are counted. Hours, weekdays and "
                f"day/night use local time ({LOCAL_TZ}).",
                style={"color": "#666", "marginTop": "0", "marginBottom": "20px"},
            ),
            _stat_cards(df, results),
            _insights_card(df, results),
            tabs,
            html.Hr(),
            html.P(
                "Data source: github.com/Vadimkin/ukrainian-air-raid-sirens-dataset (MIT)",
                style={"textAlign": "center", "color": "#999", "fontSize": "14px"},
            ),
        ],
    )
