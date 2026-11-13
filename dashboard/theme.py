"""Shared colours, sizes and small layout helpers."""

from typing import Any

import pandas as pd
from dash import html

CFG: dict[str, Any] = {
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
    "oblast_height": 700,
    "daily_height": 450,
    "chart_height": 400,
    "pie_hole": 0.3,
    "histogram_max_minutes": 600,
    "histogram_nbins": 60,
    "rolling_window": 7,
    "date_format": "%d-%m-%Y",
    "top_days_count": 10,
    "day_names": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    "month_names": [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    ],
}  # fmt: skip

TAB_STYLE = {
    "borderBottom": "1px solid #d6d6d6",
    "padding": "12px",
    "fontWeight": "bold",
    "color": "#666",
    "backgroundColor": CFG["bg"],
    "borderTop": "none",
    "borderLeft": "none",
    "borderRight": "none",
}
TAB_SELECTED_STYLE = {
    "borderTop": f"3px solid {CFG['accent']}",
    "borderBottom": "1px solid white",
    "backgroundColor": "white",
    "color": CFG["accent"],
    "padding": "12px",
    "fontWeight": "bold",
}
CARD_SHADOW = "0 2px 8px rgba(0,0,0,0.1)"
NOTE_STYLE = {
    "color": "#666",
    "fontSize": "13px",
    "fontStyle": "italic",
    "margin": "5px 0 0 0",
}


def card(children: Any, title: str | None = None) -> html.Div:
    """White rounded container with an optional heading."""
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
            "boxShadow": CARD_SHADOW,
            "marginBottom": "20px",
        },
    )


def format_date(d: Any) -> str:
    """Format a date/Timestamp as DD-MM-YYYY (other values via str())."""
    return d.strftime(CFG["date_format"]) if hasattr(d, "strftime") else str(d)


def simple_table(
    headers: list[str], rows: list[list[str]], right_align_from: int | None = None
) -> html.Table:
    """Small HTML table; columns from `right_align_from` on are right-aligned."""

    def align(i: int) -> str:
        return "right" if right_align_from is not None and i >= right_align_from else "left"

    return html.Table(
        style={"width": "100%", "borderCollapse": "collapse"},
        children=[
            html.Thead(
                html.Tr(
                    [
                        html.Th(
                            h,
                            style={
                                "textAlign": align(i),
                                "padding": "8px",
                                "borderBottom": "2px solid #ddd",
                            },
                        )
                        for i, h in enumerate(headers)
                    ]
                )
            ),
            html.Tbody(
                [
                    html.Tr(
                        [
                            html.Td(
                                cell,
                                style={
                                    "textAlign": align(i),
                                    "padding": "6px 8px",
                                    "borderBottom": "1px solid #eee",
                                },
                            )
                            for i, cell in enumerate(row)
                        ]
                    )
                    for row in rows
                ]
            ),
        ],
    )


def fmt_ts(ts: pd.Timestamp) -> str:
    """Format a timestamp as 'Mon YYYY'."""
    return ts.strftime("%b %Y")
