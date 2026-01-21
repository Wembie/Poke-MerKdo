"""Store configuration management for Poke MerKdo"""

from json import dump as json_dump
from json import load as json_load
from pathlib import Path
from typing import Final

from poke_merkdo.config.paths import CONFIG_JSON, PROJECT_ROOT

STORE_NAME_DEFAULT: Final[str] = "Poke MerKdo"

DEFAULT_CONFIG: Final[dict] = {
    "store_name": STORE_NAME_DEFAULT,
    "catalog_title": f"{STORE_NAME_DEFAULT} - Catálogo de Cartas",
    "logo_path": "data/images/logo/Poke_Merkdo_Logo.png",
    "social_networks": [
        {
            "platform": "Instagram",
            "handle": "@pokemerkdo",
            "url": "https://www.instagram.com/pokemerkdo/",
        },
        {
            "platform": "WhatsApp",
            "handle": "+57 300 000 0000",
            "url": "https://wa.me/573000000000?text=Hola%2C%20me%20interesa%20una%20carta%20del%20cat%C3%A1logo",
        },
    ],
    "welcome_message": "Bienvenido a nuestro catálogo de cartas Pokémon TCG.",
    "contact_message": "Para consultar precios y disponibilidad, contáctanos directamente.",
}


def _load_config() -> dict:
    """Load configuration from JSON file or use defaults

    - If config.json doesn't exist, creates empty one and uses defaults
    - If config.json is empty or {}, uses defaults
    - If config.json has values, merges with defaults (user values take priority)
    """
    if not CONFIG_JSON.exists():
        CONFIG_JSON.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_JSON, "w", encoding="utf-8") as f:
            f.write("{}\n")
        return DEFAULT_CONFIG.copy()

    try:
        with open(CONFIG_JSON, encoding="utf-8") as f:
            user_config = json_load(f)
        if not user_config:
            return DEFAULT_CONFIG.copy()
        return {**DEFAULT_CONFIG, **user_config}
    except Exception:
        return DEFAULT_CONFIG.copy()


def _save_config(config: dict) -> None:
    """Save configuration to JSON file"""
    CONFIG_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_JSON, "w", encoding="utf-8") as f:
        json_dump(config, f, indent=2, ensure_ascii=False)


def get_config() -> dict:
    """Get current configuration"""
    return _load_config()


def update_config(key: str, value: str) -> None:
    """Update a configuration value"""
    config = _load_config()
    config[key] = value
    _save_config(config)


_config = _load_config()

STORE_NAME: str = _config.get("store_name", DEFAULT_CONFIG["store_name"])
CATALOG_TITLE: str = _config.get("catalog_title", DEFAULT_CONFIG["catalog_title"])
LOGO_PATH: Path = PROJECT_ROOT / _config.get("logo_path", DEFAULT_CONFIG["logo_path"])
SOCIAL_NETWORKS: list[dict] = _config.get(
    "social_networks", DEFAULT_CONFIG["social_networks"]
)
WELCOME_MESSAGE: str = _config.get("welcome_message", DEFAULT_CONFIG["welcome_message"])
CONTACT_MESSAGE: str = _config.get("contact_message", DEFAULT_CONFIG["contact_message"])
