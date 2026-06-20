from pathlib import Path

# Project root
ROOT_DIR = Path(__file__).resolve().parent.parent

# Data paths
RAW_DATA_PATH = ROOT_DIR / "data" / "raw" / "raw_data_en.csv"
PROCESSED_DATA_PATH = ROOT_DIR / "data" / "processed"
PROCESSED_FILE = PROCESSED_DATA_PATH / "oblast_alerts.csv"
OUTPUT_PLOTS_DIR = ROOT_DIR / "output" / "plots"

# Columns
COL_OBLAST = "oblast"
COL_RAION = "raion"
COL_HROMADA = "hromada"
COL_LEVEL = "level"
COL_STARTED = "started_at"
COL_FINISHED = "finished_at"
COL_SOURCE = "source"
COL_DURATION = "duration_seconds"

# Filter values
LEVEL_OBLAST = "oblast"

# Permanent siren regions to exclude
EXCLUDED_OBLASTS = [
    "Luhanska oblast",  # permanent siren
]

# Max reasonable alert duration (14 days in seconds)
MAX_DURATION_SECONDS = 14 * 24 * 3600  # 1,209,600s
