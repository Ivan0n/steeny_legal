"""Create the two downloadable PDFs from the Markdown legal documents.

Requires reportlab. Fonts are cached under .cache/legal-pdf-fonts.
Run: python legal/build_pdfs.py
"""

from html import escape
from pathlib import Path
import re
from urllib.request import urlopen

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate


ROOT = Path(__file__).resolve().parent
FONT_CACHE = ROOT.parent / ".cache" / "legal-pdf-fonts"
FONT_CSS = (
    "https://fonts.googleapis.com/css2?"
    "family=Comfortaa:wght@700&family=Nunito:wght@400;700"
)
DOCUMENTS = ("user-agreement-site", "privacy-policy-site")


def load_fonts():
    FONT_CACHE.mkdir(parents=True, exist_ok=True)
    fonts = {("Nunito", "400"): "Nunito", ("Nunito", "700"): "Nunito-Bold",
             ("Comfortaa", "700"): "Comfortaa-Bold"}
    missing = [name for name in fonts.values() if not (FONT_CACHE / f"{name}.ttf").exists()]
    if missing:
        with urlopen(FONT_CSS, timeout=30) as response:
            css = response.read().decode("utf-8")
        for block in re.findall(r"@font-face\s*\{([^}]+)\}", css):
            family = re.search(r"font-family:\s*'([^']+)'", block).group(1)
            weight = re.search(r"font-weight:\s*(\d+)", block).group(1)
            name = fonts.get((family, weight))
            if name is None or name not in missing:
                continue
            url = re.search(r"src:\s*url\(([^)]+)\)", block).group(1)
            with urlopen(url, timeout=30) as response:
                (FONT_CACHE / f"{name}.ttf").write_bytes(response.read())
    for name in fonts.values():
        font = TTFont(name, str(FONT_CACHE / f"{name}.ttf"))
        if ord("я") not in font.face.charToGlyph:
            raise ValueError(f"Missing Cyrillic glyphs in {name}")
        pdfmetrics.registerFont(font)
    pdfmetrics.registerFontFamily("Nunito", normal="Nunito", bold="Nunito-Bold")


def inline_text(text):
    text = text.replace("—", "-").replace("–", "-").replace("‑", "-")
    pieces = []
    last = 0
    for match in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", text):
        pieces.append(escape(text[last:match.start()]))
        target = match.group(2).replace(".md", ".pdf")
        pieces.append(f'<link href="{escape(target, quote=True)}" color="#111111"><u>{escape(match.group(1))}</u></link>')
        last = match.end()
    pieces.append(escape(text[last:]))
    rendered = "".join(pieces)
    return re.sub(r"^(\d+\.\d+\.)", r"<b>\1</b>", rendered)


def page_frame(canvas, doc):
    width, height = A4
    left = doc.leftMargin
    right = width - doc.rightMargin
    canvas.saveState()
    canvas.setFillColor(colors.HexColor("#111111"))
    canvas.setFont("Comfortaa-Bold", 12)
    canvas.drawString(left, height - 15 * mm, "Steeny")
    canvas.setFont("Nunito", 9)
    canvas.drawRightString(right, height - 15 * mm, "steeny.xyz")
    canvas.linkURL("https://steeny.xyz", (right - 55, height - 16 * mm, right, height - 12 * mm), relative=0)
    canvas.setStrokeColor(colors.HexColor("#cccccc"))
    canvas.setLineWidth(.4)
    canvas.line(left, height - 19 * mm, right, height - 19 * mm)
    canvas.line(left, 18 * mm, right, 18 * mm)
    canvas.setFillColor(colors.HexColor("#555555"))
    canvas.setFont("Nunito", 8)
    canvas.drawString(left, 12 * mm, "support@steeny.xyz")
    canvas.linkURL("mailto:support@steeny.xyz", (left, 11 * mm, left + 80, 15 * mm), relative=0)
    canvas.drawRightString(right, 12 * mm, f"{doc.page}")
    canvas.restoreState()


def build_pdf(stem):
    title_style = ParagraphStyle("Title", fontName="Comfortaa-Bold", fontSize=20,
                                 leading=27, spaceAfter=10, alignment=TA_LEFT)
    date_style = ParagraphStyle("Date", fontName="Nunito", fontSize=9,
                                leading=13, textColor=colors.HexColor("#555555"), spaceAfter=18)
    body_style = ParagraphStyle("Body", fontName="Nunito", fontSize=10.5,
                                leading=15, spaceAfter=8, allowWidows=0, allowOrphans=0)
    heading_style = ParagraphStyle("Heading", fontName="Comfortaa-Bold", fontSize=12.5,
                                   leading=18, spaceBefore=13, spaceAfter=9, keepWithNext=True)
    bullet_style = ParagraphStyle("Bullet", parent=body_style, leftIndent=12,
                                  firstLineIndent=-9, spaceAfter=6)
    lines = (ROOT / f"{stem}.md").read_text(encoding="utf-8").splitlines()
    story = []
    title = ""
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("# "):
            title = line[2:]
            story.append(Paragraph(inline_text(title), title_style))
        elif line.startswith("**Редакция "):
            story.append(Paragraph(inline_text(line.strip("*")), date_style))
        elif line.startswith("## "):
            story.append(Paragraph(inline_text(line[3:]), heading_style))
        elif line.startswith("- "):
            story.append(Paragraph("- " + inline_text(line[2:]), bullet_style))
        else:
            story.append(Paragraph(inline_text(line), body_style))

    destination = ROOT / f"{stem}.pdf"
    doc = SimpleDocTemplate(str(destination), pagesize=A4,
                            leftMargin=20 * mm, rightMargin=20 * mm,
                            topMargin=27 * mm, bottomMargin=25 * mm,
                            title=title, author="Steeny", subject="Правовые документы Steeny")
    doc.build(story, onFirstPage=page_frame, onLaterPages=page_frame)
    print(f"Built {destination}")


if __name__ == "__main__":
    load_fonts()
    for stem in DOCUMENTS:
        build_pdf(stem)
