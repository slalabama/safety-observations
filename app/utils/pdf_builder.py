"""
Safety 1st PDF report builder.

Pure functions: pass in dicts, get back PDF bytes. No DB, no auth, no I/O
beyond producing the bytes in memory. The route handlers and the email
notification path both reuse the same builders.

Public surface:
    build_observation_pdf(observation: dict, employee: dict) -> bytes
    build_walkaround_pdf(submission: dict, form: dict, employee: dict) -> bytes
"""
import base64
import io
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

# Brand palette — mirrors the navy sidebar everywhere else in the app
BRAND_NAVY    = colors.HexColor("#1a2b4a")
BRAND_GREEN   = colors.HexColor("#28a745")
BRAND_RED     = colors.HexColor("#dc3545")
BRAND_GRAY    = colors.HexColor("#666666")
BRAND_MUTED   = colors.HexColor("#888888")
BRAND_LIGHT   = colors.HexColor("#f0f4f7")
BRAND_BORDER  = colors.HexColor("#dde3ea")

PAGE_WIDTH, PAGE_HEIGHT = letter
HEADER_HEIGHT = 0.6 * inch
SIDE_MARGIN   = 0.6 * inch
TOP_MARGIN    = HEADER_HEIGHT + 0.3 * inch
BOTTOM_MARGIN = 0.6 * inch


# ---------- branded image assets ----------
# Both are lazy-loaded the first time a PDF is built, then cached in memory
# for the life of the process. File-read failures are non-fatal — the PDF
# just renders without the missing image.

_STATIC_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "static",
)

# Hard-hat favicon, the same file served as the browser favicon
_HARDHAT_PATH = os.path.join(_STATIC_DIR, "apple-touch-icon.png")

# SL wordmark — bundled locally so PDFs don't depend on sl-america.com being
# reachable or willing to serve our request
_SL_LOGO_PATH = os.path.join(_STATIC_DIR, "sl-logo.png")

_hardhat_cache: Optional[bytes] = None
_hardhat_loaded: bool = False
_sl_logo_cache: Optional[bytes] = None
_sl_logo_loaded: bool = False


def _read_file_bytes(path: str) -> Optional[bytes]:
    try:
        with open(path, "rb") as f:
            return f.read()
    except Exception:
        return None


def _get_hardhat_bytes() -> Optional[bytes]:
    global _hardhat_cache, _hardhat_loaded
    if not _hardhat_loaded:
        _hardhat_cache = _read_file_bytes(_HARDHAT_PATH)
        _hardhat_loaded = True
    return _hardhat_cache


def _get_sl_logo_bytes() -> Optional[bytes]:
    global _sl_logo_cache, _sl_logo_loaded
    if not _sl_logo_loaded:
        _sl_logo_cache = _read_file_bytes(_SL_LOGO_PATH)
        _sl_logo_loaded = True
    return _sl_logo_cache


# ---------- styles ----------

def _build_styles() -> Dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "title", parent=base["Heading1"],
            fontName="Helvetica-Bold", fontSize=18,
            textColor=BRAND_NAVY, spaceAfter=4, leading=22,
        ),
        "subtitle": ParagraphStyle(
            "subtitle", parent=base["Normal"],
            fontName="Helvetica", fontSize=10,
            textColor=BRAND_MUTED, spaceAfter=14, leading=14,
        ),
        "section": ParagraphStyle(
            "section", parent=base["Heading2"],
            fontName="Helvetica-Bold", fontSize=12,
            textColor=BRAND_NAVY, spaceBefore=14, spaceAfter=6, leading=16,
        ),
        "body": ParagraphStyle(
            "body", parent=base["Normal"],
            fontName="Helvetica", fontSize=10,
            textColor=colors.black, leading=14,
        ),
        "label": ParagraphStyle(
            "label", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=9,
            textColor=BRAND_NAVY, leading=12,
        ),
        "value": ParagraphStyle(
            "value", parent=base["Normal"],
            fontName="Helvetica", fontSize=10,
            textColor=colors.black, leading=13,
        ),
        "footnote": ParagraphStyle(
            "footnote", parent=base["Normal"],
            fontName="Helvetica-Oblique", fontSize=9,
            textColor=BRAND_MUTED, leading=12,
        ),
    }


