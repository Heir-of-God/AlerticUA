"""
Dash web dashboard for AlerticUA.
Run with: python app.py
"""

import dash
from dash import dcc, html
import plotly.express as px
import plotly.graph_objects as go

from src.data_loader import load_and_prepare
from src.analysis import run_analysis, alerts_by_date
from src.config import COL_STARTED, COL_DURATION

CONFIG = {
    # Colors
    "bg": "#f8faf9",
    "card_bg": "white",
    "plot_bg": "#f6f6f6",
    "text": "#2c3e50",
    "accent": "#c0392b",
    "bar_scale": "Reds",
    "bar_duration_scale": "Blues",
    "season_colors": {
        "Winter": "#a8d8ea",
        "Spring": "#7bc47f",
        "Summer": "#f7d44a",
        "Autumn": "#e89b4a",
    },
    "day_night_colors": {"Day": "#f5a623", "Night": "#2c3e50"},
    # Chart sizes
    "oblast_height": 700,
    "daily_height": 450,
    "chart_height": 400,
    "pie_hole": 0.3,
    # Duration limits
    "histogram_max_minutes": 600,
    "histogram_nbins": 60,
    # Time series
    "rolling_window": 7,
    # Date format
    "date_format": "%d-%m-%Y",
    # Tables
    "top_days_count": 10,
    # Day names
    "day_names": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    "month_names": [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ],
}

CFG = CONFIG

tab_style = {
    "borderBottom": "1px solid #d6d6d6",
    "padding": "12px",
    "fontWeight": "bold",
    "color": "#666",
    "backgroundColor": CFG["bg"],
    "borderTop": "none",
    "borderLeft": "none",
    "borderRight": "none",
}

tab_selected_style = {
    "borderTop": f"3px solid {CFG['accent']}",
    "borderBottom": "1px solid white",
    "backgroundColor": "white",
    "color": CFG["accent"],
    "padding": "12px",
    "fontWeight": "bold",
}

# ── Load data ──────────────────────────────────────────────────────────────
df = load_and_prepare()
results = run_analysis(df)

ANALYSIS_KEYS = list(results.keys())


# ── Helpers ────────────────────────────────────────────────────────────────
def card(children, title=None):
    items = []
    if title:
        items.append(html.H3(title, style={"marginTop": 0, "color": CFG["accent"]}))
    items.append(children)
    return html.Div(
        items,
        style={
            "backgroundColor": CFG["card_bg"],
            "padding": "20px",
            "borderRadius": "8px",
            "boxShadow": "0 2px 8px rgba(0,0,0,0.1)",
            "marginBottom": "20px",
        },
    )


def format_date(d):
    return d.strftime(CFG["date_format"]) if hasattr(d, "strftime") else str(d)


# ── Chart functions ────────────────────────────────────────────────────────


def fig_oblasts():
    fig = px.bar(
        results["by_oblast"],
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
    fig.update_layout(
        yaxis={"categoryorder": "total ascending"},
        height=CFG["oblast_height"],
        plot_bgcolor=CFG["plot_bg"],
    )
    return fig


def fig_daily_trend():
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
        height=CFG["daily_height"],
        plot_bgcolor=CFG["plot_bg"],
    )
    return fig


def fig_hourly():
    data = results["by_hour"]
    fig = px.bar(
        data,
        x="hour_label",
        y="alert_count",
        title="Alerts by Hour Interval",
        labels={"hour_label": "", "alert_count": "Alerts"},
        color="alert_count",
        color_continuous_scale=CFG["bar_scale"],
    )
    fig.update_layout(
        xaxis={"categoryorder": "array", "categoryarray": data["hour_label"]},
        height=CFG["chart_height"],
        plot_bgcolor=CFG["plot_bg"],
    )
    return fig


