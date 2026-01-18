"""
Enricher de cartas usando TCGdex SDK.

TCGdex tiene sets más actualizados que la API oficial de Pokemon TCG.
Incluye sets como Phantasmal Flames (me02), Journey Together (sv09), etc.

Uso:
    from poke_merkdo.api.tcgdex_enricher import enrich_cards_sync

    found, not_found = enrich_cards_sync(cards)
"""

from asyncio import run as asyncio_run
from logging import getLogger

from tcgdexsdk import TCGdex

from poke_merkdo.models.card import Card

logger = getLogger(__name__)


class TCGdexEnricher:
    """
    Enricher de cartas usando TCGdex SDK.

    TCGdex tiene mejor cobertura de sets recientes como:
    - me02: Phantasmal Flames
    - sv09: Journey Together
    - sv08.5: Prismatic Evolutions
    - sv10: Destined Rivals
    """

    SET_MAPPING = {
        "Scarlet & Violet": "sv01",
        "Paldea Evolved": "sv02",
        "Obsidian Flames": "sv03",
        "151": "sv03.5",
        "Paradox Rift": "sv04",
        "Paldean Fates": "sv04.5",
        "Temporal Forces": "sv05",
        "Twilight Masquerade": "sv06",
        "Shrouded Fable": "sv06.5",
        "Stellar Crown": "sv07",
        "Surging Sparks": "sv08",
        "Prismatic Evolutions": "sv08.5",
        "Journey Together": "sv09",
        "Destined Rivals": "sv10",
        "Black Bolt": "sv10.5b",
        "White Flare": "sv10.5w",
        "Phantasmal Flames": "me02",
        "Promo": "svp",
        "Black Star Promo": "svp",
        "SVP Black Star Promos": "svp",
        "Sword & Shield": "swsh01",
        "Rebel Clash": "swsh02",
        "Darkness Ablaze": "swsh03",
        "Champion's Path": "swsh03.5",
        "Vivid Voltage": "swsh04",
        "Shining Fates": "swsh04.5",
        "Battle Styles": "swsh05",
        "Chilling Reign": "swsh06",
        "Evolving Skies": "swsh07",
        "Fusion Strike": "swsh08",
        "Brilliant Stars": "swsh09",
        "Astral Radiance": "swsh10",
        "Pokemon Go": "pgo",
        "Lost Origin": "swsh11",
        "Silver Tempest": "swsh12",
        "Crown Zenith": "swsh12.5",
    }

    def __init__(self, language: str = "en"):
        """
        Inicializa el enricher.

        Args:
            language: Idioma para TCGdex ("en", "es", "fr", etc.)
        """
        self.tcgdex = TCGdex(language)
        self._cache: dict[str, list[str]] = {}
        logger.info(f"TCGdexEnricher initialized (language: {language})")

    def _guess_set_id(self, set_name: str) -> str | None:
        """
        Adivina el ID del set basándose en el nombre.

        Args:
            set_name: Nombre del set (ej: "Pokemon Journey Together")

        Returns:
            ID del set para TCGdex (ej: "sv09") o None
        """
        if not set_name:
            return None

        clean_name = set_name.replace("Pokemon", "").strip()

        for key, value in self.SET_MAPPING.items():
            if key.lower() == clean_name.lower():
                return value

        for key, value in self.SET_MAPPING.items():
            if key.lower() in clean_name.lower():
                return value

        logger.debug(f"No mapping found for set: {set_name}")
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
            set_id = self._guess_set_id(card.console_name)
            if not set_id or not card.card_number:
                logger.debug(f"Cannot determine card ID for {card.card_name}")
                return False

            try:
                card_num = int(card.card_number)
                formatted_num = f"{card_num:03d}"
            except ValueError:
                formatted_num = card.card_number

            card_id = f"{set_id}-{formatted_num}"

            if card_id in self._cache:
                logger.debug(f"Cache hit: {card_id}")
                self._apply_data(card, self._cache[card_id])
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

                self._cache[card_id] = tcg_card
                self._apply_data(card, tcg_card)
                logger.info(f"Card enriched: {card_id} -> {card.card_name}")
                return True
            else:
                logger.debug(f"Card not found: {card_id}")
                return False

        except Exception as e:
            logger.debug(f"Error enriching {card.card_name}: {e}")
            return False

    def _apply_data(self, card: Card, tcg_card) -> None:
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
