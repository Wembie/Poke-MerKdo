"""PDF catalog generator with grid layout"""

from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.flowables import Image as RLImage
from rich.console import Console
from rich.progress import track

from poke_merkdo.cache import ImageCache
from poke_merkdo.config import AUTHOR, INSTAGRAM_HANDLE, INSTAGRAM_URL, LOGO_PATH
from poke_merkdo.models import Collection, SaleableCard

console = Console()


class PDFGenerator:
    """Generate professional PDF catalog of cards"""

    def __init__(self, cache: ImageCache | None = None):
        self.cache = cache or ImageCache()
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self) -> None:
        """Setup custom paragraph styles"""
        self.styles.add(
            ParagraphStyle(
                name="CardName",
                parent=self.styles["Normal"],
                fontSize=9,
                fontName="Helvetica-Bold",
                alignment=1,
                spaceAfter=2,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="CardPrice",
                parent=self.styles["Normal"],
                fontSize=10,
                fontName="Helvetica-Bold",
                textColor=colors.HexColor("#2E7D32"),
                alignment=1,
                spaceBefore=2,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="CardInfo",
                parent=self.styles["Normal"],
                fontSize=7,
                textColor=colors.grey,
                alignment=1,
            )
        )

    def generate_catalog(
        self,
        collection: Collection,
        output_path: Path,
        title: str = "Poke MerKdo - Catálogo de Cartas",
        include_stats: bool = True,
        show_prices: bool = False,
    ) -> Path:
        """Generate PDF catalog from collection"""
        saleable_cards = collection.get_saleable_cards()

        if not saleable_cards:
            console.print("[yellow]⚠️  No saleable cards found (quantity >= 2)[/yellow]")
            return output_path

        console.print(
            f"[cyan]Generating catalog for {len(saleable_cards)} cards...[/cyan]"
        )

        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
            author=AUTHOR,
            title=title,
            creator=f"Poke MerKdo - {AUTHOR}",
        )

        story = []

        story.extend(self._create_title_page(title, collection))
        story.append(PageBreak())

        has_images = any(sc.card.image_url for sc in saleable_cards)

        if has_images:
            cards_per_page = 9
            for i in track(
                range(0, len(saleable_cards), cards_per_page),
                description="Creating pages...",
            ):
                page_cards = saleable_cards[i : i + cards_per_page]
                page_content = self._create_card_page(
                    page_cards, include_stats, show_prices
                )
                story.extend(page_content)

                if i + cards_per_page < len(saleable_cards):
                    story.append(PageBreak())
        else:
            page_content = self._create_table_layout(saleable_cards, show_prices)
            story.extend(page_content)

        doc.build(story)
        console.print(f"[green]OK[/green] PDF generated: {output_path}")

        return output_path

    def _create_title_page(self, title: str, collection: Collection) -> list:
        """Create title page with summary"""
        elements = []

        if LOGO_PATH.exists():
            try:
                logo = RLImage(str(LOGO_PATH), width=2.5 * inch, height=2.5 * inch)
                elements.append(logo)
                elements.append(Spacer(1, 0.2 * inch))
            except Exception as e:
                console.print(f"[yellow]Warning: Could not load logo: {e}[/yellow]")

        title_style = ParagraphStyle(
            name="Title",
            parent=self.styles["Heading1"],
            fontSize=28,
            textColor=colors.HexColor("#D32F2F"),
            alignment=1,
            spaceAfter=10,
            fontName="Helvetica-Bold",
        )
        elements.append(Paragraph(title, title_style))

        subtitle_style = ParagraphStyle(
            name="Subtitle",
            parent=self.styles["Normal"],
            fontSize=14,
            textColor=colors.HexColor("#757575"),
            alignment=1,
            spaceAfter=30,
            fontName="Helvetica-Oblique",
        )
        elements.append(Paragraph("Cartas Pokémon TCG Disponibles", subtitle_style))
        elements.append(Spacer(1, 0.3 * inch))

        saleable = collection.get_saleable_cards()

        summary_data = [
            ["📦 Cartas únicas disponibles", str(len(saleable))],
            ["🎴 Total de unidades en stock", str(collection.total_saleable_cards())],
            ["📅 Catálogo actualizado", datetime.now().strftime("%d/%m/%Y")],
        ]

        summary_table = Table(summary_data, colWidths=[3.5 * inch, 2 * inch])
        summary_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#D32F2F")),
                    ("TEXTCOLOR", (0, 0), (0, -1), colors.white),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("BACKGROUND", (1, 0), (1, -1), colors.HexColor("#FFEBEE")),
                    ("TEXTCOLOR", (1, 0), (1, -1), colors.HexColor("#D32F2F")),
                    ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
                    ("ALIGN", (1, 0), (1, -1), "CENTER"),
                    ("FONTSIZE", (0, 0), (-1, -1), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
                    ("TOPPADDING", (0, 0), (-1, -1), 14),
                    ("BOX", (0, 0), (-1, -1), 2, colors.HexColor("#D32F2F")),
                    ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#FFCDD2")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )

        elements.append(summary_table)
        elements.append(Spacer(1, 0.4 * inch))

        welcome_style = ParagraphStyle(
            name="Welcome",
            parent=self.styles["Normal"],
            fontSize=11,
            textColor=colors.HexColor("#424242"),
            alignment=1,
            spaceAfter=10,
            leading=16,
        )
        welcome_text = (
            "Bienvenido a nuestro catálogo de cartas Pokémon TCG.<br/>"
            "Todas las cartas están en excelente condición y listas para entrega.<br/>"
            "<b>Para consultar precios y disponibilidad, contáctanos directamente.</b>"
        )
        elements.append(Paragraph(welcome_text, welcome_style))
        elements.append(Spacer(1, 0.2 * inch))

        contact_style = ParagraphStyle(
            name="Contact",
            parent=self.styles["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#D32F2F"),
            alignment=1,
            fontName="Helvetica-Bold",
        )
        contact_text = "📱 Consulta precios por WhatsApp o mensaje directo"
        elements.append(Paragraph(contact_text, contact_style))

        elements.append(Spacer(1, 0.3 * inch))

        ig_style = ParagraphStyle(
            name="Instagram",
            parent=self.styles["Normal"],
            fontSize=14,
            textColor=colors.HexColor("#E1306C"),
            alignment=1,
            fontName="Helvetica-Bold",
        )
        ig_text = (
            f'📸 Síguenos en Instagram: '
            f'<a href="{INSTAGRAM_URL}">{INSTAGRAM_HANDLE}</a>'
        )
        elements.append(Paragraph(ig_text, ig_style))

        elements.append(Spacer(1, 0.5 * inch))

        author_style = ParagraphStyle(
            name="Author",
            parent=self.styles["Normal"],
            fontSize=9,
            textColor=colors.HexColor("#9E9E9E"),
            alignment=1,
            fontName="Helvetica-Oblique",
        )
        author_text = f"Creado por {AUTHOR}"
        elements.append(Paragraph(author_text, author_style))

        return elements

    def _create_card_page(
        self, saleable_cards: list[SaleableCard], include_stats: bool, show_prices: bool
    ) -> list:
        """Create a page with 3x3 grid of cards"""
        elements = []

        rows = []
        for i in range(0, 9, 3):
            row = []
            for j in range(3):
                idx = i + j
                if idx < len(saleable_cards):
                    card_cell = self._create_card_cell(
                        saleable_cards[idx], include_stats, show_prices
                    )
                    row.append(card_cell)
                else:
                    row.append("")
            rows.append(row)

        col_width = 1.8 * inch
        table = Table(rows, colWidths=[col_width] * 3, rowHeights=[3 * inch] * 3)
        table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("BOX", (0, 0), (-1, -1), 1, colors.lightgrey),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ]
            )
        )

        elements.append(table)
        return elements

    def _create_card_cell(
        self, saleable_card: SaleableCard, include_stats: bool, show_prices: bool
    ) -> Table:
        """Create cell content for a single card as a nested table"""
        card = saleable_card.card
        cell_rows = []

        if card.image_url:
            image_path = self.cache.get_image(card.image_url, card.id)
            if image_path and image_path.exists():
                try:
                    img = RLImage(str(image_path), width=1.5 * inch, height=2.1 * inch)
                    cell_rows.append([img])
                except Exception as e:
                    console.print(
                        f"[red]Error loading image for {card.product_name}: {e}[/red]"
                    )

        name_text = f"<b>{card.card_name}</b>"
        if card.card_number:
            name_text += f" #{card.card_number}"
        cell_rows.append([Paragraph(name_text, self.styles["CardName"])])

        cell_rows.append(
            [Paragraph(f"<i>{card.console_name}</i>", self.styles["CardInfo"])]
        )

        if saleable_card.quantity_for_sale > 1:
            qty_text = f"Disponibles: {saleable_card.quantity_for_sale}"
        else:
            qty_text = "Disponible: 1"

        cell_rows.append([Paragraph(f"<b>{qty_text}</b>", self.styles["CardInfo"])])

        if show_prices:
            price_text = f"${card.price_dollars:.2f}"
            if saleable_card.quantity_for_sale > 1:
                price_text += f" × {saleable_card.quantity_for_sale}"
                total = saleable_card.total_value
                price_text += f" = <u>${total:.2f}</u>"

            cell_rows.append([Paragraph(price_text, self.styles["CardPrice"])])

        if include_stats and card.stats:
            stats_text = []
            if card.stats.hp:
                stats_text.append(f"HP: {card.stats.hp}")
            if card.stats.types:
                stats_text.append(f"Tipo: {', '.join(card.stats.types)}")
            if card.stats.rarity:
                stats_text.append(f"Rareza: {card.stats.rarity}")

            if stats_text:
                cell_rows.append(
                    [Paragraph(" | ".join(stats_text), self.styles["CardInfo"])]
                )

        cell_table = Table(cell_rows, colWidths=[1.7 * inch])
        cell_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )

        return cell_table

    def _create_table_layout(
        self, saleable_cards: list[SaleableCard], show_prices: bool
    ) -> list:
        """Create compact table layout for cards without images"""
        elements = []

        table_data = []

        if show_prices:
            headers = ["#", "Carta", "Colección", "Cantidad", "Precio", "Total"]
            col_widths = [
                0.4 * inch,
                2.5 * inch,
                1.8 * inch,
                0.8 * inch,
                0.8 * inch,
                0.9 * inch,
            ]
        else:
            headers = ["#", "Carta", "Colección", "Disponibles"]
            col_widths = [0.4 * inch, 3.2 * inch, 2.5 * inch, 1.1 * inch]

        table_data.append(headers)

        for idx, sc in enumerate(saleable_cards, 1):
            card = sc.card

            card_name = card.card_name
            if card.card_number:
                card_name += f" #{card.card_number}"

            set_name = card.console_name
            if len(set_name) > 30:
                set_name = set_name[:27] + "..."

            if show_prices:
                price = f"${card.price_dollars:.2f}"
                total = f"${sc.total_value:.2f}"
                row = [
                    str(idx),
                    card_name,
                    set_name,
                    str(sc.quantity_for_sale),
                    price,
                    total,
                ]
            else:
                qty_text = f"{sc.quantity_for_sale}"
                row = [str(idx), card_name, set_name, qty_text]

            table_data.append(row)

        table = Table(table_data, colWidths=col_widths, repeatRows=1)

        table_style = TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D32F2F")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 11),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 14),
                ("TOPPADDING", (0, 0), (-1, 0), 14),
                ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#212121")),
                ("ALIGN", (0, 1), (0, -1), "CENTER"),
                ("ALIGN", (-1, 1), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 9),
                ("TOPPADDING", (0, 1), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 1), (-1, -1), 10),
                ("LEFTPADDING", (0, 1), (-1, -1), 8),
                ("RIGHTPADDING", (0, 1), (-1, -1), 8),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#FFEBEE")],
                ),
                ("BACKGROUND", (-1, 1), (-1, -1), colors.HexColor("#FFF3E0")),
                ("TEXTCOLOR", (-1, 1), (-1, -1), colors.HexColor("#E65100")),
                ("FONTNAME", (-1, 1), (-1, -1), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#BDBDBD")),
                ("BOX", (0, 0), (-1, -1), 2, colors.HexColor("#D32F2F")),
                ("LINEBELOW", (0, 0), (-1, 0), 2, colors.HexColor("#B71C1C")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )

        table.setStyle(table_style)
        elements.append(table)

        if not show_prices:
            elements.append(Spacer(1, 0.4 * inch))

            footer_style = ParagraphStyle(
                name="Footer",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.HexColor("#D32F2F"),
                alignment=1,
                leading=14,
                fontName="Helvetica-Bold",
            )

            footer_text = (
                "💬 <b>¿Interesado en alguna carta?</b><br/>"
                "Contáctanos para consultar precios y disponibilidad.<br/>"
                "Todas las cartas están en excelente condición."
            )

            footer_para = Paragraph(footer_text, footer_style)

            footer_table = Table([[footer_para]], colWidths=[6.5 * inch])
            footer_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFEBEE")),
                        ("BOX", (0, 0), (-1, -1), 1.5, colors.HexColor("#D32F2F")),
                        ("TOPPADDING", (0, 0), (-1, -1), 15),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 15),
                        ("LEFTPADDING", (0, 0), (-1, -1), 20),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 20),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ]
                )
            )

            elements.append(footer_table)

        return elements