def fig_duration_by_hour():
    data = results["duration_by_hour"].copy()
    data["avg_duration_min"] = data["avg_duration_s"] / 60
    fig = px.bar(
        data,
        x="interval",
        y="avg_duration_min",
        title="Avg Alert Duration by Start Hour",
        labels={"interval": "", "avg_duration_min": "Avg Duration (minutes)"},
        color="avg_duration_min",
        color_continuous_scale=CFG["bar_duration_scale"],
        text=data["avg_duration_min"].apply(lambda s: f"{s:.0f}m"),
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        xaxis={"categoryorder": "array", "categoryarray": data["interval"]},
        height=CFG["chart_height"],
        plot_bgcolor=CFG["plot_bg"],
    )
    return fig


def fig_season():
    fig = px.pie(
        results["by_season"],
        values="alert_count",
        names="season",
        title="Alerts by Season",
        color="season",
        color_discrete_map=CFG["season_colors"],
        hole=CFG["pie_hole"],
    )
    fig.update_traces(textinfo="percent+label")
    return fig


def fig_day_night():
    fig = px.pie(
        results["by_timeofday"],
        values="alert_count",
        names="time_of_day",
        title="Day vs Night",
        color="time_of_day",
        color_discrete_map=CFG["day_night_colors"],
        hole=CFG["pie_hole"],
    )
    fig.update_traces(textinfo="percent+label")
    return fig


def fig_duration_hist():
    dur_min = df[COL_DURATION] / 60
    dur_min = dur_min[dur_min <= CFG["histogram_max_minutes"]]
    fig = px.histogram(
        dur_min,
        nbins=CFG["histogram_nbins"],
        title=f"Alert Duration Distribution (≤{CFG['histogram_max_minutes']//60}h, excl. outliers)",
        labels={"value": "Duration (minutes)", "count": "Alerts"},
        color_discrete_sequence=[CFG["accent"]],
    )
    fig.update_layout(
        bargap=0.02, height=CFG["chart_height"], plot_bgcolor=CFG["plot_bg"]
    )
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
    return fig


def fig_dayofweek():
    data = results["by_dayofweek"]
    labels = CFG["day_names"]
    data["day_label"] = data["dayofweek"].map(lambda i: labels[i])
    fig = px.bar(
        data,
        x="day_label",
        y="alert_count",
        title="Alerts by Day of Week",
        labels={"day_label": "", "alert_count": "Alerts"},
        color="alert_count",
        color_continuous_scale=CFG["bar_scale"],
    )
    fig.update_layout(
        xaxis={"categoryorder": "array", "categoryarray": labels},
        height=CFG["chart_height"],
        plot_bgcolor=CFG["plot_bg"],
    )
    return fig


def fig_monthly():
    data = results["by_month"]
    labels = CFG["month_names"]
    data["month_label"] = data["month"].map(lambda i: labels[i - 1])
    fig = px.bar(
        data,
        x="month_label",
        y="alert_count",
        title="Alerts by Month (All Years)",
        labels={"month_label": "", "alert_count": "Alerts"},
        color="alert_count",
        color_continuous_scale=CFG["bar_scale"],
    )
    fig.update_layout(
        xaxis={"categoryorder": "array", "categoryarray": labels},
        height=CFG["chart_height"],
    )
    return fig


def fig_duration_oblast():
    data = results["duration_by_oblast"].copy()
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
    fig.update_layout(
        yaxis={"categoryorder": "total ascending"},
        height=CFG["oblast_height"],
        plot_bgcolor=CFG["plot_bg"],
    )
    return fig


