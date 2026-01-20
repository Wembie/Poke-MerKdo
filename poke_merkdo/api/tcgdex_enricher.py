"""
Enricher de cartas usando TCGdex SDK.

TCGdex tiene sets más actualizados que la API oficial de Pokemon TCG.
Incluye sets como Phantasmal Flames (me02), Journey Together (sv09), etc.

Uso:
    from poke_merkdo.api.tcgdex_enricher import enrich_cards_sync

    found, not_found = enrich_cards_sync(cards)
"""

import re
import unicodedata
from asyncio import run as asyncio_run
from logging import getLogger

from requests import get as requests_get
from tcgdexsdk import TCGdex

from poke_merkdo.models.card import Card

logger = getLogger(__name__)

TCGDEX_SETS_URL = "https://api.tcgdex.net/v2/en/sets"


def normalize_set_name(name: str) -> str:
    """
    Normaliza un nombre de set para comparación determinística.

    Transformaciones aplicadas:
    1. Convierte a minúsculas
    2. Normaliza caracteres Unicode (é -> e, etc.)
    3. Elimina prefijos comunes (Pokemon, Pokémon)
    4. Elimina caracteres especiales excepto espacios y alfanuméricos
    5. Colapsa espacios múltiples
    6. Elimina espacios al inicio/final

    Args:
        name: Nombre del set a normalizar

    Returns:
        Nombre normalizado para comparación
    """
    if not name:
        return ""

    normalized = name.lower()

    normalized = unicodedata.normalize("NFKD", normalized)
    normalized = normalized.encode("ascii", "ignore").decode("ascii")

    prefixes_to_remove = ["pokemon ", "pokmon "]
    for prefix in prefixes_to_remove:
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix) :]
            break

    normalized = re.sub(r"[^a-z0-9\s]", "", normalized)

    normalized = re.sub(r"\s+", " ", normalized).strip()

    return normalized


class SetMappingCache:
    """
    Cache para el mapping dinámico de sets desde TCGdex API.

    Singleton que mantiene el mapping {normalized_name: set_id} en memoria.
    Se inicializa una sola vez al primer uso.
    """

    _instance: "SetMappingCache | None" = None
    _mapping: dict[str, str] | None = None
    _reverse_mapping: dict[str, str] | None = None

    def __new__(cls) -> "SetMappingCache":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_mapping(self) -> dict[str, str]:
        """
        Obtiene el mapping de nombres normalizados a IDs de set.

        Returns:
            Dict {normalized_name: set_id}
        """
        if self._mapping is None:
            self._load_mapping()
        return self._mapping or {}

    def get_reverse_mapping(self) -> dict[str, str]:
        """
        Obtiene el mapping reverso de IDs a nombres originales.

        Returns:
            Dict {set_id: original_name}
        """
        if self._reverse_mapping is None:
            self._load_mapping()
        return self._reverse_mapping or {}

    def _load_mapping(self) -> None:
        """Carga el mapping desde la API de TCGdex."""
        self._mapping = {}
        self._reverse_mapping = {}

        try:
            logger.info("Loading set mapping from TCGdex API...")
            response = requests_get(TCGDEX_SETS_URL, timeout=10)
            response.raise_for_status()

            sets_data = response.json()

            for set_info in sets_data:
                set_id = set_info.get("id", "")
                set_name = set_info.get("name", "")

                if not set_id or not set_name:
                    continue

                normalized = normalize_set_name(set_name)
                self._mapping[normalized] = set_id
                self._reverse_mapping[set_id] = set_name

            self._add_common_aliases()

            logger.info(f"Loaded {len(self._mapping)} sets from TCGdex API")

        except Exception as e:
            logger.warning(f"Failed to load sets from API: {e}")
            self._load_fallback_mapping()

    def _add_common_aliases(self) -> None:
        """Agrega aliases comunes que no están en la API."""
        if self._mapping is None:
            return

        aliases = {
            "promo": "svp",
            "black star promo": "svp",
            "sv promos": "svp",
            "swsh promos": "swshp",
            "swsh black star promos": "swshp",
            "pokemon go": "swsh10.5",
            "pokmon go": "swsh10.5",
            "go": "swsh10.5",
            "sword shield": "swsh1",
        }

        for alias, set_id in aliases.items():
            normalized = normalize_set_name(alias)
            if normalized not in self._mapping:
                self._mapping[normalized] = set_id

    def _load_fallback_mapping(self) -> None:
        """Mapping de fallback si la API falla."""
        logger.warning("Using fallback set mapping")
        fallback = {
            "scarlet violet": "sv01",
            "paldea evolved": "sv02",
            "obsidian flames": "sv03",
            "151": "sv03.5",
            "paradox rift": "sv04",
            "paldean fates": "sv04.5",
            "temporal forces": "sv05",
            "twilight masquerade": "sv06",
            "shrouded fable": "sv06.5",
            "stellar crown": "sv07",
            "surging sparks": "sv08",
            "prismatic evolutions": "sv08.5",
            "journey together": "sv09",
            "destined rivals": "sv10",
            "black bolt": "sv10.5b",
            "white flare": "sv10.5w",
            "phantasmal flames": "me02",
            "promo": "svp",
            "svp black star promos": "svp",
            "sword shield": "swsh1",
            "rebel clash": "swsh2",
            "darkness ablaze": "swsh3",
            "champions path": "swsh3.5",
            "vivid voltage": "swsh4",
            "shining fates": "swsh4.5",
            "battle styles": "swsh5",
            "chilling reign": "swsh6",
            "evolving skies": "swsh7",
            "fusion strike": "swsh8",
            "brilliant stars": "swsh9",
            "astral radiance": "swsh10",
            "pokemon go": "swsh10.5",
            "lost origin": "swsh11",
            "silver tempest": "swsh12",
            "crown zenith": "swsh12.5",
        }
        self._mapping = fallback
        self._reverse_mapping = {v: k for k, v in fallback.items()}

    def refresh(self) -> None:
        """Fuerza una recarga del mapping desde la API."""
        self._mapping = None
        self._reverse_mapping = None
        self._load_mapping()


