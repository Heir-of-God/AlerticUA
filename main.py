"""
Air Raid Alert Analysis — Ukraine
Main entry point.
"""

from src.data_loader import load_and_prepare
from src.analysis import run_analysis


def main():
    df = load_and_prepare()
    results = run_analysis(df)
    # Visualization will be added in the next step


if __name__ == "__main__":
    main()
