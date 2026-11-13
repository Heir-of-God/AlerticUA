"""
Dash web dashboard for AlerticUA.
Run with: python app.py

Environment variables (all optional):
  ALERTICUA_DEBUG=1   enable Dash debug mode (off by default)
  ALERTICUA_HOST      host to bind (default 127.0.0.1)
  ALERTICUA_PORT      port to listen on (default 8050)
"""

import os

import dash

from dashboard.callbacks import register_callbacks
from dashboard.layout import build_layout
from src.analysis import run_analysis
from src.data_loader import load_and_prepare

df = load_and_prepare()
results = run_analysis(df)

app = dash.Dash(__name__)
app.title = "AlerticUA"
app.layout = build_layout(df, results)
register_callbacks(app, df)


if __name__ == "__main__":
    app.run(
        debug=os.environ.get("ALERTICUA_DEBUG", "").lower() in {"1", "true", "yes"},
        host=os.environ.get("ALERTICUA_HOST", "127.0.0.1"),
        port=int(os.environ.get("ALERTICUA_PORT", "8050")),
    )
