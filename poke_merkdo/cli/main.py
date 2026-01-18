"""Main CLI application"""

from datetime import datetime
from decimal import Decimal
from json import dump as json_dump
from json import load as json_load
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from poke_merkdo.api.tcgdex_enricher import enrich_cards_sync
from poke_merkdo.cache import ImageCache
from poke_merkdo.config import CATALOG_DIR, COLLECTION_CSV, PRICES_JSON
from poke_merkdo.generators import PDFGenerator
from poke_merkdo.models import Collection
from poke_merkdo.parsers import CSVParser

app = typer.Typer(
    name="poke-merkdo",
    help="Professional Pokémon card catalog generator for Poke MerKdo",
    add_completion=False,
)
console = Console(legacy_windows=True, force_terminal=True)


@app.command()
def generate(
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output PDF path (default: catalogs/catalog_YYYY-MM-DD.pdf)",
    ),
    csv_file: Path = typer.Option(
        COLLECTION_CSV,
        "--csv",
        "-c",
        help="Path to collection CSV file",
    ),
    enrich: bool = typer.Option(
        False,
        "--enrich/--no-enrich",
        help="Fetch images and stats from Pokemon TCG API (default: table format)",
    ),
    include_stats: bool = typer.Option(
        True,
        "--stats/--no-stats",
        help="Include card statistics in PDF",
    ),
    show_prices: bool = typer.Option(
        False,
        "--prices/--no-prices",
        help="Show prices in PDF (default: hidden, customers ask for prices)",
    ),
    title: str = typer.Option(
        "Poke MerKdo - Catálogo de Cartas",
        "--title",
        "-t",
        help="Catalog title",
    ),
) -> None:
    """
    Generate PDF catalog of saleable cards (quantity >= 2).

    This will parse your collection CSV, optionally enrich cards with
    Pokemon TCG API data (images + stats), and generate a professional
    PDF catalog showing only cards available for sale.
    """
    console.print(Panel.fit("Poke MerKdo - Catalog Generator", style="bold magenta"))

    if not csv_file.exists():
        console.print(f"[red]X[/red] CSV file not found: {csv_file}")
        raise typer.Exit(1)

    console.print(f"\n[cyan]Parsing collection from:[/cyan] {csv_file}")
    console.print("Loading CSV...")
    parser = CSVParser(csv_file)
    collection = parser.parse()

    console.print(
        f"[green]OK[/green] Loaded {collection.total_unique_cards()} unique cards "
        f"({collection.total_cards()} total with duplicates)"
    )

    _load_custom_prices(collection)

    saleable = collection.get_saleable_cards()
    console.print(
        f"[yellow]>[/yellow]  Found [bold]{len(saleable)}[/bold] saleable cards "
        f"({collection.total_saleable_cards()} total copies)"
    )

    if not saleable:
        console.print("[red]No cards with quantity >= 2 found. Nothing to sell![/red]")
        raise typer.Exit(0)

    if enrich:
        console.print("\n[cyan]Enriching cards with TCGdex API...[/cyan]")
        console.print(
            "[yellow]Using TCGdex SDK (sets actualizados: "
            "Phantasmal Flames, Journey Together, etc.)...[/yellow]"
        )

        cards_to_enrich = [sc.card for sc in saleable]

        console.print(f"[cyan]Processing {len(saleable)} cards with TCGdex...[/cyan]")

        found, not_found = enrich_cards_sync(
            cards=cards_to_enrich, language="en", show_progress=False
        )

        console.print(f"\n[cyan]Results:[/cyan] {found} found, {not_found} not found")
        console.print("[dim]TCGdex SDK - includes latest sets[/dim]")

    console.print("\n[cyan]Generating PDF catalog...[/cyan]")
    if not output:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        output = CATALOG_DIR / f"catalog_{timestamp}.pdf"

    cache = ImageCache()
    generator = PDFGenerator(cache)

    try:
        output_path = generator.generate_catalog(
            collection=collection,
            output_path=output,
            title=title,
            include_stats=include_stats,
            show_prices=show_prices,
        )

        console.print(
            f"\n[bold green]OK - Success![/bold green] Catalog generated: {output_path}"
        )

        total_value = collection.total_collection_value()
        console.print(f"\n[bold]Total catalog value:[/bold] ${total_value:.2f}")

    except Exception as e:
        console.print(f"[red]X Error generating PDF:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def list_cards(
    csv_file: Path = typer.Option(
        COLLECTION_CSV,
        "--csv",
        "-c",
        help="Path to collection CSV file",
    ),
    saleable_only: bool = typer.Option(
        False,
        "--saleable",
        "-s",
        help="Show only saleable cards (quantity >= 2)",
    ),
    set_filter: str | None = typer.Option(
        None,
        "--set",
        help="Filter by set name",
    ),
) -> None:
    """List all cards in collection"""
    parser = CSVParser(csv_file)
    collection = parser.parse()

    _load_custom_prices(collection)

    if saleable_only:
        cards = [sc.card for sc in collection.get_saleable_cards()]
        title = f"Saleable Cards ({len(cards)})"
    else:
        cards = list(collection.cards)
        title = f"All Cards ({len(cards)})"

    if set_filter:
        cards = [c for c in cards if set_filter.lower() in c.console_name.lower()]
        title += f" - Set: {set_filter}"

    table = Table(title=title, show_header=True, header_style="bold magenta")
    table.add_column("Name", style="cyan", no_wrap=False)
    table.add_column("Set", style="dim")
    table.add_column("Qty", justify="right", style="yellow")
    table.add_column("Price", justify="right", style="green")
    table.add_column("Total", justify="right", style="bold green")

    for card in cards:
        qty_for_sale = max(0, card.quantity - 1) if card.quantity >= 2 else 0
        total = card.price_dollars * qty_for_sale if qty_for_sale > 0 else Decimal(0)

        table.add_row(
            card.card_name,
            card.console_name[:30],
            str(qty_for_sale) if qty_for_sale > 0 else "-",
            f"${card.price_dollars:.2f}",
            f"${total:.2f}" if total > 0 else "-",
        )

    console.print(table)


