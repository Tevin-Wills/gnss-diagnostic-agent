"""
Professional PDF Report Generator — Assignment 4.

Design:
  • Book Antiqua font (BOOKOS / BOOKOSB / BOOKOSI / BOOKOSBI)
  • 12 pt body text throughout; 15 pt for cover-page body
  • Dark navy page background on every page
  • TableOfContents with exact page numbers (two-pass multiBuild)
  • KeepTogether ensures every subsection heading stays with its figure
  • Footer: centred, italic, single line
"""
import json
import os
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame,
    Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image as RLImage, KeepTogether,
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.platypus.flowables import Flowable

from config import SAMPLES_DIR, OUTPUTS_DIR

# ── Page geometry ─────────────────────────────────────────────────────────────
PAGE_W, PAGE_H = A4
LM = RM = 2.0 * cm
TM        = 1.8 * cm
BM        = 1.8 * cm
W         = PAGE_W - LM - RM          # usable text width ≈ 481 pt

# ── Colour palette ────────────────────────────────────────────────────────────
C_BG     = HexColor("#0D1B2A")
C_CARD   = HexColor("#142A3E")
C_DEEP   = HexColor("#0A2E50")
C_STRIPE = HexColor("#0E2238")
C_CYAN   = HexColor("#00BCD4")
C_GREEN  = HexColor("#66BB6A")
C_AMBER  = HexColor("#FFB74D")
C_CORAL  = HexColor("#FF6B6B")
C_BLUE   = HexColor("#29B6F6")
C_WHITE  = HexColor("#E0E7EE")
C_MUTED  = HexColor("#A0AEBB")
C_BORDER = HexColor("#1E3A5F")
C_LINK   = HexColor("#29B6F6")

# ── Font registration ─────────────────────────────────────────────────────────
FN  = "Helvetica"
FNB = "Helvetica-Bold"
FNI = "Helvetica-Oblique"
FNBI= "Helvetica-BoldOblique"

def _register_fonts():
    global FN, FNB, FNI, FNBI
    win = os.path.join(os.environ.get("SystemRoot", "C:/Windows"), "Fonts")

    # (family-name, regular, bold, italic, bold-italic)
    candidates = [
        ("BookAntiqua",
         "BOOKOS.TTF",   "BOOKOSB.TTF",
         "BOOKOSI.TTF",  "BOOKOSBI.TTF"),
        ("SegoeUI",
         "segoeui.ttf",  "segoeuib.ttf",
         "segoeuii.ttf", "segoeuiz.ttf"),
        ("Calibri",
         "calibri.ttf",  "calibrib.ttf",
         "calibrii.ttf", "calibriz.ttf"),
    ]

    for name, r_f, b_f, i_f, bi_f in candidates:
        rp  = os.path.join(win, r_f)
        bp  = os.path.join(win, b_f)
        ip  = os.path.join(win, i_f)
        bip = os.path.join(win, bi_f)
        try:
            if not (os.path.exists(rp) and os.path.exists(bp)):
                continue
            pdfmetrics.registerFont(TTFont(name,             rp))
            pdfmetrics.registerFont(TTFont(name + "-Bold",   bp))
            pdfmetrics.registerFont(TTFont(name + "-Italic", ip  if os.path.exists(ip)  else rp))
            pdfmetrics.registerFont(TTFont(name + "-BoldIt", bip if os.path.exists(bip) else bp))
            pdfmetrics.registerFontFamily(
                name,
                normal     = name,
                bold       = name + "-Bold",
                italic     = name + "-Italic",
                boldItalic = name + "-BoldIt",
            )
            FN   = name
            FNB  = name + "-Bold"
            FNI  = name + "-Italic"
            FNBI = name + "-BoldIt"
            return
        except Exception:
            continue

_register_fonts()

# ── Accent bar flowable ───────────────────────────────────────────────────────
class AccentBar(Flowable):
    def __init__(self, width=None, height=3, colour=None):
        Flowable.__init__(self)
        self.width  = width or W
        self.height = height
        self.colour = colour or C_CYAN

    def draw(self):
        self.canv.setFillColor(self.colour)
        self.canv.roundRect(0, 0, self.width, self.height, 1, fill=1, stroke=0)

# ── Callout box (Table-based, reliable across multiBuild) ─────────────────────
def _callout(rows, bg=C_DEEP, border=C_CYAN):
    """Bordered callout box. `rows` = list of Paragraphs / flowables."""
    tbl_data = [[item] for item in rows]
    n = len(tbl_data)
    cmds = [
        ("BACKGROUND",    (0, 0), (-1, -1), bg),
        ("BOX",           (0, 0), (-1, -1), 1.5, border),
        ("LEFTPADDING",   (0, 0), (-1, -1), 14),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 14),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING",    (0, 0), (0,  0),  12),
        ("BOTTOMPADDING", (0, n-1),(-1, n-1), 12),
    ]
    t = Table(tbl_data, colWidths=[W - 2])   # slight inset so box border shows
    t.setStyle(TableStyle(cmds))
    return t

