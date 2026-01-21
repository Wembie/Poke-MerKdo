"""Path constants for Poke MerKdo"""

from pathlib import Path
from typing import Final

PROJECT_ROOT: Final[Path] = Path(__file__).parent.parent.parent
DATA_DIR: Final[Path] = PROJECT_ROOT / "data"

CACHE_DIR: Final[Path] = DATA_DIR / "cache"
LOGS_DIR: Final[Path] = DATA_DIR / "logs"
CATALOG_DIR: Final[Path] = PROJECT_ROOT / "catalogs"

COLLECTION_CSV: Final[Path] = PROJECT_ROOT / "collection.csv"
PRICES_JSON: Final[Path] = DATA_DIR / "prices.json"
CONFIG_JSON: Final[Path] = DATA_DIR / "config.json"

CACHE_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
CATALOG_DIR.mkdir(parents=True, exist_ok=True)
