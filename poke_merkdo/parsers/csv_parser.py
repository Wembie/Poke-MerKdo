"""CSV parser for collection data"""

from datetime import datetime
from pathlib import Path

from pandas import DataFrame, Series, isna, read_csv

from poke_merkdo.models import Card, Collection


class CSVParser:
    """Parse collection CSV into Card objects"""

    def __init__(self, csv_path: Path):
        self.csv_path = csv_path

    def parse(self) -> Collection:
        """Parse CSV file into Collection object"""
        df = read_csv(self.csv_path)

        cards: list[Card] = []
        for _, row in df.iterrows():
            try:
                card = self._parse_row(row)
                cards.append(card)
            except Exception as e:
                print(f"Warning: Failed to parse row {row.get('id', 'unknown')}: {e}")
                continue

        return Collection(cards=cards)

    def _parse_row(self, row: Series) -> Card:
        """Parse a single CSV row into Card object"""
        date_str = str(row.get("date-entered", ""))
        try:
            date_entered = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            date_entered = datetime.now()

        return Card(
            id=str(row["id"]),
            product_name=str(row["product-name"]),
            console_name=str(row["console-name"]),
            price_in_pennies=int(row.get("price-in-pennies", 0)),
            condition=str(row.get("condition-string", "Normal wear")),
            quantity=int(row.get("quantity", 1)),
            date_entered=date_entered,
            sku=str(row.get("sku", "")) if not isna(row.get("sku")) else None,
            notes=str(row.get("notes", "")) if not isna(row.get("notes")) else None,
        )

    def export_to_csv(self, collection: Collection, output_path: Path) -> None:
        """Export collection back to CSV format"""
        data = []
        for card in collection.cards:
            data.append(
                {
                    "id": card.id,
                    "product-name": card.product_name,
                    "console-name": card.console_name,
                    "price-in-pennies": card.price_in_pennies,
                    "include-string": "Ungraded",
                    "condition-string": card.condition,
                    "sku": card.sku or "",
                    "notes": card.notes or "",
                    "cost-basis-in-pennies": 0,
                    "quantity": card.quantity,
                    "date-entered": card.date_entered.strftime("%Y-%m-%d"),
                    "grading-company": "",
                    "grading-cert-id": "",
                    "folder": "",
                }
            )

        df = DataFrame(data)
        df.to_csv(output_path, index=False)
