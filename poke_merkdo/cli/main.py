"""Main CLI application"""

from datetime import datetime
from decimal import Decimal
from json import dump as json_dump
from json import load as json_load
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn, TimeElapsedColumn
from rich.table import Table

from poke_merkdo.api.tcgdex_enricher import enrich_cards_sync
from poke_merkdo.cache import ImageCache
from poke_merkdo.config import (
    CATALOG_DIR,
    CATALOG_TITLE,
    COLLECTION_CSV,
    CONFIG_JSON,
    LOGS_DIR,
    PRICES_JSON,
    get_config,
    update_config,
)
from poke_merkdo.generators import PDFGenerator
from poke_merkdo.models import Card, Collection, SaleableCard
from poke_merkdo.parsers import CSVParser

app = typer.Typer(
    name="poke-merkdo",
    help="Professional PDF catalog generator for Pokémon TCG cards.",
    add_completion=False,
    no_args_is_help=True,
)
console = Console(legacy_windows=True, force_terminal=True)


@app.command()
def generate(  # noqa: PLR0913
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output PDF path",
        show_default="catalogs/catalog_DATE.pdf",
    ),
    csv_file: Path = typer.Option(
        COLLECTION_CSV,
        "--csv",
        "-c",
        help="Path to collection CSV file",
        show_default=True,
    ),
    enrich: bool = typer.Option(
        False,
        "--enrich/--no-enrich",
        help="Download images from TCGdex API",
        show_default=True,
    ),
    include_stats: bool = typer.Option(
        True,
        "--stats/--no-stats",
        help="Include card statistics in PDF",
        show_default=True,
    ),
    show_prices: bool = typer.Option(
        False,
        "--prices/--no-prices",
        help="Show prices in PDF",
        show_default=True,
    ),
    title: str = typer.Option(
        CATALOG_TITLE,
        "--title",
        "-t",
        help="Catalog title",
        show_default=True,
    ),
    all_cards: bool = typer.Option(
        False,
        "--all/--saleable",
        "-a",
        help="Include ALL cards",
        show_default="only qty >= 2",
    ),
    min_quantity: int = typer.Option(
        2,
        "--min-qty",
        "-m",
        help="Minimum quantity to include",
        show_default=True,
    ),
    sort_by: str = typer.Option(
        "set",
        "--sort",
        "-s",
        help="Sort cards by: set (collection + number), name, price",
        show_default=True,
    ),
) -> None:
    """Generate a PDF catalog of cards.

    By default only includes saleable cards (qty >= 2).
    Use --all to include ALL cards, or --min-qty for a custom minimum.
    Cards are sorted by set and number by default.
    """
    console.print(Panel.fit("Poke MerKdo - Catalog Generator", style="bold magenta"))

    if not csv_file.exists():
        console.print(f"[red]X[/red] CSV file not found: {csv_file}")
        raise typer.Exit(1)

    steps = ["Loading CSV", "Processing cards", "Generating PDF", "Finalizing"]
    if enrich:
        steps = [
            "Loading CSV",
            "Processing cards",
            "Enriching with TCGdex",
            "Generating PDF",
            "Finalizing",
        ]

    total_steps = len(steps)

    with Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=40),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    ) as progress:
        main_task = progress.add_task("Overall progress", total=total_steps)
        current_step = 0

        progress.update(main_task, description=f"[cyan]{steps[current_step]}...")
        parser = CSVParser(csv_file)
        collection = parser.parse()
        _load_custom_prices(collection)
        current_step += 1
        progress.update(main_task, completed=current_step)

        progress.update(main_task, description=f"[cyan]{steps[current_step]}...")
        if all_cards:
            min_quantity = 1
        saleable = collection.get_cards_by_min_quantity(min_quantity)

        saleable = _sort_cards(saleable, sort_by)

        if not saleable:
            progress.stop()
            console.print(f"[red]No cards with quantity >= {min_quantity} found.[/red]")
            raise typer.Exit(0)
        current_step += 1
        progress.update(main_task, completed=current_step)

        not_found_cards: list[Card] = []
        if enrich:
            progress.update(main_task, description=f"[cyan]{steps[current_step]}...")
            cards_to_enrich = [sc.card for sc in saleable]
            found, not_found, not_found_cards = enrich_cards_sync(
                cards=cards_to_enrich,
                language="en",
                show_progress=False,
                max_concurrent=20,
            )
            current_step += 1
            progress.update(main_task, completed=current_step)

        progress.update(main_task, description=f"[cyan]{steps[current_step]}...")
        if not output:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            output = CATALOG_DIR / f"catalog_{timestamp}.pdf"

        cache = ImageCache()
        generator = PDFGenerator(cache)
        pdf_warnings: list[str] = []

        try:
            output_path, pdf_warnings = generator.generate_catalog(
                collection=collection,
                output_path=output,
                title=title,
                include_stats=include_stats,
                show_prices=show_prices,
                saleable_cards=saleable,
                show_progress=False,
            )
            current_step += 1
            progress.update(main_task, completed=current_step)

            progress.update(main_task, description=f"[cyan]{steps[current_step]}...")
            current_step += 1
            progress.update(
                main_task, completed=current_step, description="[green]Complete!"
            )

        except Exception as e:
            progress.stop()
            console.print(f"[red]X Error generating PDF:[/red] {e}")
            raise typer.Exit(1)

    for warning in pdf_warnings:
        console.print(f"[yellow]Warning:[/yellow] {warning}")

    console.print(
        f"\n[green]OK[/green] Loaded {collection.total_unique_cards()} unique cards ({collection.total_cards()} total)"
    )

    if min_quantity == 1:
        console.print(
            f"[green]OK[/green] Included [bold]{len(saleable)}[/bold] cards (ALL)"
        )
    else:
        console.print(
            f"[green]OK[/green] Found [bold]{len(saleable)}[/bold] saleable cards (qty >= {min_quantity})"
        )

    if enrich:
        console.print(
            f"[green]OK[/green] Enriched: {found} found, {not_found} not found"
        )
        if not_found_cards:
            log_file = (
                LOGS_DIR / f"not_found_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.txt"
            )
            with open(log_file, "w", encoding="utf-8") as f:
                f.write(
                    f"Cards not found - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                )
                f.write(f"Total: {not_found}\n")
                f.write("-" * 50 + "\n\n")
                for card in not_found_cards:
                    f.write(
                        f"{card.card_name} | {card.console_name} | #{card.card_number}\n"
                    )
            console.print("[yellow]  Not found (first 10):[/yellow]")
            for card in not_found_cards[:10]:
                console.print(f"    - {card.card_name} ({card.console_name})")
            if len(not_found_cards) > 10:
                console.print(
                    f"[dim]    ... and {len(not_found_cards) - 10} more (see {log_file.name})[/dim]"
                )

    console.print(f"\n[bold green]Success![/bold green] Catalog: {output_path}")

    total_value = sum((card.price_dollars for card in collection.cards), Decimal(0))
    console.print(f"[bold]Total collection value:[/bold] ${total_value:.2f}")


@app.command()
def list_cards(
    csv_file: Path = typer.Option(
        COLLECTION_CSV,
        "--csv",
        "-c",
        help="Path to collection CSV file",
        show_default=True,
    ),
    saleable_only: bool = typer.Option(
        False,
        "--saleable",
        "-s",
        help="Show only saleable cards (qty >= 2)",
        show_default=True,
    ),
    set_filter: str | None = typer.Option(
        None,
        "--set",
        help="Filter by set name",
        show_default=True,
    ),
) -> None:
    """List all cards in collection."""
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
    card_name: str = typer.Argument(..., help="Card name to search"),
    price: float = typer.Argument(..., help="New price in dollars"),
    csv_file: Path = typer.Option(
        COLLECTION_CSV,
        "--csv",
        "-c",
        help="Path to collection CSV file",
        show_default=True,
    ),
) -> None:
    """Set custom price for a card."""
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
        show_default=True,
    ),
) -> None:
    """Show collection statistics."""
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
    """Clear image cache from data/cache/."""
    cache = ImageCache()
    size_before = cache.get_cache_size()

    cache.clear_cache()
    console.print(
        f"[green]OK[/green] Cache cleared ({size_before / 1024 / 1024:.2f} MB freed)"
    )


