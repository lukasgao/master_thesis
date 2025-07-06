"""All the general configuration of the project."""
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
RAW = BASE / "data" / "original_data"
BLD = BASE / "data" / "processed"
OUTPUT = BASE /"data" / "outputs"
TEST = BASE / "tests"
YEAR_RANGE = range(2017, 2020)


RANDOM_SEED = 42
DATE_FORMAT = "%Y-%m-%d"
