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
| `config` | View or edit store configuration |

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
 Cards are sorted by set and number by default.

Options:
  -o, --output PATH          Output PDF path  [default: catalogs/catalog_DATE.pdf]
  -c, --csv PATH             Path to collection CSV file  [default: collection.csv]
  --enrich / --no-enrich     Download images from TCGdex API  [default: no-enrich]
  --stats / --no-stats       Include card statistics in PDF  [default: stats]
  --prices / --no-prices     Show prices in PDF  [default: no-prices]
  -t, --title TEXT           Catalog title  [default: Poke MerKdo - Catálogo de Cartas]
  -a, --all / --saleable     Include ALL cards  [default: only qty >= 2]
  -m, --min-qty INTEGER      Minimum quantity to include  [default: 2]
  -s, --sort TEXT            Sort by: set (collection + number), name, price  [default: set]
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

# Sort by set and card number (default)
poke-merkdo generate --enrich --sort set

# Sort by card name
poke-merkdo generate --enrich --sort name

# Sort by price (highest first)
poke-merkdo generate --enrich --sort price

# List all saleable cards
poke-merkdo list-cards --saleable

# List cards from a specific set
poke-merkdo list-cards --set "Prismatic Evolutions"

# Clear image cache
poke-merkdo clear-cache

# View store configuration
poke-merkdo config

# Update a setting
poke-merkdo config store_name "My Pokemon Store"

#My favorite command
poke-merkdo generate --enrich --all
```

## Store Configuration

Customize your store's branding by editing `data/config.json`.

### How It Works

- On first run, an empty `data/config.json` is created automatically
- If empty (`{}`), default values are used (Poke MerKdo branding)
- Add only the fields you want to customize
- Missing fields use defaults

```json
{
  "store_name": "My Pokemon Store",
  "catalog_title": "My Pokemon Store - Card Catalog",
  "logo_path": "data/images/logo/my_logo.png",
  "social_networks": [
    {
      "platform": "Instagram",
      "handle": "@my_store",
      "url": "https://www.instagram.com/my_store/"
    },
    {
      "platform": "WhatsApp",
      "handle": "+57 300 000 0000",
      "url": "https://wa.me/573000000000?text=Hi%2C%20I%27m%20interested%20in%20a%20card"
    }
  ],
  "welcome_message": "Welcome to our Pokémon TCG catalog.",
  "contact_message": "Contact us for prices and availability."
}
```

### Configuration Options

| Key | Description | Example |
|-----|-------------|---------|
| `store_name` | Your store name | `"Pokemon Shop"` |
| `catalog_title` | PDF catalog title | `"Pokemon Shop - Catalog"` |
| `logo_path` | Path to logo image (relative to project) | `"data/images/logo/logo.png"` |
| `social_networks` | List of social media accounts | See below |
| `welcome_message` | Welcome text on PDF cover | `"Welcome to our catalog"` |
| `contact_message` | Contact instructions | `"DM us for prices"` |

### Social Networks

Add multiple social networks to your catalog:

```json
"social_networks": [
  {
    "platform": "Instagram",
    "handle": "@my_store",
    "url": "https://www.instagram.com/my_store/"
  },
  {
    "platform": "Facebook",
    "handle": "My Pokemon Store",
    "url": "https://www.facebook.com/mystore"
  },
  {
    "platform": "WhatsApp",
    "handle": "+57 300 000 0000",
    "url": "https://wa.me/573000000000?text=Hello"
  },
  {
    "platform": "TikTok",
    "handle": "@my_store",
    "url": "https://www.tiktok.com/@my_store"
  }
]
```

**Supported platforms with icons:**
- Instagram 📸
- Facebook 📘
- WhatsApp 📱
- Twitter/X 🐦
- TikTok 🎵
- YouTube 📺
- Telegram ✈️
- Others 🔗

### WhatsApp Link Format

For WhatsApp with a pre-filled message:

```
https://wa.me/PHONENUMBER?text=URL_ENCODED_MESSAGE
```

Example (Colombian number +57 300 000 0000):
```
https://wa.me/573000000000?text=Hola%2C%20me%20interesa%20una%20carta
```

**URL encode your message:** Replace spaces with `%20`, commas with `%2C`, etc.

### CLI Commands

```bash
# View all settings
poke-merkdo config

# View specific setting
poke-merkdo config store_name

# Update setting (not for social_networks)
poke-merkdo config store_name "New Name"
poke-merkdo config welcome_message "Welcome!"

# For social networks, edit data/config.json directly
```

## Project Structure

```
poke-merkdo/
├── poke_merkdo/
│   ├── api/                 # TCGdex client
│   ├── cache/               # Image cache
│   ├── cli/                 # CLI commands
│   ├── config/              # Configuration module
│   │   ├── paths.py         # Path constants
│   │   ├── constants.py     # Fixed constants
│   │   └── store.py         # Store configuration
│   ├── generators/          # PDF generator
│   ├── models/              # Data models
│   └── parsers/             # CSV parser
├── catalogs/                # Generated PDFs
├── data/
│   ├── cache/               # Cached images
│   ├── logs/                # Not-found card logs
│   ├── images/logo/         # Store logo
│   └── config.json          # Your store config (auto-created, edit to customize)
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
