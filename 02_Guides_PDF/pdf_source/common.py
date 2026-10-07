"""Shared layout helpers for the two conveyor guides (reportlab)."""
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.graphics.shapes import Circle, Drawing, Line, Polygon, Rect, String
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (KeepTogether, ListFlowable, ListItem, PageBreak, Paragraph,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

FONT_DIR = "/usr/share/fonts/truetype/dejavu/"
pdfmetrics.registerFont(TTFont("DV", FONT_DIR + "DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DVB", FONT_DIR + "DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("DVM", FONT_DIR + "DejaVuSansMono.ttf"))
pdfmetrics.registerFontFamily("DV", normal="DV", bold="DVB", italic="DV", boldItalic="DVB")

NAVY = colors.HexColor("#1f3a5f")
GREY = colors.HexColor("#f1f3f6")
LINE = colors.HexColor("#b8c0cc")
INK = colors.HexColor("#222222")
OKC = colors.HexColor("#e3f4e6")
CHK = colors.HexColor("#fff3cd")
BAD = colors.HexColor("#fde2e2")
BLUE = colors.HexColor("#eef3fa")
WIDTH = 174  # usable page width in mm

ST = dict(
    title=ParagraphStyle("t", fontName="DVB", fontSize=22, leading=27, textColor=NAVY, spaceAfter=4),
    sub=ParagraphStyle("s", fontName="DV", fontSize=10.5, leading=14.5, textColor=colors.HexColor("#555555"), spaceAfter=10),
    h1=ParagraphStyle("h1", keepWithNext=1, fontName="DVB", fontSize=15, leading=19, textColor=NAVY, spaceBefore=8, spaceAfter=6),
    h2=ParagraphStyle("h2", keepWithNext=1, fontName="DVB", fontSize=11.5, leading=15, textColor=NAVY, spaceBefore=8, spaceAfter=4),
    h3=ParagraphStyle("h3", keepWithNext=1, fontName="DVB", fontSize=9.5, leading=13, textColor=INK, spaceBefore=5, spaceAfter=2),
    p=ParagraphStyle("p", fontName="DV", fontSize=9.5, leading=13.5, spaceAfter=5),
    c=ParagraphStyle("c", fontName="DV", fontSize=8.3, leading=11),
    ch=ParagraphStyle("ch", fontName="DVB", fontSize=8.3, leading=11, textColor=colors.white),
    note=ParagraphStyle("n", fontName="DV", fontSize=9, leading=12.5),
    code=ParagraphStyle("code", fontName="DVM", fontSize=8.6, leading=12.5, leftIndent=6, backColor=GREY,
                        borderPadding=5, spaceBefore=4, spaceAfter=10),
)


class Doc:
    """Collects flowables; every helper appends to self.story."""

    def __init__(self):
        self.story = []

    def add(self, flowable):
        self.story.append(flowable)

    def title(self, text, sub):
        self.add(Paragraph(text, ST["title"]))
        self.add(Paragraph(sub, ST["sub"]))

    def h1(self, text):
        self.add(Paragraph(text, ST["h1"]))

    def h2(self, text):
        self.add(Paragraph(text, ST["h2"]))

    def p(self, text):
        self.add(Paragraph(text, ST["p"]))

    def code(self, text):
        self.add(Paragraph(text, ST["code"]))

    def sp(self, height=4):
        self.add(Spacer(1, height))

    def page(self):
        self.add(PageBreak())

    def steps(self, items):
        self.add(ListFlowable([ListItem(Paragraph(i, ST["p"]), leftIndent=16) for i in items],
                              bulletType="1", bulletFontName="DVB", bulletFontSize=9.5, leftIndent=16))

    def bullets(self, items):
        self.add(ListFlowable([ListItem(Paragraph(i, ST["p"]), leftIndent=14) for i in items],
                              bulletType="bullet", bulletFontSize=7, leftIndent=14))

    def box(self, text, color=CHK):
        table = Table([[Paragraph(text, ST["note"])]], colWidths=[WIDTH * mm])
        table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), color), ("BOX", (0, 0), (-1, -1), 0.6, LINE),
                                   ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                                   ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
        self.add(table)
        self.sp(6)

    def table(self, head, rows, widths, status_col=None):
        data = [[Paragraph(h, ST["ch"]) for h in head]] + [[Paragraph(str(x), ST["c"]) for x in r] for r in rows]
        table = Table(data, colWidths=[w * mm for w in widths], repeatRows=1)
        style = [("BACKGROUND", (0, 0), (-1, 0), NAVY), ("GRID", (0, 0), (-1, -1), 0.4, LINE),
                 ("VALIGN", (0, 0), (-1, -1), "TOP"), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GREY]),
                 ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                 ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]
        if status_col is not None:
            for i, row in enumerate(rows, 1):
                value = str(row[status_col]).upper()
                color = OKC if value.startswith("OK") else BAD if value.startswith(("MISSING", "NOT")) else CHK
                style.append(("BACKGROUND", (status_col, i), (status_col, i), color))
        table.setStyle(TableStyle(style))
        self.add(table)
        self.sp(7)

    # ---- ladder diagram -------------------------------------------------
    def rung(self, title, rows, links=(), ncols=None, explain=None):
        """rows: list of rows; a cell is None, '-' (wire) or (kind, label[, box lines]).
        kinds: NO, NC, COIL, S, R, BOX. links: (column boundary, row a, row b) vertical wires."""
        n = ncols or max(len(r) for r in rows)
        x0 = 4 * mm
        cw = (170 * mm - x0) / n

        def box_height(cell):
            return max(9 * mm, (len(cell[2]) * 3.1 + 2.5) * mm)

        below = [max([6 * mm] + [box_height(c) - 3.2 * mm + 2.5 * mm for c in row
                                 if isinstance(c, tuple) and c[0] == "BOX"]) for row in rows]
        above = 12 * mm
        centres, used = [], 0
        for extra in below:
            centres.append(used + above)
            used += above + extra
        height = used + 1 * mm
        d = Drawing(WIDTH * mm, height)

        def wire(x1, y1, x2, y2, w=0.9):
            d.add(Line(x1, y1, x2, y2, strokeColor=INK, strokeWidth=w))

        def yc(r):
            return height - centres[r]

        wire(x0, height - 2 * mm, x0, yc(len(rows) - 1) - 5 * mm, 1.6)  # left power rail
        for r, row in enumerate(rows):
            y = yc(r)
            for c in range(n):
                cell = row[c] if c < len(row) else None
                xa = x0 + c * cw
                xb = xa + cw
                xm = (xa + xb) / 2
                if cell is None:
                    continue
                if cell == "-":
                    wire(xa, y, xb, y)
                    continue
                kind, label = cell[0], cell[1]
                if kind == "BOX":
                    lines = cell[2]
                    bw = min(cw - 3 * mm, 46 * mm)
                    bh = box_height(cell)
                    top = y + 3.2 * mm
                    d.add(Rect(xm - bw / 2, top - bh, bw, bh, fillColor=BLUE, strokeColor=INK, strokeWidth=0.9))
                    wire(xa, y, xm - bw / 2, y)
                    wire(xm + bw / 2, y, xb, y)
                    for i, text in enumerate(lines):
                        d.add(String(xm, top - (3.1 * (i + 1)) * mm, text, fontName="DVB" if i == 0 else "DV",
                                     fontSize=5.9, textAnchor="middle"))
                    label_y = top + 1.2 * mm
                else:
                    gap, half = 1.6 * mm, 2.6 * mm
                    wire(xa, y, xm - gap, y)
                    wire(xm + gap, y, xb, y)
                    if kind in ("NO", "NC"):
                        wire(xm - gap, y - half, xm - gap, y + half)
                        wire(xm + gap, y - half, xm + gap, y + half)
                        if kind == "NC":
                            wire(xm - gap, y - half, xm + gap, y + half, 0.8)
                    else:
                        d.add(Circle(xm, y, 2.3 * mm, fillColor=colors.white, strokeColor=INK, strokeWidth=0.9))
                        wire(xm - gap, y, xm - 2.3 * mm, y)
                        wire(xm + 2.3 * mm, y, xm + gap, y)
                        if kind in ("S", "R"):
                            d.add(String(xm, y - 1.1 * mm, kind, fontName="DVB", fontSize=7, textAnchor="middle"))
                    label_y = y + half + 1.2 * mm
                for i, text in enumerate(reversed(label.split("\n"))):
                    if text:
                        d.add(String(xm, label_y + i * 2.5 * mm, text, fontName="DV", fontSize=5.9,
                                     textAnchor="middle", fillColor=NAVY))
        for boundary, r1, r2 in links:
            x = x0 + boundary * cw
            wire(x, yc(r1), x, yc(r2))
        items = [Paragraph(title, ST["h3"]), d] if title else [d]
        if explain:
            items += [Paragraph(explain, ST["note"]), Spacer(1, 5)]
        self.add(KeepTogether(items))

    def build(self, path, footer_text, doc_title):
        def footer(canvas, doc):
            canvas.saveState()
            canvas.setFont("DV", 7.5)
            canvas.setFillColor(colors.HexColor("#777777"))
            canvas.drawString(18 * mm, 10 * mm, footer_text)
            canvas.drawRightString(192 * mm, 10 * mm, f"Page {doc.page}")
            canvas.restoreState()

        SimpleDocTemplate(path, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm,
                          bottomMargin=17 * mm, title=doc_title).build(self.story, onFirstPage=footer,
                                                                       onLaterPages=footer)