def top_days_table():
    data = results["top_days"].head(CFG["top_days_count"])
    data["date"] = data["date"].apply(format_date)
    return html.Table(
        style={"width": "100%", "borderCollapse": "collapse"},
        children=[
            html.Thead(
                html.Tr(
                    [
                        html.Th(
                            "Date",
                            style={
                                "textAlign": "left",
                                "padding": "8px",
                                "borderBottom": "2px solid #ddd",
                            },
                        ),
                        html.Th(
                            "Alerts",
                            style={
                                "textAlign": "right",
                                "padding": "8px",
                                "borderBottom": "2px solid #ddd",
                            },
                        ),
                    ]
                )
            ),
            html.Tbody(
                [
                    html.Tr(
                        [
                            html.Td(
                                row["date"],
                                style={
                                    "padding": "6px 8px",
                                    "borderBottom": "1px solid #eee",
                                },
                            ),
                            html.Td(
                                f"{row['alert_count']:,}",
                                style={
                                    "textAlign": "right",
                                    "padding": "6px 8px",
                                    "borderBottom": "1px solid #eee",
                                    "fontWeight": "bold",
                                    "color": CFG["accent"],
                                },
                            ),
                        ]
                    )
                    for _, row in data.iterrows()
                ]
            ),
        ],
    )


# ── Stat cards ─────────────────────────────────────────────────────────────