@app.command()
def set_price(
    card_name: str = typer.Argument(..., help="Card name to update"),
    price: float = typer.Argument(..., help="New price in dollars"),
    csv_file: Path = typer.Option(
        COLLECTION_CSV,
        "--csv",
        "-c",
        help="Path to collection CSV file",
    ),
) -> None:
    """Set custom price for a card"""
    parser = CSVParser(csv_file)
    collection = parser.parse()

    matches = [
        c for c in collection.cards if card_name.lower() in c.product_name.lower()
    ]

    if not matches:
        console.print(f"[red]X[/red] No cards found matching: {card_name}")
        raise typer.Exit(1)

    if len(matches) > 1:
        console.print(f"[yellow]Found {len(matches)} matching cards:[/yellow]")
        for i, card in enumerate(matches, 1):
            console.print(f"  {i}. {card.product_name} ({card.console_name})")

        choice = typer.prompt("Select card number", type=int)
        if choice < 1 or choice > len(matches):
            console.print("[red]Invalid selection[/red]")
            raise typer.Exit(1)

        selected_card = matches[choice - 1]
    else:
        selected_card = matches[0]

    prices = {}
    if PRICES_JSON.exists():
        with open(PRICES_JSON) as f:
            prices = json_load(f)

    prices[selected_card.id] = float(price)

    PRICES_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(PRICES_JSON, "w") as f:
        json_dump(prices, f, indent=2)

    console.print(
        f"[green]OK[/green] Updated price for "
        f"[cyan]{selected_card.product_name}[/cyan]: ${price:.2f}"
    )


@app.command()
def stats(
    csv_file: Path = typer.Option(
        COLLECTION_CSV,
        "--csv",
        "-c",
        help="Path to collection CSV file",
    ),
) -> None:
    """Show collection statistics"""
    parser = CSVParser(csv_file)
    collection = parser.parse()

    _load_custom_prices(collection)

    saleable = collection.get_saleable_cards()

    table = Table(title="Collection Statistics", show_header=False)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="yellow")

    table.add_row("Total unique cards", str(collection.total_unique_cards()))
    table.add_row("Total cards (with duplicates)", str(collection.total_cards()))
    table.add_row("Saleable cards (unique)", str(len(saleable)))
    table.add_row(
        "Saleable cards (total copies)", str(collection.total_saleable_cards())
    )
    table.add_row("Total catalog value", f"${collection.total_collection_value():.2f}")

    console.print(table)

    sets = collection.get_unique_sets()
    console.print(f"\n[cyan]Sets in collection:[/cyan] {len(sets)}")
    for set_name in sets:
        set_cards = collection.get_cards_by_set(set_name)
        console.print(f"  • {set_name}: {len(set_cards)} cards")


@app.command()
def clear_cache() -> None:
    """Clear image cache"""
    cache = ImageCache()
    size_before = cache.get_cache_size()

    cache.clear_cache()
    console.print(
        f"[green]OK[/green] Cache cleared ({size_before / 1024 / 1024:.2f} MB freed)"
    )


def _load_custom_prices(collection: Collection) -> None:
    """Load custom prices from JSON file"""
    if not PRICES_JSON.exists():
        return

    try:
        with open(PRICES_JSON) as f:
            prices = json_load(f)

        for card in collection.cards:
            if card.id in prices:
                card.custom_price = Decimal(str(prices[card.id]))

    except Exception as e:
        console.print(f"[yellow]Warning: Could not load custom prices: {e}[/yellow]")


if __name__ == "__main__":
    app()