# ---------- page header (drawn via canvas on every page) ----------

def _draw_header(canvas, doc, kind_label: str, submission_id: int) -> None:
    canvas.saveState()

    # Navy band across the top
    canvas.setFillColor(BRAND_NAVY)
    canvas.rect(0, PAGE_HEIGHT - HEADER_HEIGHT, PAGE_WIDTH, HEADER_HEIGHT, fill=1, stroke=0)

    # Hard-hat icon, left side of the band
    icon_size = 0.40 * inch
    icon_y    = PAGE_HEIGHT - HEADER_HEIGHT + (HEADER_HEIGHT - icon_size) / 2.0
    icon_x    = SIDE_MARGIN
    text_x    = SIDE_MARGIN  # default if no icon

    hardhat = _get_hardhat_bytes()
    if hardhat:
        try:
            canvas.drawImage(
                ImageReader(io.BytesIO(hardhat)),
                icon_x, icon_y,
                width=icon_size, height=icon_size,
                mask="auto",
                preserveAspectRatio=True,
            )
            text_x = icon_x + icon_size + 0.12 * inch
        except Exception:
            pass  # render without the icon rather than failing the whole PDF

    # "Safety 1st" wordmark, left (offset past the icon)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 16)
    canvas.drawString(text_x,
                      PAGE_HEIGHT - HEADER_HEIGHT + 0.18 * inch,
                      "Safety 1st")

    # Report type + id, right
    canvas.setFont("Helvetica", 11)
    right_text = f"{kind_label}  \u2022  #{submission_id}"
    canvas.drawRightString(PAGE_WIDTH - SIDE_MARGIN,
                           PAGE_HEIGHT - HEADER_HEIGHT + 0.22 * inch,
                           right_text)

    # Footer: generated timestamp + page number
    canvas.setFillColor(BRAND_MUTED)
    canvas.setFont("Helvetica", 8)
    footer = f"Generated {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}  \u2022  Page {doc.page}"
    canvas.drawCentredString(PAGE_WIDTH / 2.0, 0.35 * inch, footer)

    canvas.restoreState()


def _new_doc(kind_label: str, submission_id: int) -> Tuple[BaseDocTemplate, io.BytesIO]:
    buf = io.BytesIO()
    doc = BaseDocTemplate(
        buf,
        pagesize=letter,
        leftMargin=SIDE_MARGIN,
        rightMargin=SIDE_MARGIN,
        topMargin=TOP_MARGIN,
        bottomMargin=BOTTOM_MARGIN,
        title=f"{kind_label} #{submission_id}",
    )
    frame = Frame(
        SIDE_MARGIN, BOTTOM_MARGIN,
        PAGE_WIDTH - 2 * SIDE_MARGIN,
        PAGE_HEIGHT - TOP_MARGIN - BOTTOM_MARGIN,
        id="content", showBoundary=0,
    )
    template = PageTemplate(
        id="branded",
        frames=[frame],
        onPage=lambda c, d: _draw_header(c, d, kind_label, submission_id),
    )
    doc.addPageTemplates([template])
    return doc, buf


# ---------- shared helpers ----------

def _esc(s: Optional[str]) -> str:
    if not s:
        return ""
    return (
        s.replace("&", "&amp;")
         .replace("<", "&lt;")
         .replace(">", "&gt;")
         .replace("\n", "<br/>")
    )


def _fmt_dt(dt) -> str:
    if not dt:
        return "\u2014"
    if isinstance(dt, str):
        return dt
    try:
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        return str(dt)