ds = results["duration_stats"]
stat_cards = html.Div(
    [
        html.Div(
            [
                html.H4("Total Alerts", style={"margin": "0 0 5px 0", "color": "#666"}),
                html.Span(
                    f"{len(df):,}",
                    style={
                        "fontSize": "28px",
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
                "boxShadow": "0 2px 8px rgba(0,0,0,0.1)",
                "flex": "1",
            },
        ),
        html.Div(
            [
                html.H4("Avg Duration", style={"margin": "0 0 5px 0", "color": "#666"}),
                html.Span(
                    f"{ds['mean_s']/60:.0f} min",
                    style={
                        "fontSize": "28px",
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
                "boxShadow": "0 2px 8px rgba(0,0,0,0.1)",
                "flex": "1",
            },
        ),
        html.Div(
            [
                html.H4("Date Range", style={"margin": "0 0 5px 0", "color": "#666"}),
                html.Span(
                    f"{df[COL_STARTED].min().strftime('%b %Y')} – {df[COL_STARTED].max().strftime('%b %Y')}",
                    style={
                        "fontSize": "20px",
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
                "boxShadow": "0 2px 8px rgba(0,0,0,0.1)",
                "flex": "1",
            },
        ),
        html.Div(
            [
                html.H4("Oblasts", style={"margin": "0 0 5px 0", "color": "#666"}),
                html.Span(
                    f"{df['oblast'].nunique() - 1} oblasts + Kyiv city",
                    style={
                        "fontSize": "28px",
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
                "boxShadow": "0 2px 8px rgba(0,0,0,0.1)",
                "flex": "1",
            },
        ),
    ],
    style={"display": "flex", "gap": "15px", "marginBottom": "20px"},
)

# ── App layout ─────────────────────────────────────────────────────────────

app = dash.Dash(__name__)
app.title = "AlerticUA"

app.layout = html.Div(
    style={
        "backgroundColor": CFG["bg"],
        "minHeight": "100vh",
        "padding": "20px",
        "fontFamily": "Segoe UI, sans-serif",
    },
    children=[
        html.H1(
            "AlerticUA",
            style={"color": CFG["text"], "marginBottom": "5px"},
        ),
        html.P(
            "Interactive analysis of air raid alert patterns across Ukrainian oblasts (2022-2026)",
            style={"color": "#666", "marginTop": "0", "marginBottom": "20px"},
        ),
        stat_cards,
        # ── Key Insights ────────────────────────────────────────────────
        html.Div(
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
                    [
                        html.Li(
                            f"Donetska, Kharkivska, and Zaporizka oblasts account for ~31% of all {len(df):,} alerts — the front-line regions."
                        ),
                        html.Li(
                            f"Evening alerts (18:00-22:00) last nearly twice as long (~2h) as the average ({ds['mean_s']/60:.0f} min)."
                        ),
                        html.Li(
                            f"Though winters are hard for us, Ukrainians, the busiest season is Summer (38,325 alerts) and Winter is the quietest (24,990)."
                        ),
                        html.Li(
                            f"75% of alerts occur during daytime (06:00-22:00), but night alerts last significantly longer."
                        ),
                        html.Li(
                            f"24 August 2022 — Ukraine's Independence Day — was the single busiest day on record (370 oblast level alerts in a single day)."
                        ),
                        html.Li(
                            f"Though most alerts start at the daytime, most russian attacks happen at night."
                        ),
                    ],
                    style={
                        "lineHeight": "1.8",
                        "paddingLeft": "20px",
                        "marginBottom": 0,
                    },
                ),
            ],
            style={
                "backgroundColor": CFG["card_bg"],
                "padding": "15px 20px",
                "borderRadius": "8px",
                "boxShadow": "0 2px 8px rgba(0,0,0,0.1)",
                "marginBottom": "20px",
            },
        ),
        dcc.Tabs(
            style={"marginBottom": "20px"},
            children=[
                dcc.Tab(
                    label="Overview",
                    style=tab_style,
                    selected_style=tab_selected_style,
                    children=[
                        card(
                            dcc.Graph(figure=fig_oblasts()), title="Regional Breakdown"
                        ),
                        card(
                            dcc.Graph(figure=fig_daily_trend()),
                            title="Trends Over Time",
                        ),
                    ],
                ),
                dcc.Tab(
                    label="Hourly Patterns",
                    style=tab_style,
                    selected_style=tab_selected_style,
                    children=[
                        card(
                            dcc.Graph(figure=fig_hourly()),
                            title="Alert Frequency by Hour",
                        ),
                        card(
                            dcc.Graph(figure=fig_duration_by_hour()),
                            title="Duration by Start Hour",
                        ),
                        card(
                            dcc.Graph(figure=fig_duration_hist()),
                            title=f"Duration Distribution (≤{CFG['histogram_max_minutes']//60}h)",
                        ),
                        card(
                            top_days_table(),
                            title=f"Top {CFG['top_days_count']} Busiest Days",
                        ),
                        html.Div(
                            [
                                html.P(
                                    "🗓️ 24-08-2022 — Ukraine's Independence Day, marked by a large-scale russian missile attack across the country.",
                                    style={
                                        "color": "#666",
                                        "fontSize": "13px",
                                        "fontStyle": "italic",
                                        "margin": "5px 0 0 0",
                                    },
                                ),
                                html.P(
                                    "🗓️ 25-08-2023 — Another Independence Day period attack wave.",
                                    style={
                                        "color": "#666",
                                        "fontSize": "13px",
                                        "fontStyle": "italic",
                                        "margin": "3px 0 0 0",
                                    },
                                ),
                            ],
                            style={"padding": "0 8px"},
                        ),
                    ],
                ),
                dcc.Tab(
                    label="Weekly & Monthly",
                    style=tab_style,
                    selected_style=tab_selected_style,
                    children=[
                        card(dcc.Graph(figure=fig_dayofweek()), title="By Day of Week"),
                        card(
                            dcc.Graph(figure=fig_monthly()),
                            title="By Month (All Years)",
                        ),
                        card(dcc.Graph(figure=fig_season())),
                        card(dcc.Graph(figure=fig_day_night())),
                    ],
                ),
                dcc.Tab(
                    label="Duration Analysis",
                    style=tab_style,
                    selected_style=tab_selected_style,
                    children=[
                        card(
                            dcc.Graph(figure=fig_duration_oblast()),
                            title="Avg Duration by Oblast",
                        ),
                        card(
                            dcc.Graph(figure=fig_duration_hist()),
                            title=f"Duration Distribution (≤{CFG['histogram_max_minutes']//60}h)",
                        ),
                        card(
                            dcc.Graph(figure=fig_duration_by_hour()),
                            title="Duration by Start Hour",
                        ),
                    ],
                ),
            ],
        ),
        html.Hr(),
        html.P(
            "Data source: https://github.com/Vadimkin/ukrainian-air-raid-sirens-dataset.git ··· Built for AlerticUA",
            style={"textAlign": "center", "color": "#999", "fontSize": "14px"},
        ),
    ],
)

if __name__ == "__main__":
    app.run(debug=True)
