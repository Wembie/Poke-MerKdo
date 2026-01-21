"""Configuration settings for Poke MerKdo"""

from pathlib import Path
from typing import Final

_PROJECT_ROOT: Final[Path] = Path(__file__).parent.parent
_DATA_DIR: Final[Path] = _PROJECT_ROOT / "data"

CACHE_DIR: Final[Path] = _DATA_DIR / "cache"
LOGS_DIR: Final[Path] = _DATA_DIR / "logs"
CATALOG_DIR: Final[Path] = _PROJECT_ROOT / "catalogs"
COLLECTION_CSV: Final[Path] = _PROJECT_ROOT / "collection.csv"
PRICES_JSON: Final[Path] = _DATA_DIR / "prices.json"
LOGO_PATH: Final[Path] = _DATA_DIR / "images" / "logo" / "Poke_MerKdo_Logo.png"

INSTAGRAM_URL: Final[str] = "https://www.instagram.com/pokemerkdo"
INSTAGRAM_HANDLE: Final[str] = "@pokemerkdo"
AUTHOR: Final[str] = "Wembie"

CACHE_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
CATALOG_DIR.mkdir(parents=True, exist_ok=True)

CACHE_EXPIRY_DAYS: Final[int] = 30