@app.command()
def config(
    key: str | None = typer.Argument(
        None,
        help="Configuration key to view or set",
    ),
    value: str | None = typer.Argument(
        None,
        help="New value to set (optional)",
    ),
) -> None:
    """View or edit store configuration.

    Without arguments: show all settings.
    With key: show specific setting.
    With key and value: update setting.

    Available keys:
      store_name, catalog_title, logo_path,
      welcome_message, contact_message

    For social networks, edit data/config.json directly.
    """
    current_config = get_config()

    if key is None:
        console.print(Panel.fit("Store Configuration", style="bold magenta"))
        console.print(f"[dim]Config file: {CONFIG_JSON}[/dim]\n")

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Key", style="yellow")
        table.add_column("Value", style="green")

        for k, v in current_config.items():
            if k == "social_networks":
                table.add_row(k, f"[{len(v)} networks]")
            else:
                display_value = str(v)
                if len(display_value) > 50:
                    display_value = display_value[:47] + "..."
                table.add_row(k, display_value)

        console.print(table)

        networks = current_config.get("social_networks", [])
        if networks:
            console.print("\n[bold cyan]Social Networks:[/bold cyan]")
            for i, net in enumerate(networks, 1):
                console.print(
                    f"  {i}. [yellow]{net.get('platform', '')}[/yellow]: {net.get('handle', '')} ({net.get('url', '')})"
                )

        console.print(
            "\n[dim]Use 'poke-merkdo config <key> <value>' to update a setting[/dim]"
        )
        console.print("[dim]For social networks, edit data/config.json directly[/dim]")

    elif value is None:
        if key in current_config:
            val = current_config[key]
            if key == "social_networks":
                console.print(f"[cyan]{key}[/cyan]:")
                for i, net in enumerate(val, 1):
                    console.print(
                        f"  {i}. [yellow]{net.get('platform', '')}[/yellow]: {net.get('handle', '')} ({net.get('url', '')})"
                    )
            else:
                console.print(f"[cyan]{key}[/cyan] = [green]{val}[/green]")
        else:
            console.print(f"[red]Unknown key:[/red] {key}")
            console.print(
                f"[dim]Available keys: {', '.join(current_config.keys())}[/dim]"
            )
            raise typer.Exit(1)

    else:
        if key not in current_config:
            console.print(f"[red]Unknown key:[/red] {key}")
            console.print(
                f"[dim]Available keys: {', '.join(current_config.keys())}[/dim]"
            )
            raise typer.Exit(1)

        if key == "social_networks":
            console.print("[yellow]Cannot update social_networks via CLI.[/yellow]")
            console.print(
                f"[dim]Edit {CONFIG_JSON} directly to add/remove social networks.[/dim]"
            )
            raise typer.Exit(1)

        old_value = current_config[key]
        update_config(key, value)
        console.print(f"[green]OK[/green] Updated [cyan]{key}[/cyan]")
        console.print(f"  [dim]Old:[/dim] {old_value}")
        console.print(f"  [green]New:[/green] {value}")


def _sort_cards(cards: list[SaleableCard], sort_by: str) -> list[SaleableCard]:
    """Sort cards by specified criteria.

    Args:
        cards: List of saleable cards
        sort_by: Sort method - 'set' (collection + number), 'name', 'price'

    Returns:
        Sorted list of cards
    """
    if sort_by == "name":
        return sorted(cards, key=lambda sc: sc.card.card_name.lower())

    if sort_by == "price":
        return sorted(cards, key=lambda sc: sc.card.price_dollars, reverse=True)

    def set_sort_key(sc: SaleableCard) -> tuple[str, int]:
        card = sc.card
        num = 0
        if card.card_number:
            digits = "".join(c for c in card.card_number if c.isdigit())
            num = int(digits) if digits else 0
        return (card.console_name.lower(), num)

    return sorted(cards, key=set_sort_key)


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
