"""Collection models"""

from collections.abc import Iterator
from decimal import Decimal

from pydantic import BaseModel

from poke_merkdo.models.card import Card


class SaleableCard(BaseModel):
    """A card available for sale with calculated quantity"""

    card: Card
    quantity_for_sale: int

    @property
    def total_value(self) -> Decimal:
        """Total value of all saleable copies"""
        return self.card.price_dollars * self.quantity_for_sale


class Collection(BaseModel):
    """Represents the entire card collection"""

    cards: list[Card]

    def get_saleable_cards(self) -> list[SaleableCard]:
        """Get all cards with quantity >= 2 (keep 1, sell the rest)"""
        return self.get_cards_by_min_quantity(min_quantity=2)

    def get_cards_by_min_quantity(self, min_quantity: int = 2) -> list[SaleableCard]:
        """Get cards with quantity >= min_quantity"""
        result = []
        for card in self.cards:
            if card.quantity >= min_quantity:
                if min_quantity == 1:
                    quantity_for_sale = card.quantity
                else:
                    quantity_for_sale = card.quantity - 1
                result.append(
                    SaleableCard(card=card, quantity_for_sale=quantity_for_sale)
                )
        return result

    def get_cards_by_set(self, set_name: str) -> list[Card]:
        """Filter cards by set name"""
        return [c for c in self.cards if c.console_name == set_name]

    def get_unique_sets(self) -> list[str]:
        """Get list of unique set names"""
        return sorted(set(c.console_name for c in self.cards))

    def total_cards(self) -> int:
        """Total number of cards (counting duplicates)"""
        return sum(c.quantity for c in self.cards)

    def total_unique_cards(self) -> int:
        """Total number of unique cards"""
        return len(self.cards)

    def total_saleable_cards(self) -> int:
        """Total number of cards available for sale"""
        return sum(c.quantity_for_sale for c in self.get_saleable_cards())

    def total_collection_value(self) -> Decimal:
        """Total value of all saleable cards"""
        saleable = self.get_saleable_cards()
        if not saleable:
            return Decimal(0)
        return sum((c.total_value for c in saleable), Decimal(0))

    def __iter__(self) -> Iterator[Card]:  # type: ignore[override]
        return iter(self.cards)

    def __len__(self) -> int:
        return len(self.cards)
