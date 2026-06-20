# AlerticUA

A time series analysis project exploring air raid alert patterns in Ukraine using publicly available data. Built as a mini pet-project for an Agentic AI school assignment.

## Features

- Load and inspect historical air raid alert data
- Explore patterns by region, time of day, day of week, and month
- Interactive visualizations (Plotly HTML)
- Optional forecasting with Prophet

## Project Structure

```
AlerticUA/
├── data/
│   ├── raw/          # Original dataset (CSV)
│   └── processed/    # Cleaned/transformed data
├── src/
│   ├── data_loader.py    # Load & parse CSV
│   ├── preprocessing.py  # Clean, filter, resample
│   ├── analysis.py       # Statistical analysis
│   ├── visualization.py  # Plotly charts
│   ├── forecasting.py    # Prophet model
│   └── config.py         # Paths & constants
├── output/
│   └── plots/        # Generated HTML charts
├── main.py           # Entry point
├── requirements.txt
└── README.md
```

## Setup

1. Create a virtual environment:

   ```bash
   python -m venv venv
   ```

2. Activate it:

   ```bash
   venv\Scripts\activate    # Windows
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Place the dataset CSV in `data/raw/`

## Usage

```bash
python main.py
```

## Data Source

Dataset: [ukrainian-air-raid-sirens-dataset](https://github.com/Vadimkin/ukrainian-air-raid-sirens-dataset) by Vadimkin.

## License

MIT
