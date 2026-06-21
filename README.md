# AlerticUA

Interactive time series analysis of air raid alert patterns in Ukraine. Built as a mini pet-project for an Agentic AI school assignment.

## Features

- **Data Pipeline**: Load, clean, and cache oblast-level air raid alert data
- **Statistical Analysis**: Alert patterns by region, hour, day of week, month, season, and time of day
- **Interactive Dashboard**: Dash web app with 5 tabs — Overview, Hourly Patterns, Weekly & Monthly, Duration Analysis, Forecast
- **Forecasting**: Facebook Prophet model for predicting daily alert counts and average duration (14-day horizon with backtesting)
- **Key Insights**: Automatically generated narrative highlights

## Project Structure

```
AlerticUA/
├── data/
│   ├── raw/              # Original dataset
│   └── processed/        # Cleaned/transformed data (gitignored)
├── src/
│   ├── data_loader.py    # Load & parse CSV, caching
│   ├── analysis.py       # Statistical analysis
│   ├── forecasting.py    # Prophet model
│   └── config.py         # Paths, constants, color schemes
│
├── app.py                # Dash dashboard entry point
├── main.py               # CLI analysis entry point
├── requirements.txt
└── README.md
```

## Setup

1. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate    # Windows
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

### CLI Analysis

```bash
python main.py
```

Prints statistical summaries to the console.

### Interactive Dashboard

```bash
python app.py
```

Opens a Dash web app at `http://127.0.0.1:8050` with:

- **Overview**: Regional breakdown + daily trend
- **Hourly Patterns**: Alert frequency, duration by hour, distribution histogram, top busiest days
- **Weekly & Monthly**: Day of week, month, season, day/night split
- **Duration Analysis**: Avg duration by oblast, distribution, by start hour
- **Forecast**: Prophet model with date picker — predicts next 14 days for both alert count and average duration

## Data Source

Dataset: [ukrainian-air-raid-sirens-dataset](https://github.com/Vadimkin/ukrainian-air-raid-sirens-dataset) by Vadimkin.

## Tech Stack

- **Python 3.10+**
- **Dash** (Plotly) — interactive web dashboard
- **Prophet** (Meta) — time series forecasting
- **Pandas** — data processing

## License

MIT
