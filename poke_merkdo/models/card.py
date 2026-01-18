"""Card data models"""

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, field_validator


class PokemonSet(BaseModel):
    """Represents a Pokémon TCG set"""

    id: str
    name: str
    series: str
    total: int
    release_date: str | None = None


class CardStats(BaseModel):
    """Extended card statistics from API"""

    hp: str | None = None
    types: list[str] = Field(default_factory=list)
    rarity: str | None = None
    artist: str | None = None
    attacks: list[dict[str, Any]] = Field(default_factory=list)
    weaknesses: list[dict[str, Any]] = Field(default_factory=list)
    resistances: list[dict[str, Any]] = Field(default_factory=list)
    retreat_cost: list[str] = Field(default_factory=list)


class Card(BaseModel):
    """Represents a Pokémon card from CSV and API"""

    id: str
    product_name: str
    console_name: str
    price_in_pennies: int
    condition: str = "Normal wear"
    quantity: int = 1
    date_entered: datetime
    sku: str | None = None
    notes: str | None = None

    api_id: str | None = None
    image_url: str | None = None
    image_url_hires: str | None = None
    stats: CardStats | None = None
    set_info: PokemonSet | None = None

    custom_price: Decimal | None = None

    @field_validator("date_entered", mode="before")
    @classmethod
    def parse_date(cls, v: str | datetime) -> datetime:
        """Parse date string to datetime"""
        if isinstance(v, datetime):
            return v
        try:
            return datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            return datetime.now()

    @property
    def price_dollars(self) -> Decimal:
        """Get price in dollars"""
        if self.custom_price:
            return self.custom_price
        return Decimal(self.price_in_pennies) / Decimal(100)

    @property
    def card_number(self) -> str:
        """Extract card number from product name"""
        import re

        match = re.search(r"-\s*(\d+)/\d+", self.product_name)
        if match:
            return match.group(1)

        if "#" in self.product_name:
            return self.product_name.split("#")[-1].strip()

        return ""

    @property
    def card_name(self) -> str:
        """Extract clean card name without number"""
        import re

        match = re.match(r"^(.+?)\s*-\s*\d+/\d+", self.product_name)
        if match:
            return match.group(1).strip()

        if "#" in self.product_name:
            return self.product_name.split("#")[0].strip()

        return self.product_name

    @property
    def is_saleable(self) -> bool:
        """Check if card has duplicates for sale"""
        return self.quantity >= 2

    def __str__(self) -> str:
        return (
            f"{self.product_name} ({self.console_name}) "
            f"- ${self.price_dollars:.2f} x{self.quantity}"
        )
