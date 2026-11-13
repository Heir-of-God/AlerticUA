from pathlib import Path

# Project root
ROOT_DIR = Path(__file__).resolve().parent.parent

# Data paths
RAW_DATA_PATH = ROOT_DIR / "data" / "raw" / "raw_data_en.csv"
PROCESSED_DATA_PATH = ROOT_DIR / "data" / "processed"
PROCESSED_FILE = PROCESSED_DATA_PATH / "oblast_alerts.csv"

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

# Season mapping (month → season name)
SEASON_MAP = {
    12: "Winter",
    1: "Winter",
    2: "Winter",
    3: "Spring",
    4: "Spring",
    5: "Spring",
    6: "Summer",
    7: "Summer",
    8: "Summer",
    9: "Autumn",
    10: "Autumn",
    11: "Autumn",
}

# Night hours: 22:00–06:00 (inclusive of start, exclusive of end)
NIGHT_START_HOUR = 22
NIGHT_END_HOUR = 6