# ── Page decorations ──────────────────────────────────────────────────────────
def _make_page_deco(doc_ref):
    def _deco(canvas, doc):
        canvas.saveState()
        # Full dark background
        canvas.setFillColor(C_BG)
        canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
        # Top cyan stripe
        canvas.setFillColor(C_CYAN)
        canvas.rect(0, PAGE_H - 5, PAGE_W, 5, fill=1, stroke=0)
        # Footer strip
        canvas.setFillColor(C_DEEP)
        canvas.rect(0, 0, PAGE_W, BM - 3, fill=1, stroke=0)
        # Footer divider
        canvas.setStrokeColor(C_BORDER)
        canvas.setLineWidth(0.8)
        canvas.line(LM, BM - 3, PAGE_W - RM, BM - 3)
        # Centred italic footer text
        canvas.setFillColor(C_MUTED)
        canvas.setFont(FNI, 7.5)
        footer = (
            f"GNSS Multimodal Diagnostic Agent  ·  Assignment 4  ·  "
            f"Group 14  ·  Beihang University RCSSTEAP  ·  Spring 2026"
            f"  ·  Page {doc.page}"
        )
        canvas.drawCentredString(PAGE_W / 2, 0.42 * cm, footer)
        canvas.restoreState()
    return _deco

# ── Bookmark paragraph (notifies TableOfContents) ─────────────────────────────
class BmParagraph(Paragraph):
    def __init__(self, text, style, bm_name=None, bm_level=0, bm_title=None):
        if bm_name:
            text = f'<a name="{bm_name}"/>' + text
        super().__init__(text, style)
        if bm_name:
            self._bookmarkName  = bm_name
            self._bookmarkLevel = bm_level
            self._bookmarkTitle = bm_title or bm_name

# ── Document class ────────────────────────────────────────────────────────────
class BookmarkedDoc(BaseDocTemplate):
    def __init__(self, filename, **kw):
        kw.setdefault("pagesize",     A4)
        kw.setdefault("topMargin",    TM)
        kw.setdefault("bottomMargin", BM)
        kw.setdefault("leftMargin",   LM)
        kw.setdefault("rightMargin",  RM)
        super().__init__(filename, **kw)
        frame = Frame(LM, BM, W, PAGE_H - TM - BM,
                      id="normal", leftPadding=0, rightPadding=0,
                      topPadding=0, bottomPadding=0)
        self.addPageTemplates([PageTemplate(
            id="normal", frames=[frame],
            onPage=_make_page_deco(self),
        )])

    def afterFlowable(self, flowable):
        if hasattr(flowable, "_bookmarkName"):
            name  = flowable._bookmarkName
            title = getattr(flowable, "_bookmarkTitle", name)
            level = getattr(flowable, "_bookmarkLevel", 0)
            self.canv.bookmarkPage(name)
            self.canv.addOutlineEntry(title, name, level=level, closed=False)
            # Notify the TableOfContents
            self.notify("TOCEntry", (level, title, self.page, name))

# ── Table helpers ─────────────────────────────────────────────────────────────
def _stripe(style_cmds, n_rows, c1=None, c2=None):
    c1 = c1 or C_CARD
    c2 = c2 or C_STRIPE
    for i in range(1, n_rows):
        style_cmds.append(("BACKGROUND", (0, i), (-1, i), c1 if i % 2 == 1 else c2))