def _gps(lat, lon) -> str:
    if lat is None or lon is None:
        return "\u2014"
    try:
        return f"{float(lat):.5f}, {float(lon):.5f}"
    except Exception:
        return f"{lat}, {lon}"


def _metadata_table(rows: List[Tuple[str, Any]], styles) -> Table:
    data = []
    for label, value in rows:
        data.append([
            Paragraph(label, styles["label"]),
            Paragraph(_esc(str(value)) if value not in (None, "") else "\u2014", styles["value"]),
        ])
    t = Table(data, colWidths=[1.5 * inch, None])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), BRAND_LIGHT),
        ("BOX",          (0, 0), (-1, -1), 0.5, BRAND_BORDER),
        ("INNERGRID",    (0, 0), (-1, -1), 0.25, BRAND_BORDER),
        ("LEFTPADDING",  (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING",   (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def _decode_photo_b64(photo_data: Optional[str]) -> Optional[bytes]:
    """Decode the base64-stored photo to raw bytes. Handles data: URL prefix."""
    if not photo_data:
        return None
    s = photo_data.strip()
    if s.startswith("data:"):
        try:
            s = s.split(",", 1)[1]
        except Exception:
            return None
    try:
        return base64.b64decode(s)
    except Exception:
        return None


def _photo_flowable(photo_data: Optional[str], max_width: float = 5.5 * inch) -> Optional[Image]:
    raw = _decode_photo_b64(photo_data)
    if not raw:
        return None
    try:
        img = Image(io.BytesIO(raw))
        iw, ih = img.imageWidth, img.imageHeight
        if iw > max_width:
            scale = max_width / float(iw)
            img.drawWidth = max_width
            img.drawHeight = ih * scale
        else:
            img.drawWidth = iw
            img.drawHeight = ih
        return img
    except Exception:
        return None


def _sl_logo_flowable(max_width: float = 1.6 * inch) -> Optional[Image]:
    """Centered SL wordmark, used as the first flowable on the page."""
    raw = _get_sl_logo_bytes()
    if not raw:
        return None
    try:
        img = Image(io.BytesIO(raw))
        iw, ih = img.imageWidth, img.imageHeight
        if iw <= 0 or ih <= 0:
            return None
        scale = max_width / float(iw)
        img.drawWidth = max_width
        img.drawHeight = ih * scale
        img.hAlign = "CENTER"
        return img
    except Exception:
        return None


# ---------- public builders ----------

def build_observation_pdf(obs: Dict[str, Any], employee: Dict[str, Any]) -> bytes:
    """
    Build a PDF for one safety observation.

    obs keys:      id, incident_type, description, created_at, photo_data,
                   video_data, location_description (optional)
    employee keys: name, badge, department, role
    """
    styles = _build_styles()
    doc, buf = _new_doc("Safety Observation", obs.get("id", 0))
    story: List[Any] = []

    # Centered SL logo at the very top of the body
    sl = _sl_logo_flowable()
    if sl:
        story.append(sl)
        story.append(Spacer(1, 0.12 * inch))

    title = obs.get("incident_type") or "Safety Observation"
    story.append(Paragraph(_esc(title), styles["title"]))
    story.append(Paragraph("Reported via Safety 1st", styles["subtitle"]))

    story.append(_metadata_table([
        ("Submitted by", employee.get("name")),
        ("Badge",        employee.get("badge")),
        ("Department",   employee.get("department")),
        ("Submitted",    _fmt_dt(obs.get("created_at"))),
        ("Incident",     obs.get("incident_type")),
        ("Location",     obs.get("location_description")),
    ], styles))

    story.append(Paragraph("Description", styles["section"]))
    desc = obs.get("description") or "(no description provided)"
    story.append(Paragraph(_esc(desc), styles["body"]))

    photo = _photo_flowable(obs.get("photo_data"))
    if photo:
        story.append(Paragraph("Photo", styles["section"]))
        story.append(photo)

    if obs.get("video_data"):
        story.append(Spacer(1, 0.12 * inch))
        story.append(Paragraph(
            "Video attached \u2014 viewable in the Safety 1st app.",
            styles["footnote"],
        ))

    doc.build(story)
    return buf.getvalue()


def build_walkaround_pdf(sub: Dict[str, Any], form: Dict[str, Any], employee: Dict[str, Any]) -> bytes:
    """
    Build a PDF for one walk-around inspection submission.

    sub keys:      id, latitude, longitude, responses (dict question_id -> answer),
                   photo_data, video_data, created_at
    form keys:     name, description, sections
                   where sections is [{name, questions: [{id, text, question_type}]}]
    employee keys: name, badge, department, role
    """
    styles = _build_styles()
    doc, buf = _new_doc("Walk-Around Inspection", sub.get("id", 0))
    story: List[Any] = []

    # Centered SL logo at the very top of the body
    sl = _sl_logo_flowable()
    if sl:
        story.append(sl)
        story.append(Spacer(1, 0.12 * inch))

    story.append(Paragraph(_esc(form.get("name") or "Walk-Around Inspection"), styles["title"]))
    if form.get("description"):
        story.append(Paragraph(_esc(form["description"]), styles["subtitle"]))

    story.append(_metadata_table([
        ("Inspector",  employee.get("name")),
        ("Badge",      employee.get("badge")),
        ("Department", employee.get("department")),
        ("Inspected",  _fmt_dt(sub.get("created_at"))),
        ("Location",   _gps(sub.get("latitude"), sub.get("longitude"))),
    ], styles))

    # Normalize response keys (JSON often serializes int keys as strings)
    responses = sub.get("responses") or {}
    responses_s = {str(k): v for k, v in responses.items()}

    for section in form.get("sections", []):
        story.append(Paragraph(_esc(section.get("name") or "Section"), styles["section"]))

        rows = []
        for q in section.get("questions", []):
            qid    = str(q.get("id"))
            qtext  = q.get("text") or ""
            answer = responses_s.get(qid)
            answer_str = "" if answer is None else str(answer)

            # Color-code Yes / No / N/A so the report scans fast
            color = colors.black
            font  = "Helvetica"
            if answer_str == "Yes":
                color, font = BRAND_GREEN, "Helvetica-Bold"
            elif answer_str == "No":
                color, font = BRAND_RED, "Helvetica-Bold"
            elif answer_str == "N/A":
                color, font = BRAND_GRAY, "Helvetica-Bold"

            answer_style = ParagraphStyle(
                "ans",
                parent=styles["value"],
                textColor=color,
                fontName=font,
            )
            rows.append([
                Paragraph(_esc(qtext), styles["body"]),
                Paragraph(_esc(answer_str) or "\u2014", answer_style),
            ])

        if not rows:
            continue

        t = Table(rows, colWidths=[4.5 * inch, 1.6 * inch])
        t.setStyle(TableStyle([
            ("GRID",          (0, 0), (-1, -1), 0.25, BRAND_BORDER),
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING",   (0, 0), (-1, -1), 6),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("BACKGROUND",    (0, 0), (-1, -1), colors.white),
            # Alternate row stripe for legibility on long sections
            *[("BACKGROUND", (0, i), (-1, i), BRAND_LIGHT)
              for i in range(0, len(rows), 2)],
        ]))
        story.append(t)

    photo = _photo_flowable(sub.get("photo_data"))
    if photo:
        story.append(Paragraph("Photo", styles["section"]))
        story.append(photo)

    if sub.get("video_data"):
        story.append(Spacer(1, 0.12 * inch))
        story.append(Paragraph(
            "Video attached \u2014 viewable in the Safety 1st app.",
            styles["footnote"],
        ))

    doc.build(story)
    return buf.getvalue()
