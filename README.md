# Poke MerKdo

Professional PDF catalog generator for Pokémon TCG cards.

Parse your collection exported from PriceCharting, enrich cards with high-quality images using the [TCGdex](https://tcgdex.dev/) API, and generate a PDF ready to share with customers.

## Features

- **CSV Parsing** - Import your collection from PriceCharting
- **Auto Enrichment** - Download HD images from TCGdex (parallel processing)
- **Professional PDF** - 3x3 card grid per page with images
- **Image Cache** - Won't re-download already fetched images
- **Hidden Prices** - No prices by default (customers ask for them)
- **Dynamic Set Mapping** - Automatically fetches set IDs from TCGdex API
- **Not-Found Logging** - Cards not found are saved to log files
- **Latest Sets Supported**:
  - Phantasmal Flames (me02)
  - Journey Together (sv09)
  - Prismatic Evolutions (sv08.5)
  - Destined Rivals (sv10)
  - Mega Evolution (me01)
  - And more...

## Installation

### Requirements

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### With uv (recommended)

```bash
git clone https://github.com/Wembie/Poke-MerKdo.git
cd Poke-MerKdo
uv sync
uv run poke-merkdo --help
```

### With pip

```bash
git clone https://github.com/Wembie/Poke-MerKdo.git
cd Poke-MerKdo
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac
pip install -e .
poke-merkdo --help
```

## Usage

### Available Commands

| Command | Description |
|---------|-------------|
| `generate` | Generate PDF catalog of cards |
| `list-cards` | List all cards in collection |
| `set-price` | Set custom price for a card |
| `stats` | Show collection statistics |
| `clear-cache` | Clear image cache |

### Quick Start

```bash
# Show all available commands
poke-merkdo --help

# Show collection statistics
poke-merkdo stats

# Generate catalog WITHOUT images (compact table)
poke-merkdo generate

# Generate catalog WITH images (recommended)
poke-merkdo generate --enrich

# With visible prices
poke-merkdo generate --enrich --prices

# Specify output file
poke-merkdo generate --enrich -o my_catalog.pdf
```

### `generate --help`

```
Usage: poke-merkdo generate [OPTIONS]

 Generate a PDF catalog of cards.

 By default only includes saleable cards (qty >= 2).
 Use --all to include ALL cards, or --min-qty for a custom minimum.

Options:
  -o, --output PATH          Output PDF path  [default: catalogs/catalog_DATE.pdf]
  -c, --csv PATH             Path to collection CSV file  [default: collection.csv]
  --enrich / --no-enrich     Download images from TCGdex API  [default: no-enrich]
  --stats / --no-stats       Include card statistics in PDF  [default: stats]
  --prices / --no-prices     Show prices in PDF  [default: no-prices]
  -t, --title TEXT           Catalog title  [default: Poke MerKdo - Catálogo de Cartas]
  -a, --all / --saleable     Include ALL cards  [default: only qty >= 2]
  -m, --min-qty INTEGER      Minimum quantity to include  [default: 2]
  --help                     Show this message and exit.
```

### `list-cards --help`

```
Usage: poke-merkdo list-cards [OPTIONS]

 List all cards in collection.

Options:
  -c, --csv PATH    Path to collection CSV file  [default: collection.csv]
  -s, --saleable    Show only saleable cards (qty >= 2)
  --set TEXT        Filter by set name
  --help            Show this message and exit.
```

### `set-price --help`

```
Usage: poke-merkdo set-price [OPTIONS] CARD_NAME PRICE

 Set custom price for a card.

Arguments:
  CARD_NAME  Card name to search  [required]
  PRICE      New price in dollars  [required]

Options:
  -c, --csv PATH  Path to collection CSV file  [default: collection.csv]
  --help          Show this message and exit.
```

### Examples

```bash
# Basic catalog with images (only cards with qty >= 2)
poke-merkdo generate --enrich

# Catalog with ALL cards
poke-merkdo generate --enrich --all

# Catalog with cards qty >= 3
poke-merkdo generate --enrich --min-qty 3

# Catalog with custom title
poke-merkdo generate --enrich --title "My Pokemon Store"

# From a specific CSV
poke-merkdo generate --enrich --csv exports/my_collection.csv

# Internal catalog with prices
poke-merkdo generate --enrich --prices -o internal.pdf

# List all saleable cards
poke-merkdo list-cards --saleable

# List cards from a specific set
poke-merkdo list-cards --set "Prismatic Evolutions"

# Clear image cache
poke-merkdo clear-cache
```

## Project Structure

```
poke-merkdo/
├── poke_merkdo/
│   ├── api/                 # TCGdex client
│   │   └── tcgdex_enricher.py
│   ├── cache/               # Image cache
│   ├── cli/                 # CLI commands
│   ├── generators/          # PDF generator
│   ├── models/              # Data models
│   └── parsers/             # CSV parser
├── catalogs/                # Generated PDFs
├── data/
│   ├── cache/               # Cached images
│   └── logs/                # Not-found card logs
├── collection.csv           # Your collection
└── pyproject.toml
```

## CSV Format

Export your collection from [PriceCharting](https://www.pricecharting.com/) with these columns:

| Column | Description |
|--------|-------------|
| `quantity` | Number of copies |
| `product-name` | Full card name |
| `console-name` | Set/Expansion name |
| `id` | Unique card ID |
| `price-in-pennies` | Total price in cents (price × quantity) |

## Sales Logic

- **Quantity >= 2**: Card available for sale
- **Quantity = 1**: Kept in collection
- **For sale = Total - 1**: You always keep 1 copy

Example: 5 copies of "Charizard" → 4 available for sale

## Supported Sets

### Scarlet & Violet
| ID | Name |
|----|------|
| sv01 | Scarlet & Violet |
| sv02 | Paldea Evolved |
| sv03 | Obsidian Flames |
| sv03.5 | 151 |
| sv04 | Paradox Rift |
| sv04.5 | Paldean Fates |
| sv05 | Temporal Forces |
| sv06 | Twilight Masquerade |
| sv06.5 | Shrouded Fable |
| sv07 | Stellar Crown |
| sv08 | Surging Sparks |
| sv08.5 | Prismatic Evolutions |
| sv09 | Journey Together |
| sv10 | Destined Rivals |
| me01 | Mega Evolution |
| me02 | Phantasmal Flames |
| svp | SV Promos |

### Sword & Shield
- swsh01-swsh12, swsh12.5 (Crown Zenith)
- pgo: Pokémon Go

## Notes

- **Basic energies** are not enriched (no sets in TCGdex)
- By default, only cards with **quantity >= 2** appear
- Images are cached in `data/cache/`
- PDFs are generated in `catalogs/`
- Cards not found are logged in `data/logs/`

## Technologies

- [Typer](https://typer.tiangolo.com/) - CLI framework
- [Rich](https://rich.readthedocs.io/) - Terminal formatting
- [Pydantic](https://docs.pydantic.dev/) - Data validation
- [ReportLab](https://www.reportlab.com/) - PDF generation
- [TCGdex SDK](https://github.com/tcgdex/python-sdk) - Card API
- [aiohttp](https://docs.aiohttp.org/) - Async HTTP requests

## License

MIT