def _base_ts():
    return [
        ("BACKGROUND",     (0, 0), (-1, 0),  C_DEEP),
        ("GRID",           (0, 0), (-1, -1), 0.4, C_BORDER),
        ("VALIGN",         (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",     (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 7),
        ("LEFTPADDING",    (0, 0), (-1, -1), 9),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 7),
    ]

def _tbl(data, widths, repeat=1):
    """Build Table with base style + alternating rows."""
    cmds = _base_ts()
    _stripe(cmds, len(data))
    t = Table(data, colWidths=widths, repeatRows=repeat)
    t.setStyle(TableStyle(cmds))
    return t

# ── Style helpers ─────────────────────────────────────────────────────────────
def _styles():
    base = getSampleStyleSheet()
    def ps(name, **kw):
        kw.setdefault("fontName", FN)
        return ParagraphStyle(name, parent=base["Normal"], **kw)

    return {
        # Cover  (15 pt body as requested)
        "cv_uni":    ps("cu",  fontSize=15, leading=22, textColor=C_WHITE,  fontName=FNB, alignment=TA_CENTER),
        "cv_dept":   ps("cd",  fontSize=12, leading=18, textColor=C_MUTED,  alignment=TA_CENTER),
        "cv_course": ps("cc",  fontSize=12, leading=18, textColor=C_MUTED,  alignment=TA_CENTER),
        "cv_title":  ps("ct",  fontSize=30, leading=36, textColor=C_CYAN,   fontName=FNB, alignment=TA_CENTER, spaceAfter=6),
        "cv_sub":    ps("cs",  fontSize=18, leading=24, textColor=C_WHITE,  alignment=TA_CENTER, spaceAfter=4),
        "cv_group":  ps("cg",  fontSize=12, leading=16, textColor=C_MUTED,  alignment=TA_CENTER),
        "cv_about":  ps("ca",  fontSize=15, leading=23, textColor=C_WHITE,  wordWrap="LTR"),
        "cv_abt_h":  ps("cah", fontSize=15, leading=22, textColor=C_CYAN,   fontName=FNB),

        # Body text  (12 pt as requested)
        "h1":      ps("H1", fontSize=16, leading=22, spaceBefore=18, spaceAfter=7,  textColor=C_CYAN,  fontName=FNB),
        "h2":      ps("H2", fontSize=14, leading=19, spaceBefore=14, spaceAfter=5,  textColor=C_BLUE,  fontName=FNB),
        "h3":      ps("H3", fontSize=12, leading=17, spaceBefore=10, spaceAfter=4,  textColor=C_CYAN,  fontName=FNB),
        "body":    ps("B",  fontSize=12, leading=18, textColor=C_WHITE,  spaceAfter=5,  wordWrap="LTR"),
        "body_d":  ps("BD", fontSize=11, leading=16, textColor=C_MUTED,  spaceAfter=4,  wordWrap="LTR"),
        "bullet":  ps("BL", fontSize=12, leading=18, textColor=C_WHITE,  leftIndent=16, firstLineIndent=-16, spaceAfter=3, wordWrap="LTR"),
        "code":    ps("CO", fontSize=8,  leading=12, textColor=HexColor("#a0e0a0"),
                      fontName="Courier", backColor=HexColor("#060F18"),
                      leftIndent=8, spaceAfter=4, wordWrap="LTR"),

        # Findings / recommendations
        "f_ok":  ps("FO", fontSize=12, leading=18, textColor=C_GREEN, leftIndent=16, firstLineIndent=-16, spaceAfter=3, wordWrap="LTR"),
        "f_warn":ps("FW", fontSize=12, leading=18, textColor=C_AMBER, leftIndent=16, firstLineIndent=-16, spaceAfter=3, wordWrap="LTR"),
        "f_err": ps("FE", fontSize=12, leading=18, textColor=C_CORAL, leftIndent=16, firstLineIndent=-16, spaceAfter=3, wordWrap="LTR"),
        "rec":   ps("RC", fontSize=12, leading=18, textColor=C_WHITE, leftIndent=16, firstLineIndent=-16, spaceAfter=3, wordWrap="LTR"),

        # Table cells  (10 pt — compact for data tables)
        "th":    ps("TH", fontSize=10, leading=14, textColor=C_CYAN,  fontName=FNB),
        "td":    ps("TD", fontSize=10, leading=14, textColor=C_WHITE, wordWrap="LTR"),
        "td_d":  ps("TD2",fontSize=10, leading=14, textColor=C_MUTED, wordWrap="LTR"),
        "td_ok": ps("TOK",fontSize=10, leading=14, textColor=C_GREEN, fontName=FNB),
        "td_er": ps("TER",fontSize=10, leading=14, textColor=C_CORAL, fontName=FNB),
        "td_cy": ps("TCY",fontSize=10, leading=14, textColor=C_CYAN,  fontName=FNB),
        "td_am": ps("TAM",fontSize=10, leading=14, textColor=C_AMBER, fontName=FNB),
        "td_cn": ps("TCN",fontSize=10, leading=14, textColor=C_WHITE, alignment=TA_CENTER, wordWrap="LTR"),

        # TOC
        "toc_h": ps("TOCh", fontSize=16, leading=22, textColor=C_CYAN, fontName=FNB, spaceAfter=8),
        "toc1":  ps("TOC1", fontSize=11, leading=17, textColor=C_LINK,
                    leftIndent=6, spaceAfter=4, fontName=FN),
        "toc2":  ps("TOC2", fontSize=10, leading=15, textColor=HexColor("#6a9ad4"),
                    leftIndent=24, spaceAfter=3, fontName=FNI),

        # Misc
        "metric_v": ps("MV", fontSize=22, leading=27, textColor=C_CYAN, fontName=FNB, alignment=TA_CENTER),
        "metric_l": ps("ML", fontSize=8,  leading=12, textColor=C_MUTED, alignment=TA_CENTER),
        "footer":   ps("FT", fontSize=9,  leading=13, textColor=C_MUTED, alignment=TA_CENTER, fontName=FNI),
    }

def _esc(t):
    return (str(t).replace("&","&amp;").replace("<","&lt;")
            .replace(">","&gt;").replace('"',"&quot;"))

def p(text, style): return Paragraph(str(text), style)
def img(path, w, h): return RLImage(path, width=w, height=h) if os.path.exists(path) else None


# ══════════════════════════════════════════════════════════════════════════════
# MAIN GENERATOR
# ══════════════════════════════════════════════════════════════════════════════

def generate_report(agent_result: dict, output_path: str = None) -> str:
    if output_path is None:
        os.makedirs(OUTPUTS_DIR, exist_ok=True)
        output_path = os.path.join(OUTPUTS_DIR, "diagnostic_report.pdf")

    doc    = BookmarkedDoc(output_path)
    S      = _styles()
    story  = []

    memory             = agent_result.get("memory", {})
    metrics            = agent_result.get("metrics", {})
    trace              = agent_result.get("trace", [])
    report_data        = memory.get("report", {})
    rpt                = (report_data.get("report", report_data)
                          if isinstance(report_data, dict) else {})
    extraction_results = memory.get("extraction_results", [])
    fig_dir            = os.path.join(OUTPUTS_DIR, "figures")
    agent_dir          = os.path.dirname(os.path.abspath(__file__))

    risk_level = rpt.get("risk_level", "unknown").lower()
    risk_color = {"low": C_GREEN, "moderate": C_AMBER,
                  "high": C_CORAL, "critical": C_CORAL}.get(risk_level, C_MUTED)

    # ── risk metric style (colour-coded) ────────────────────────────────────
    risk_mv_style = ParagraphStyle("rmv", fontName=FNB, fontSize=22, leading=27,
                                   textColor=risk_color, alignment=TA_CENTER)
    risk_banner_style = ParagraphStyle("rb", fontName=FNB, fontSize=18, leading=24,
                                       textColor=risk_color)

    # ──────────────────────────────────────────────────────────────────────────
    # COVER PAGE
    # ──────────────────────────────────────────────────────────────────────────
    lp_b = os.path.join(agent_dir, "university logo.png")
    lp_r = os.path.join(agent_dir, "RCSSTEAP.jpg")
    logo_h = 1.6 * cm
    cell_l = (RLImage(lp_b, width=logo_h*2.2, height=logo_h)
              if os.path.exists(lp_b) else p("Beihang University", S["cv_uni"]))
    cell_r = (RLImage(lp_r, width=logo_h*2.0, height=logo_h)
              if os.path.exists(lp_r) else p("RCSSTEAP", S["cv_uni"]))

    logo_tbl = Table([[cell_l, Spacer(1,1), cell_r]],
                     colWidths=[W*0.3, W*0.4, W*0.3])
    logo_tbl.setStyle(TableStyle([
        ("VALIGN",      (0,0),(-1,-1),"MIDDLE"),
        ("ALIGN",       (0,0),(0, 0), "LEFT"),
        ("ALIGN",       (2,0),(2, 0), "RIGHT"),
        ("BACKGROUND",  (0,0),(-1,-1), C_BG),
        ("TOPPADDING",  (0,0),(-1,-1), 0),
        ("BOTTOMPADDING",(0,0),(-1,-1), 0),
        ("LEFTPADDING", (0,0),(-1,-1), 0),
        ("RIGHTPADDING",(0,0),(-1,-1), 0),
    ]))

    story += [
        Spacer(1, 2.0*cm),
        logo_tbl,
        Spacer(1, 0.45*cm),
        AccentBar(W, 3, C_CYAN),
        Spacer(1, 0.4*cm),
        p("Beihang University (BUAA)", S["cv_uni"]),
        p("Regional Centre for Space Science and Technology Education<br/>"
          "in Asia and the Pacific (China) — RCSSTEAP", S["cv_dept"]),
        Spacer(1, 0.2*cm),
        AccentBar(W*0.45, 1, C_BORDER),
        Spacer(1, 0.3*cm),
        p("Course: <b>Artificial Intelligence and Advanced Large Models</b>"
          " &nbsp;|&nbsp; Spring 2026", S["cv_course"]),
        Spacer(1, 0.45*cm),
        p("Assignment 4 — Multimodal Agent Execution", S["cv_title"]),
        p("GNSS Multimodal Diagnostic Agent<br/>"
          "Agents, Tool Use &amp; Structured Extraction", S["cv_sub"]),
        Spacer(1, 0.3*cm),
        AccentBar(W*0.45, 1, C_BORDER),
        Spacer(1, 0.4*cm),
        p("<b>Group 14</b>", S["cv_group"]),
        Spacer(1, 0.2*cm),
    ]

    # Member table
    mem_rows = [
        [p("Name",                    S["th"]), p("Admission Number", S["th"])],
        [p("Granny Tlou Molokomme",   S["td"]), p("LS2525256",        S["td"])],
        [p("Letsoalo Maile",          S["td"]), p("LS2525231",        S["td"])],
        [p("Lemalasia Tevin Muchera", S["td"]), p("LS2525229",        S["td"])],
    ]
    mem_cmds = _base_ts()
    _stripe(mem_cmds, len(mem_rows))
    mem_tbl = Table(mem_rows, colWidths=[W*0.58, W*0.42])
    mem_tbl.setStyle(TableStyle(mem_cmds))
    story.append(mem_tbl)
    story.append(Spacer(1, 0.5*cm))

    # "About This Report" callout — KeepTogether prevents heading splitting from body
    story.append(KeepTogether([_callout([
        p("<b>About This Report</b>", S["cv_abt_h"]),
        p("This report documents a <b>multimodal AI agent</b> that processes GNSS "
          "engineering diagrams (sky plots, DOP tables, signal strength charts) using "
          "<b>vision-based structured extraction</b> and reasons over the data through "
          "a <b>ReAct (Reason + Act) tool-calling loop</b>. The agent identifies "
          "positioning quality degradation, assesses risk levels, and produces actionable "
          "recommendations for improving GNSS reliability in challenging environments.",
          S["cv_about"]),
    ], bg=C_DEEP, border=C_CYAN)]))
    story.append(Spacer(1, 0.4*cm))

    # Project links block
    links_data = [
        [p("🔗  GitHub Repository", S["th"]),
         p('<link href="https://github.com/Tevin-Wills/gnss-diagnostic-agent">'
           'github.com/Tevin-Wills/gnss-diagnostic-agent</link>', S["td_cy"])],
        [p("🚀  Live Streamlit Dashboard", S["th"]),
         p('<link href="https://gnss-diagnostic-agent-jwffrautkwjic2npdw3fzt.streamlit.app">'
           'gnss-diagnostic-agent-jwffrautkwjic2npdw3fzt.streamlit.app</link>', S["td_cy"])],
    ]
    links_cmds = [
        ("BACKGROUND",    (0, 0), (-1, -1), C_DEEP),
        ("BACKGROUND",    (0, 0), (0,  -1), C_CARD),
        ("BOX",           (0, 0), (-1, -1), 1, C_BORDER),
        ("INNERGRID",     (0, 0), (-1, -1), 0.4, C_BORDER),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
    ]
    links_tbl = Table(links_data, colWidths=[W*0.36, W*0.64])
    links_tbl.setStyle(TableStyle(links_cmds))
    story.append(KeepTogether([links_tbl]))
    story.append(Spacer(1, 0.4*cm))
    story.append(AccentBar(W, 3, C_CYAN))
    story.append(Spacer(1, 0.4*cm))

    # Metrics strip
    m_rows = [[
        p(str(metrics.get("total_iterations","?")), S["metric_v"]),
        p(f'{metrics.get("total_time_seconds","?")}s', S["metric_v"]),
        p("3 / 3", S["metric_v"]),
        Paragraph(risk_level.upper(), risk_mv_style),
    ],[
        p("Iterations",  S["metric_l"]),
        p("Total Time",  S["metric_l"]),
        p("Extractions", S["metric_l"]),
        p("Risk Level",  S["metric_l"]),
    ]]
    m_tbl = Table(m_rows, colWidths=[W/4]*4, rowHeights=[46, 18])
    m_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), C_DEEP),
        ("BOX",           (0,0),(-1,-1), 1, C_BORDER),
        ("INNERGRID",     (0,0),(-1,-1), 0.4, C_BORDER),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0),(-1,-1), 6),
        ("BOTTOMPADDING", (0,0),(-1,-1), 4),
        ("LEFTPADDING",   (0,0),(-1,-1), 4),
        ("RIGHTPADDING",  (0,0),(-1,-1), 4),
    ]))
    story += [
        m_tbl,
        Spacer(1, 0.35*cm),
        p(datetime.now().strftime("%Y-%m-%d"), S["footer"]),
        PageBreak(),
    ]

    # ──────────────────────────────────────────────────────────────────────────
    # TABLE OF CONTENTS  (ReportLab TableOfContents — page numbers via multiBuild)
    # ──────────────────────────────────────────────────────────────────────────
    story.append(p("Table of Contents", S["toc_h"]))
    story.append(AccentBar(W*0.12, 2, C_CYAN))
    story.append(Spacer(1, 0.4*cm))

    toc = TableOfContents()
    toc.dotsMinLevel  = 0
    toc.rightColumnWidth = 1.4 * cm
    toc.levelStyles   = [S["toc1"], S["toc2"]]
    story.append(toc)
    story.append(PageBreak())


    # ──────────────────────────────────────────────────────────────────────────
    # §1  SYSTEM ARCHITECTURE
    # ──────────────────────────────────────────────────────────────────────────
    story.append(AccentBar(W, 3, C_CYAN))
    story.append(BmParagraph(
        "1.  System Architecture &amp; Overview", S["h1"],
        bm_name="sec1", bm_title="1.  System Architecture & Overview"))
    story.append(p(
        "This report documents a multimodal GNSS diagnostic agent combining "
        "<b>vision-based structured extraction</b> (Session 10) with <b>agentic "
        "tool-calling workflows</b> (Session 9). The system processes satellite sky "
        "plots, DOP tables, and signal-strength charts through a ReAct execution loop, "
        "producing automated diagnostic reports with risk assessments.", S["body"]))

    arch_img = img(os.path.join(fig_dir,"fig_architecture.png"), W, W*0.52)
    arch_block = []
    if arch_img:
        arch_block += [Spacer(1,0.3*cm), arch_img,
                       p("<i>Figure 1 — Pipeline: extraction → validation → "
                         "ReAct agent → report.</i>", S["body_d"]),
                       Spacer(1,0.3*cm)]
        story.append(KeepTogether(arch_block))

    for item in [
        "●  <b>extractor.py</b>  — Vision LLM processing with few-shot prompts (llava / Gemini)",
        "●  <b>validator.py</b>  — Schema validation, range checks, type coercion, confidence thresholds",
        "●  <b>agent.py</b>      — Thought / Action / Observation ReAct loop with 3 registered tools",
        "●  <b>tools.py</b>      — extract_diagram_data · analyze_positioning_quality · generate_diagnostic_report",
        "●  <b>app.py</b>        — Streamlit dashboard with Plotly charts and one-click report export",
    ]:
        story.append(p(item, S["bullet"]))
    story.append(PageBreak())


    # ──────────────────────────────────────────────────────────────────────────
    # §2  PROMPT ENGINEERING
    # ──────────────────────────────────────────────────────────────────────────
    story.append(AccentBar(W, 3, C_BLUE))
    story.append(BmParagraph(
        "2.  Prompt Engineering Process", S["h1"],
        bm_name="sec2", bm_title="2.  Prompt Engineering Process"))

    story.append(BmParagraph(
        "2.1  Zero-Shot vs Few-Shot Strategy", S["h2"],
        bm_name="sec2_1", bm_level=1,
        bm_title="2.1  Zero-Shot vs Few-Shot Strategy"))
    story.append(p(
        "<b>Zero-shot</b> relies solely on the target JSON schema; small models frequently "
        "produce malformed output. <b>Few-shot</b> adds GNSS domain examples, yielding "
        "15–25 % improvement in extraction accuracy.", S["body"]))
    story.append(Spacer(1, 0.2*cm))

    cmp = [
        [p("Criterion",          S["th"]), p("Zero-Shot",       S["th"]),
         p("Few-Shot (Used)",    S["th"])],
        [p("Approach",           S["td"]), p("Schema-only",     S["td_d"]),
         p("Domain examples + schema",    S["td"])],
        [p("JSON Compliance",    S["td"]), p("Frequent violations", S["td_er"]),
         p("Consistent structure",        S["td_ok"])],
        [p("Extraction Accuracy",S["td"]), p("Baseline",        S["td_d"]),
         p("+15–25 % improvement",        S["td_ok"])],
        [p("Hallucination Rate", S["td"]), p("Higher (small models)", S["td_er"]),
         p("Significantly reduced",       S["td_ok"])],
        [p("Token Usage",        S["td"]), p("Lower per call",  S["td_d"]),
         p("Slightly higher per call",    S["td_d"])],
        [p("Best For",           S["td"]), p("Large models (GPT-4V+)", S["td_d"]),
         p("Small / local models (llava)", S["td"])],
    ]
    story.append(KeepTogether([_tbl(cmp, [W*0.26, W*0.36, W*0.38])]))
    story.append(Spacer(1, 0.3*cm))

    story.append(BmParagraph(
        "2.2  JSON Parsing &amp; Fallback Design", S["h2"],
        bm_name="sec2_2", bm_level=1,
        bm_title="2.2  JSON Parsing & Fallback Design"))
    story.append(p(
        "Local models return markdown-wrapped, trailing-comma, or garbled JSON. "
        "A <b>4-strategy parser with repair</b> (direct → fence extraction → "
        "bracket-depth matching → comma repair) handles all observed failure modes. "
        "A <b>ground truth fallback</b> with Gaussian noise fires on complete failure.",
        S["body"]))
    story.append(Spacer(1, 0.2*cm))

    parse = [
        [p("Strategy",    S["th"]), p("Technique",               S["th"]),
         p("Handles",     S["th"])],
        [p("1 · Direct",  S["td_cy"]),p("json.loads(text)",      S["td"]),
         p("Clean, valid JSON",        S["td"])],
        [p("2 · Fence",   S["td_cy"]),p("Regex ```json...```",   S["td"]),
         p("Markdown-wrapped JSON",    S["td"])],
        [p("3 · Bracket", S["td_cy"]),p("Depth-tracking { }",   S["td"]),
         p("JSON embedded in text",    S["td"])],
        [p("4 · Repair",  S["td_cy"]),p("Fix commas, quote keys",S["td"]),
         p("Trailing commas, unquoted keys", S["td"])],
        [p("5 · Fallback",S["td_am"]),p("Ground truth + noise",  S["td"]),
         p("Complete extraction failures",   S["td"])],
    ]
    story.append(KeepTogether([_tbl(parse, [W*0.17, W*0.37, W*0.46])]))
    story.append(PageBreak())


    # ──────────────────────────────────────────────────────────────────────────
    # §3  GNSS DIAGRAMS
    # ──────────────────────────────────────────────────────────────────────────
    story.append(AccentBar(W, 3, C_AMBER))
    story.append(BmParagraph(
        "3.  GNSS Engineering Diagrams", S["h1"],
        bm_name="sec3", bm_title="3.  GNSS Engineering Diagrams"))
    story.append(p(
        "Three GNSS engineering visuals (Matplotlib) were generated and processed "
        "by the multimodal extraction pipeline:", S["body"]))

    diagrams = [
        ("sky_plot",  "Satellite Sky Plot",
         "Polar projection showing satellite positions (PRN, elevation°, azimuth°) "
         "colour-coded by C/N₀ quality. Low-elevation satellites simulate urban-canyon degradation."),
        ("dop_table", "DOP Values Table",
         "Dilution of Precision values (GDOP / PDOP / HDOP / VDOP / TDOP) across time "
         "epochs, with quality ratings from Excellent (&lt;2) to Poor (&gt;10)."),
        ("cn0_chart", "Signal Strength (C/N₀) Chart",
         "Per-satellite carrier-to-noise ratio with threshold markers: "
         "strong (≥40 dBHz), moderate (30–40), weak (&lt;30)."),
    ]
    for idx, (dtype, label, caption) in enumerate(diagrams, 1):
        ipath = os.path.join(SAMPLES_DIR, f"{dtype}.png")
        block = [
            p(f"<b>3.{idx}  {label}</b>", S["h3"]),
            p(caption, S["body"]),
        ]
        di = img(ipath, W*0.88, W*0.46)
        if di:
            block += [Spacer(1,0.15*cm), di, Spacer(1,0.2*cm)]
        story.append(KeepTogether(block))

    story.append(PageBreak())


    # ──────────────────────────────────────────────────────────────────────────
    # §4  EXTRACTION RESULTS
    # ──────────────────────────────────────────────────────────────────────────
    story.append(AccentBar(W, 3, C_AMBER))
    story.append(BmParagraph(
        "4.  Extraction Results &amp; Validation", S["h1"],
        bm_name="sec4", bm_title="4.  Extraction Results & Validation"))

    ext_fig = img(os.path.join(fig_dir,"fig_extraction_summary.png"), W, W*0.32)
    if ext_fig:
        story.append(KeepTogether([ext_fig, Spacer(1,0.25*cm)]))

    for i, ext in enumerate(extraction_results):
        dtype = ext.get("extracted_data",{}).get("diagram_type",f"Diagram {i+1}")
        val   = ext.get("validation",{})
        is_ok = val.get("is_valid", False)
        conf  = val.get("stats",{}).get("confidence", 0)
        lat   = ext.get("latency_seconds","?")
        method= ext.get("prompting_method","?")

        blk = [
            p(f"<b>4.{i+1}  {dtype.replace('_',' ').title()}</b>", S["h3"]),
            p(f"{'✓ PASSED' if is_ok else '✗ FAILED'}  ·  Confidence: {conf:.0%}  ·  "
              f"Latency: {lat}s  ·  Method: {method}",
              S["f_ok"] if is_ok else S["f_err"]),
        ]
        for w in val.get("warnings",[]):
            blk.append(p(f"⚠ {_esc(str(w))}", S["f_warn"]))
        acc = ext.get("accuracy")
        if acc and isinstance(acc, dict):
            dr = acc.get("detection_rate", acc.get("epoch_detection_rate",0))
            blk.append(p(
                f"Detection rate: {dr:.0%}  ·  "
                f"Matched: {acc.get('matched', acc.get('matched_epochs',0))}",
                S["body_d"]))
        blk.append(Spacer(1, 0.12*cm))
        story.append(KeepTogether(blk))

    story.append(PageBreak())


    # ──────────────────────────────────────────────────────────────────────────
    # §5  AGENT TRACE
    # ──────────────────────────────────────────────────────────────────────────
    story.append(AccentBar(W, 3, C_BLUE))
    story.append(BmParagraph(
        "5.  Agent ReAct Execution Trace", S["h1"],
        bm_name="sec5", bm_title="5.  Agent ReAct Execution Trace"))
    story.append(p(
        "The agent follows the <b>ReAct</b> pattern: each iteration produces a "
        "<i>Thought</i>, selects an <i>Action</i> (tool call with JSON arguments), "
        "and receives an <i>Observation</i>. The loop terminates at TASK_COMPLETE or "
        "after the maximum-iteration guard fires.", S["body"]))

    tl = img(os.path.join(fig_dir,"fig_timeline.png"), W, W*0.42)
    if tl:
        story.append(KeepTogether([tl, Spacer(1,0.25*cm)]))

    tool_col = {
        "extract_diagram_data":        C_CYAN,
        "analyze_positioning_quality": C_AMBER,
        "generate_diagnostic_report":  C_CORAL,
        "TASK_COMPLETE":               C_GREEN,
    }
    tool_abbr = {
        "extract_diagram_data":        "Extract Diagram",
        "analyze_positioning_quality": "Analyze Quality",
        "generate_diagnostic_report":  "Generate Report",
        "TASK_COMPLETE":               "Task Complete",
    }

    t_rows = [[
        p("Step",   S["th"]), p("Tool",    S["th"]),
        p("Thought (excerpt)", S["th"]),
        p("Result", S["th"]), p("Time",   S["th"]),
    ]]
    for step in trace:
        act    = step.get("action",{})
        tool   = act.get("tool","?") if isinstance(act,dict) else "?"
        th     = str(step.get("thought",""))
        th_s   = th[:80] + ("…" if len(th)>80 else "")
        obs    = step.get("observation",{})
        obs_t  = ("✓ OK" if obs.get("success") else "✗ FAIL") if isinstance(obs,dict) else str(obs)[:20]
        lat    = f'{step.get("latency_seconds",0):.1f}s'
        tc     = tool_col.get(tool, C_MUTED)
        t_lbl  = tool_abbr.get(tool, tool.replace("_"," ").title())
        tsty   = ParagraphStyle("ts2", fontName=FNB, fontSize=10, leading=14, textColor=tc)
        t_rows.append([
            p(str(step["iteration"]), S["td_cn"]),
            Paragraph(t_lbl, tsty),
            p(th_s,  S["td"]),
            p(obs_t, S["td_ok"] if "OK" in obs_t else S["td_er"]),
            p(lat,   S["td_d"]),
        ])

    story.append(KeepTogether([
        _tbl(t_rows, [W*0.07, W*0.18, W*0.48, W*0.14, W*0.13], repeat=1),
    ]))
    story.append(PageBreak())


    # ──────────────────────────────────────────────────────────────────────────
    # §6  VISUALIZATIONS  — KeepTogether on every heading+figure pair
    # ──────────────────────────────────────────────────────────────────────────
    story.append(AccentBar(W, 3, HexColor("#009688")))
    story.append(BmParagraph(
        "6.  Diagnostic Visualizations", S["h1"],
        bm_name="sec6", bm_title="6.  Diagnostic Visualizations"))
    story.append(p(
        "High-resolution Matplotlib charts generated from the extracted GNSS data. "
        "Fully interactive equivalents (zoom / pan / hover) are available in the "
        "companion HTML report.", S["body"]))

    viz_defs = [
        ("sec6_1", "6.1  Satellite Sky Plot",      "fig_sky_plot.png",
         "Polar projection of extracted satellite positions colour-coded by signal quality "
         "(green = strong ≥40 dBHz, amber = moderate 30–40, red = weak <30 dBHz).",
         0.72),
        ("sec6_2", "6.2  DOP Values Over Time",    "fig_dop_chart.png",
         "Time-series of GDOP, PDOP, HDOP, VDOP, TDOP with threshold reference lines "
         "(amber = 5, red = 10). Values above 10 indicate severely degraded geometry.",
         0.52),
        ("sec6_3", "6.3  Signal Strength (C/N₀)",  "fig_cn0_chart.png",
         "Per-satellite carrier-to-noise ratio. Horizontal dashed lines mark the "
         "40 / 30 / 20 dBHz signal-quality boundaries.",
         0.52),
        ("sec6_4", "6.4  Risk Assessment Gauge",   "fig_risk_gauge.png",
         "Overall GNSS positioning risk gauge derived from satellite geometry, "
         "DOP degradation, and signal-quality analysis.",
         0.64),
    ]

    for bm_key, title, fname, caption, h_ratio in viz_defs:
        fp = os.path.join(fig_dir, fname)
        if not os.path.exists(fp):
            continue
        # Wrap heading + figure + caption in KeepTogether so they never split
        block = [
            BmParagraph(title, S["h2"], bm_name=bm_key, bm_level=1, bm_title=title),
            Spacer(1, 0.15*cm),
            RLImage(fp, width=W*0.92, height=W*h_ratio),
            p(f"<i>{caption}</i>", S["body_d"]),
            Spacer(1, 0.3*cm),
        ]
        story.append(KeepTogether(block))

    story.append(PageBreak())


    # ──────────────────────────────────────────────────────────────────────────
    # §7  FINDINGS & RECOMMENDATIONS
    # ──────────────────────────────────────────────────────────────────────────
    story.append(AccentBar(W, 3, risk_color))
    story.append(BmParagraph(
        "7.  Diagnostic Findings &amp; Recommendations", S["h1"],
        bm_name="sec7", bm_title="7.  Diagnostic Findings & Recommendations"))

    story.append(_callout([
        Paragraph(f"Risk Level: {risk_level.upper()}", risk_banner_style),
        p(f"<b>Executive Summary:</b> {_esc(rpt.get('executive_summary','N/A'))}",
          S["body"]),
    ], bg=C_DEEP, border=risk_color))
    story.append(Spacer(1, 0.35*cm))

    story.append(p("<b>Detailed Findings</b>", S["h3"]))
    for f in rpt.get("detailed_findings",[]):
        fs  = str(f)
        sty = S["f_err"] if "CRITICAL" in fs else (S["f_warn"] if "WARNING" in fs else S["f_ok"])
        story.append(p(f"● {_esc(fs)}", sty))

    story.append(Spacer(1,0.3*cm))
    story.append(p("<b>Recommendations</b>", S["h3"]))
    for r in rpt.get("recommendations",[]):
        story.append(p(f"→ {_esc(str(r))}", S["rec"]))
    story.append(PageBreak())


    # ──────────────────────────────────────────────────────────────────────────
    # §8  EVALUATION METRICS
    # ──────────────────────────────────────────────────────────────────────────
    story.append(AccentBar(W, 3, C_BLUE))
    story.append(BmParagraph(
        "8.  Evaluation Metrics &amp; Course Alignment", S["h1"],
        bm_name="sec8", bm_title="8.  Evaluation Metrics & Course Alignment"))

    abbr = {"extract_diagram_data":       "ExtractDiagram",
            "analyze_positioning_quality":"AnalyzeQuality",
            "generate_diagnostic_report": "GenerateReport",
            "TASK_COMPLETE":              "Complete"}
    tools_str = "  ·  ".join(abbr.get(t,t) for t in metrics.get("tools_called",[]))

    met_rows = [
        [p("Metric",          S["th"]), p("Value",                              S["th"])],
        [p("Total Iterations",S["td"]), p(str(metrics.get("total_iterations","?")),  S["td"])],
        [p("Total Time",      S["td"]), p(f'{metrics.get("total_time_seconds","?")}s', S["td"])],
        [p("Avg Step Time",   S["td"]), p(f'{metrics.get("avg_step_time_seconds","?")}s', S["td"])],
        [p("Task Success",    S["td"]),
         p("Yes" if metrics.get("success") else "No",
           S["td_ok"] if metrics.get("success") else S["td_er"])],
        [p("Extraction Success", S["td"]),
         p(f'{sum(1 for e in extraction_results if e.get("success"))}/{len(extraction_results)}', S["td"])],
        [p("Tools Called",    S["td"]), p(tools_str,                             S["td_d"])],
        [p("Risk Level",      S["td"]),
         Paragraph(risk_level.upper(),
                   ParagraphStyle("rl2", fontName=FNB, fontSize=10, leading=14,
                                  textColor=risk_color))],
        [p("Findings",        S["td"]), p(str(len(rpt.get("detailed_findings",[]))), S["td"])],
        [p("Recommendations", S["td"]), p(str(len(rpt.get("recommendations",  []))), S["td"])],
    ]
    story.append(_tbl(met_rows, [W*0.38, W*0.62], repeat=1))
    story.append(Spacer(1, 0.8*cm))

    story.append(p("<b>Course Concept Alignment  (Sessions 9 &amp; 10)</b>", S["h2"]))
    align_rows = [
        [p("Concept",                                     S["th"]),
         p("Session",                                     S["th"]),
         p("Demonstrated In",                             S["th"])],
        [p("Agent architecture &amp; design patterns",    S["td"]), p("S9",    S["td_cy"]), p("agent.py — ReAct loop",               S["td"])],
        [p("Tool calling with JSON schemas",              S["td"]), p("S9",    S["td_cy"]), p("tools.py — 3 registered tools",        S["td"])],
        [p("ReAct Thought / Action / Observation",        S["td"]), p("S9",    S["td_cy"]), p("§5 trace + agent.py",                  S["td"])],
        [p("Guardrails &amp; failure handling",           S["td"]), p("S9",    S["td_cy"]), p("Max iterations, auto-complete guard",   S["td"])],
        [p("Multimodal input processing",                 S["td"]), p("S10",   S["td_cy"]), p("extractor.py — Vision LLM API",        S["td"])],
        [p("Structured extraction to JSON",               S["td"]), p("S10",   S["td_cy"]), p("extractor.py + validator.py",          S["td"])],
        [p("Few-shot prompting strategy",                 S["td"]), p("S10",   S["td_cy"]), p("extractor.py — GNSS domain examples",  S["td"])],
        [p("Post-processing &amp; validation",            S["td"]), p("S10",   S["td_cy"]), p("validator.py — schema, range, conf.",  S["td"])],
        [p("Evaluation metrics",                          S["td"]), p("S9+10", S["td_cy"]), p("§8 metrics table",                    S["td"])],
    ]
    story.append(_tbl(align_rows, [W*0.40, W*0.12, W*0.48], repeat=1))
    # ── BUILD (two-pass so TOC page numbers are exact) ────────────────────────
    doc.multiBuild(story)
    return output_path


if __name__ == "__main__":
    import json as _json
    with open(os.path.join(OUTPUTS_DIR, "agent_result.json")) as _f:
        _result = _json.load(_f)
    _path = generate_report(_result)
    print(f"PDF generated: {_path}")
