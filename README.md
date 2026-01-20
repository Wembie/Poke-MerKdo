# Poke MerKdo

Generador profesional de catálogos PDF para cartas Pokémon TCG.

Parsea tu colección exportada desde PriceCharting, enriquece las cartas con imágenes de alta calidad usando la API de [TCGdex](https://tcgdex.dev/), y genera un PDF listo para compartir con clientes.

## Características

- **Parseo de CSV** - Importa tu colección desde PriceCharting
- **Enriquecimiento automático** - Descarga imágenes HD de TCGdex
- **PDF profesional** - Grid de 3x3 cartas por página con imágenes
- **Caché de imágenes** - No vuelve a descargar imágenes ya obtenidas
- **Precios ocultos** - Por defecto sin precios (clientes preguntan)
- **Sets actualizados** - Soporta los sets más recientes:
  - Phantasmal Flames (me02)
  - Journey Together (sv09)
  - Prismatic Evolutions (sv08.5)
  - Destined Rivals (sv10)
  - Y más...

## Instalación

### Requisitos

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recomendado) o pip

### Con uv (recomendado)

```bash
git clone https://github.com/tu-usuario/poke-merkdo.git
cd poke-merkdo
uv sync
uv run poke-merkdo --help
```

### Con pip

```bash
git clone https://github.com/tu-usuario/poke-merkdo.git
cd poke-merkdo
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac
pip install -e .
poke-merkdo --help
```

## Uso

### Comandos principales

```bash
# Ver estadísticas de tu colección
poke-merkdo stats

# Generar catálogo SIN imágenes (tabla compacta)
poke-merkdo generate

# Generar catálogo CON imágenes (recomendado)
poke-merkdo generate --enrich

# Con precios visibles
poke-merkdo generate --enrich --prices

# Especificar archivo de salida
poke-merkdo generate --enrich -o mi_catalogo.pdf
```

### Opciones de `generate`

| Opción | Descripción | Default |
|--------|-------------|---------|
| `--enrich` | Descargar imágenes de TCGdex | No |
| `--prices` | Mostrar precios en el PDF | No |
| `--csv, -c` | Ruta al archivo CSV | `collection.csv` |
| `--output, -o` | Ruta del PDF de salida | `catalogs/catalog_FECHA.pdf` |
| `--title, -t` | Título del catálogo | "Poke MerKdo - Catálogo de Cartas" |
| `--stats/--no-stats` | Incluir estadísticas | Sí |
| `--all, -a` | Incluir TODAS las cartas | No (solo qty >= 2) |
| `--min-qty, -m` | Cantidad mínima para incluir | 2 |

### Ejemplos

```bash
# Catálogo básico con imágenes (solo cartas con qty >= 2)
uv run poke-merkdo generate --enrich

# Catálogo con TODAS las cartas
uv run poke-merkdo generate --enrich --all

# Catálogo con cartas qty >= 3
uv run poke-merkdo generate --enrich --min-qty 3

# Catálogo con título personalizado
uv run poke-merkdo generate --enrich --title "Mi Tienda Pokemon"

# Desde un CSV específico
uv run poke-merkdo generate --enrich --csv exports/mi_coleccion.csv

# Catálogo interno con precios
uv run poke-merkdo generate --enrich --prices -o interno.pdf
```

## Estructura del proyecto

```
poke-merkdo/
├── poke_merkdo/
│   ├── api/                 # Cliente TCGdex
│   │   └── tcgdex_enricher.py
│   ├── cache/               # Caché de imágenes
│   ├── cli/                 # Comandos CLI
│   ├── generators/          # Generador de PDF
│   ├── models/              # Modelos de datos
│   └── parsers/             # Parser de CSV
├── catalogs/                # PDFs generados
├── data/cache/              # Imágenes cacheadas
├── collection.csv           # Tu colección
└── pyproject.toml
```

## Formato del CSV

Exporta tu colección desde [PriceCharting](https://www.pricecharting.com/) con estas columnas:

| Columna | Descripción |
|---------|-------------|
| `quantity` | Cantidad de copias |
| `product-name` | Nombre completo |
| `console-name` | Expansión |
| `id` | ID único de la carta |
| `upc` | Código UPC |
| `asin` | Código ASIN |
| `loose-price` | Precio USD |

## Lógica de ventas

- **Cantidad >= 2**: Carta disponible para venta
- **Cantidad = 1**: Se mantiene en colección
- **Para venta = Total - 1**: Siempre guardas 1 copia

Ejemplo: 5 copias de "Charizard" → 4 disponibles para venta

## Sets soportados

### Scarlet & Violet
| ID | Nombre |
|----|--------|
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
| me02 | Phantasmal Flames |
| svp | SV Promos |

### Sword & Shield
- swsh01-swsh12, swsh12.5 (Crown Zenith)
- pgo: Pokémon Go

## Notas

- Las **energías básicas** no se enriquecen (no tienen sets en TCGdex)
- Solo aparecen cartas con **cantidad >= 2**
- Imágenes se cachean en `data/cache/`
- PDFs se generan en `catalogs/`

## Tecnologías

- [Typer](https://typer.tiangolo.com/) - CLI
- [Rich](https://rich.readthedocs.io/) - Terminal
- [Pydantic](https://docs.pydantic.dev/) - Validación
- [ReportLab](https://www.reportlab.com/) - PDF
- [TCGdex SDK](https://github.com/tcgdex/python-sdk) - API de cartas
- [Pandas](https://pandas.pydata.org/) - CSV

## Licencia

MIT