# cell shortcuts for ladder rungs
def NO(label): return ("NO", label)
def NC(label): return ("NC", label)
def COIL(label): return ("COIL", label)
def SET(label): return ("S", label)
def RST(label): return ("R", label)
def BOX(label, lines): return ("BOX", label, lines)


class Diagram:
    """Small box-and-arrow drawing helper (units: mm)."""

    def __init__(self, height):
        self.d = Drawing(WIDTH * mm, height * mm)

    def box(self, x, y, w, h, text, fill=GREY, bold_first=False):
        self.d.add(Rect(x * mm, y * mm, w * mm, h * mm, fillColor=fill, strokeColor=NAVY, strokeWidth=0.8))
        lines = text.split("\n")
        y0 = y + h / 2 + (len(lines) - 1) * 1.7 - 1.1
        for i, line in enumerate(lines):
            self.d.add(String((x + w / 2) * mm, (y0 - i * 3.4) * mm, line,
                              fontName="DVB" if (bold_first and i == 0) else "DV", fontSize=7.2, textAnchor="middle"))

    def line(self, x1, y1, x2, y2):
        self.d.add(Line(x1 * mm, y1 * mm, x2 * mm, y2 * mm, strokeColor=NAVY, strokeWidth=0.9))

    def arrow(self, x1, y1, x2, y2):
        import math
        self.line(x1, y1, x2, y2)
        ang = math.atan2(y2 - y1, x2 - x1)
        size = 1.8
        pts = []
        for da in (0, 2.6, -2.6):
            px = x2 + (size * math.cos(ang + da) if da else 0)
            py = y2 + (size * math.sin(ang + da) if da else 0)
            pts += [px * mm, py * mm]
        self.d.add(Polygon(pts, fillColor=NAVY, strokeColor=NAVY, strokeWidth=0.5))

    def label(self, x, y, text, anchor="start", size=6.6):
        for i, line in enumerate(text.split("\n")):
            self.d.add(String(x * mm, (y - i * 2.9) * mm, line, fontName="DV", fontSize=size,
                              fillColor=colors.HexColor("#444444"), textAnchor=anchor))
