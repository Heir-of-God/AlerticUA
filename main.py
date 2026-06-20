"""
AlerticUA
CLI analysis results. For visualization use app.py
"""

from src.data_loader import load_and_prepare
from src.analysis import run_analysis


def main():
    df = load_and_prepare()
    results = run_analysis(df)


if __name__ == "__main__":
    main()
