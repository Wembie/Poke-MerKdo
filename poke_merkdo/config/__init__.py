"""Configuration module for Poke MerKdo"""

from poke_merkdo.config.constants import AUTHOR, CACHE_EXPIRY_DAYS
from poke_merkdo.config.paths import (
    CACHE_DIR,
    CATALOG_DIR,
    COLLECTION_CSV,
    CONFIG_JSON,
    DATA_DIR,
    LOGS_DIR,
    PRICES_JSON,
    PROJECT_ROOT,
)
from poke_merkdo.config.store import (
    CATALOG_TITLE,
    CONTACT_MESSAGE,
    LOGO_PATH,
    SOCIAL_NETWORKS,
    STORE_NAME,
    WELCOME_MESSAGE,
    get_config,
    update_config,
)

__all__ = [
    "PROJECT_ROOT",
    "DATA_DIR",
    "CACHE_DIR",
    "LOGS_DIR",
    "CATALOG_DIR",
    "COLLECTION_CSV",
    "PRICES_JSON",
    "CONFIG_JSON",
    "AUTHOR",
    "CACHE_EXPIRY_DAYS",
    "STORE_NAME",
    "CATALOG_TITLE",
    "LOGO_PATH",
    "SOCIAL_NETWORKS",
    "WELCOME_MESSAGE",
    "CONTACT_MESSAGE",
    "get_config",
    "update_config",
]
