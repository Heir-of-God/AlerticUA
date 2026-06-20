"""
Air Raid Alert Analysis — Ukraine
Main entry point.
"""

from src.data_loader import load_and_prepare


def main():
    df = load_and_prepare()


if __name__ == "__main__":
    main()