class TCGdexEnricher:
    """
    Enricher de cartas usando TCGdex SDK con mapping dinámico.

    Características:
    - Carga automática de sets desde la API de TCGdex
    - Normalización robusta de nombres de sets
    - Cache en memoria para evitar llamadas repetidas
    - Fallback a mapping estático si la API falla
    """

    def __init__(self, language: str = "en"):
        """
        Inicializa el enricher.

        Args:
            language: Idioma para TCGdex ("en", "es", "fr", etc.)
        """
        self.tcgdex = TCGdex(language)
        self._card_cache: dict[str, object] = {}
        self._set_cache = SetMappingCache()
        logger.info(f"TCGdexEnricher initialized (language: {language})")

    def _resolve_set_id(self, set_name: str) -> str | None:
        """
        Resuelve el ID del set a partir del nombre del CSV.

        Estrategia de búsqueda (en orden):
        1. Match exacto con nombre normalizado
        2. Match parcial (nombre normalizado contenido en el set name)

        Args:
            set_name: Nombre del set desde el CSV (ej: "Pokemon Journey Together")

        Returns:
            ID del set para TCGdex (ej: "sv09") o None si no se encuentra
        """
        if not set_name:
            return None

        mapping = self._set_cache.get_mapping()
        normalized_input = normalize_set_name(set_name)

        if normalized_input in mapping:
            set_id = mapping[normalized_input]
            logger.debug(f"Exact match: '{set_name}' -> '{set_id}'")
            return set_id

        for normalized_name, set_id in mapping.items():
            if normalized_name in normalized_input:
                logger.debug(f"Partial match: '{set_name}' -> '{set_id}'")
                return set_id

        for normalized_name, set_id in mapping.items():
            if normalized_input in normalized_name:
                logger.debug(f"Reverse partial match: '{set_name}' -> '{set_id}'")
                return set_id

        logger.debug(
            f"No mapping found for set: '{set_name}' (normalized: '{normalized_input}')"
        )
        return None

    async def enrich_card(self, card: Card) -> bool:
        """
        Enriquece una carta con datos de TCGdex.

        SOLO busca por ID exacto (set + número). No usa fallback por nombre
        para evitar traer imágenes de cartas incorrectas.

        Args:
            card: Carta a enriquecer

        Returns:
            True si se enriqueció exitosamente
        """
        if card.image_url:
            logger.debug(f"Skipping {card.card_name}: already has image")
            return True

        if "basic" in card.card_name.lower() and "energy" in card.card_name.lower():
            logger.debug(f"Skipping basic energy: {card.card_name}")
            return False

        if "energy" in card.console_name.lower():
            logger.debug(f"Skipping energy set card: {card.card_name}")
            return False

        try:
            set_id = self._resolve_set_id(card.console_name)
            if not set_id or not card.card_number:
                logger.debug(f"Cannot determine card ID for {card.card_name}")
                return False

            try:
                card_num = int(card.card_number)
                formatted_num = f"{card_num:03d}"
            except ValueError:
                formatted_num = card.card_number

            card_id = f"{set_id}-{formatted_num}"

            if card_id in self._card_cache:
                logger.debug(f"Cache hit: {card_id}")
                self._apply_data(card, self._card_cache[card_id])
                return True

            logger.debug(f"Fetching {card_id} from TCGdex...")
            tcg_card = await self.tcgdex.card.get(card_id)

            if tcg_card:
                tcg_name = tcg_card.name if hasattr(tcg_card, "name") else ""
                csv_name = card.card_name.split()[0].lower()
                if csv_name not in tcg_name.lower():
                    logger.debug(
                        f"Name mismatch: {card.card_name} != {tcg_name}, skipping"
                    )
                    return False

                self._card_cache[card_id] = tcg_card
                self._apply_data(card, tcg_card)
                logger.info(f"Card enriched: {card_id} -> {card.card_name}")
                return True
            else:
                logger.debug(f"Card not found: {card_id}")
                return False

        except Exception as e:
            logger.debug(f"Error enriching {card.card_name}: {e}")
            return False

    def _apply_data(self, card: Card, tcg_card: object) -> None:
        """
        Aplica los datos de TCGdex a la carta.

        Args:
            card: Carta destino
            tcg_card: Datos de TCGdex
        """
        if hasattr(tcg_card, "image") and tcg_card.image:
            card.image_url = f"{tcg_card.image}/high.png"

    async def enrich_cards(
        self, cards: list[Card], show_progress: bool = False
    ) -> tuple[int, int]:
        """
        Enriquece múltiples cartas.

        Args:
            cards: Lista de cartas
            show_progress: Mostrar progreso

        Returns:
            Tupla (encontradas, no encontradas)
        """
        found = 0
        not_found = 0
        total = len(cards)

        for i, card in enumerate(cards):
            if show_progress and i % 10 == 0:
                logger.info(f"Progress: {i}/{total}")

            success = await self.enrich_card(card)
            if success:
                found += 1
            else:
                not_found += 1

        logger.info(f"Enrichment complete: {found} found, {not_found} not found")
        return found, not_found


async def enrich_cards_with_tcgdex(
    cards: list[Card], language: str = "en", show_progress: bool = False
) -> tuple[int, int]:
    """
    Función async para enriquecer cartas con TCGdex.

    Args:
        cards: Lista de cartas a enriquecer
        language: Idioma (default: "en")
        show_progress: Mostrar progreso

    Returns:
        Tupla (encontradas, no encontradas)
    """
    enricher = TCGdexEnricher(language=language)
    return await enricher.enrich_cards(cards, show_progress=show_progress)


def enrich_cards_sync(
    cards: list[Card], language: str = "en", show_progress: bool = False
) -> tuple[int, int]:
    """
    Versión síncrona del enricher.

    Args:
        cards: Lista de cartas
        language: Idioma
        show_progress: Mostrar progreso

    Returns:
        Tupla (encontradas, no encontradas)
    """
    return asyncio_run(enrich_cards_with_tcgdex(cards, language, show_progress))
