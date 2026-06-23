from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable, Image as RLImage, PageBreak,
    KeepTogether, ListFlowable, ListItem,
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate, Frame
from reportlab.platypus.tableofcontents import TableOfContents
from PIL import Image as PILImage
from io import BytesIO
import os
from datetime import datetime

PAGE_W, PAGE_H = A4
MARGIN = 45
USABLE_W = PAGE_W - 2 * MARGIN

# ── Dark theme palette ──
DARK_BG = colors.HexColor("#0F0F1A")
DARK_CARD = colors.HexColor("#1A1A2E")
DARK_BORDER = colors.HexColor("#2A2A45")
AMBER = colors.HexColor("#F59E0B")
AMBER_DIM = colors.HexColor("#B87E0A")
AMBER_GLOW = colors.HexColor("#F59E0B33")
ORANGE = colors.HexColor("#E8893C")
WHITE = colors.white
LIGHT = colors.HexColor("#E8E8F0")
MUTED = colors.HexColor("#9898B0")
DIM = colors.HexColor("#686880")
DARKER_TEXT = colors.HexColor("#0A0A0F")

SEVERITY_COLORS = {
    "Critical": colors.HexColor("#EF4444"),
    "High": colors.HexColor("#F97316"),
    "Medium": colors.HexColor("#EAB308"),
    "Low": colors.HexColor("#22C55E"),
}
SEVERITY_BG = {
    "Critical": colors.HexColor("#450A0A"),
    "High": colors.HexColor("#431407"),
    "Medium": colors.HexColor("#422006"),
    "Low": colors.HexColor("#052E16"),
}


def build_pdf_report(ddr_data: dict, images: list, output_path: str, client_name: str = "Client"):
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    class DarkDocTemplate(SimpleDocTemplate):
        def __init__(self, *args, **kwargs):
            SimpleDocTemplate.__init__(self, *args, **kwargs)
            self.client_name = client_name

        def afterPage(self):
            self.canv.saveState()
            w, h = A4
            # Footer bar
            self.canv.setFillColor(DARK_CARD)
            self.canv.rect(0, 0, w, 28, fill=1, stroke=0)
            # Footer line
            self.canv.setStrokeColor(AMBER_DIM)
            self.canv.setLineWidth(0.5)
            self.canv.line(MARGIN, 28, w - MARGIN, 28)
            # Footer text
            self.canv.setFont("Helvetica", 7)
            self.canv.setFillColor(DIM)
            self.canv.drawString(MARGIN, 10, f"Agentic DDR  |  {self.client_name}")
            self.canv.drawRightString(w - MARGIN, 10, f"Page {self.page}")
            self.canv.drawCentredString(w / 2, 10, datetime.now().strftime("%Y-%m-%d"))
            self.canv.restoreState()

    def add_header_block(canvas, doc):
        pass

    doc = DarkDocTemplate(
        output_path, pagesize=A4,
        rightMargin=MARGIN, leftMargin=MARGIN,
        topMargin=38, bottomMargin=42,
    )

    S = {
        "cover_title": ParagraphStyle("ct", fontSize=28, fontName="Helvetica-Bold", alignment=TA_CENTER, textColor=AMBER, leading=34, spaceAfter=6),
        "cover_sub": ParagraphStyle("cs", fontSize=11, fontName="Helvetica", alignment=TA_CENTER, textColor=MUTED, leading=15),
        "client_name_style": ParagraphStyle("cns", fontSize=22, fontName="Helvetica-Bold", alignment=TA_CENTER, textColor=LIGHT, leading=28, spaceAfter=4),
        "sec": ParagraphStyle("sec", fontSize=16, fontName="Helvetica-Bold", textColor=AMBER, leading=20, spaceBefore=20, spaceAfter=10),
        "sec_line": ParagraphStyle("sl", fontSize=10, fontName="Helvetica-Bold", textColor=AMBER_DIM, leading=13, spaceBefore=4, spaceAfter=2),
        "h2": ParagraphStyle("h2", fontSize=12, fontName="Helvetica-Bold", textColor=LIGHT, leading=16, spaceBefore=10, spaceAfter=4),
        "body": ParagraphStyle("body", fontSize=9.5, fontName="Helvetica", textColor=LIGHT, leading=17, spaceAfter=0),
        "body_bold": ParagraphStyle("bb", fontSize=9.5, fontName="Helvetica-Bold", textColor=LIGHT, leading=17),
        "sm": ParagraphStyle("sm", fontSize=8, fontName="Helvetica", textColor=MUTED, leading=11, spaceAfter=2),
        "label": ParagraphStyle("lbl", fontSize=9, fontName="Helvetica-Bold", textColor=MUTED, leading=12),
        "note": ParagraphStyle("note", fontSize=8.5, fontName="Helvetica-Oblique", textColor=DIM, leading=11),
        "bul": ParagraphStyle("bul", fontSize=9.5, fontName="Helvetica", textColor=LIGHT, leading=14, spaceAfter=4, leftIndent=16),
        "hdr": ParagraphStyle("hdr", fontSize=8.5, fontName="Helvetica-Bold", textColor=DARKER_TEXT, leading=12),
        "footer": ParagraphStyle("ftr", fontSize=7, fontName="Helvetica", textColor=DIM, leading=9, alignment=TA_CENTER),
        "metric_value": ParagraphStyle("mv", fontSize=22, fontName="Helvetica-Bold", textColor=AMBER, leading=26, alignment=TA_CENTER),
        "metric_label": ParagraphStyle("ml", fontSize=8, fontName="Helvetica", textColor=MUTED, leading=10, alignment=TA_CENTER),
        "action_priority": ParagraphStyle("ap", fontSize=8.5, fontName="Helvetica-Bold", leading=12),
    }

    def safe_str(val, default="Not Available"):
        return str(val) if val else default

    def find_image(ref):
        for img in images:
            if img.get("ref") == ref:
                return img
        return None

    def hr_amber(thick=2):
        return HRFlowable(width="50%", thickness=thick, color=AMBER_DIM, spaceAfter=14, spaceBefore=4, hAlign='CENTER')

    def hr_subtle():
        return HRFlowable(width="100%", thickness=0.5, color=DARK_BORDER, spaceAfter=10, spaceBefore=4)

    def render_image(img_ref):
        if img_ref == "Not Available":
            return None
        img_obj = find_image(img_ref)
        if not img_obj or not img_obj.get("data"):
            return None
        try:
            pil = PILImage.open(BytesIO(img_obj["data"]))
            if pil.mode not in ("RGB", "L"):
                pil = pil.convert("RGB")
            iw, ih = pil.size
            max_w = USABLE_W * 0.92
            max_h = 90 * mm
            scale = min(max_w / iw, max_h / ih, 1.0)
            if scale < 0.05:
                return None
            buf = BytesIO()
            pil.save(buf, format="JPEG", quality=72)
            buf.seek(0)
            return RLImage(buf, width=iw * scale, height=ih * scale, hAlign='CENTER')
        except Exception as e:
            print("  [WARN] Image failed: %s - %s" % (img_ref, e))
            return None

    def sev_badge(level, text=None):
        c = SEVERITY_COLORS.get(level, DIM)
        bg = SEVERITY_BG.get(level, DARK_CARD)
        txt = text or level.upper()
        p = Paragraph(
            '<font color="%s"><b>%s</b></font>' % (c.hexval(), txt),
            ParagraphStyle("sb", fontSize=8, fontName="Helvetica-Bold", alignment=TA_CENTER, leading=11)
        )
        t = Table([[p]], colWidths=[72])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), bg),
            ("BOX", (0, 0), (-1, -1), 1.5, c),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        return t

    def metric_card(value, label, color=AMBER):
        return Table([
            [Paragraph(str(value), ParagraphStyle("mv2", fontSize=20, fontName="Helvetica-Bold", textColor=color, leading=24, alignment=TA_CENTER))],
            [Paragraph(label, S["metric_label"])],
        ], colWidths=[72])

    def build_table(headers, rows, col_widths):
        data = [headers] + rows
        wrapped = []
        for r_idx, row in enumerate(data):
            cells = []
            for c_idx, cell in enumerate(row):
                if r_idx == 0:
                    cells.append(Paragraph(str(cell), S["hdr"]))
                else:
                    cells.append(Paragraph(str(cell), S["body"]))
            wrapped.append(cells)
        t = Table(wrapped, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), AMBER),
            ("TEXTCOLOR", (0, 0), (-1, 0), DARKER_TEXT),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8.5),
            ("FONTSIZE", (0, 1), (-1, -1), 8.5),
            ("TEXTCOLOR", (0, 1), (-1, -1), LIGHT),
            ("LEADING", (0, 0), (-1, -1), 15),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [DARK_CARD, colors.HexColor("#16162A")]),
            ("GRID", (0, 0), (-1, -1), 0.5, DARK_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        return t

    story = []

    # ═══════════════════════════════════════════
    # COVER PAGE — dark premium
    # ═══════════════════════════════════════════
    story.append(Spacer(1, 20))
    # Dark cover background block
    cover_bg_data = [[
        Table([[""]], colWidths=[USABLE_W], rowHeights=[220])
    ]]
    cover_bg = Table(cover_bg_data, colWidths=[USABLE_W])
    cover_bg.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), DARK_CARD),
        ("BOX", (0, 0), (-1, -1), 1, DARK_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(cover_bg)
    story.append(Spacer(1, -200))

    story.append(Spacer(1, 50))
    story.append(hr_amber(2.5))
    story.append(Spacer(1, 20))
    story.append(Paragraph("DETAILED DIAGNOSTIC REPORT", S["cover_title"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph("AI-Powered Asset Intelligence", S["cover_sub"]))
    story.append(Spacer(1, 20))
    story.append(hr_amber(1.5))
    story.append(Spacer(1, 18))

    story.append(Paragraph(client_name.upper(), S["client_name_style"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Prepared exclusively for", S["cover_sub"]))

    story.append(Spacer(1, 25))

    report_title = safe_str(ddr_data.get("report_title", "Site Inspection Report"))
    report_date = safe_str(ddr_data.get("report_date", datetime.now().strftime("%Y-%m-%d")))

    info_rows = [
        [Paragraph('<font color="%s">Report</font>' % DIM.hexval(), S["sm"]), Paragraph(report_title, S["body"])],
        [Paragraph('<font color="%s">Date</font>' % DIM.hexval(), S["sm"]), Paragraph(report_date, S["body"])],
        [Paragraph('<font color="%s">Prepared By</font>' % DIM.hexval(), S["sm"]), Paragraph("AI-Assisted Analysis Engine v3.0", S["body"])],
        [Paragraph('<font color="%s">Client</font>' % DIM.hexval(), S["sm"]), Paragraph(client_name, S["body"])],
    ]
    ci_table = Table(info_rows, colWidths=[30 * mm, USABLE_W - 30 * mm])
    ci_table.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 25),
        ("RIGHTPADDING", (0, 0), (-1, -1), 25),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, 0), 0.3, DARK_BORDER),
        ("LINEBELOW", (0, 1), (-1, 1), 0.3, DARK_BORDER),
        ("LINEBELOW", (0, 2), (-1, 2), 0.3, DARK_BORDER),
    ]))
    story.append(ci_table)

    story.append(Spacer(1, 25))

    overall = ddr_data.get("severity_assessment", {}).get("overall", "N/A")
    sev_c = SEVERITY_COLORS.get(overall, DIM)
    sev_bg = SEVERITY_BG.get(overall, DARK_CARD)
    overall_badge = Table(
        [[Paragraph('<font color="%s" size="12"><b>OVERALL SEVERITY: %s</b></font>' % (sev_c.hexval(), overall.upper()),
                    ParagraphStyle("ob", fontSize=12, fontName="Helvetica-Bold", alignment=TA_CENTER, leading=16))]],
        colWidths=[280])
    overall_badge.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), sev_bg),
        ("BOX", (0, 0), (-1, -1), 2, sev_c),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(Table([[overall_badge]], colWidths=[USABLE_W], style=[("ALIGN", (0, 0), (-1, -1), "CENTER")]))

    story.append(Spacer(1, 20))
    story.append(Paragraph("This report is AI-generated from submitted inspection documents.", S["footer"]))
    story.append(Paragraph("Review with a qualified professional before taking action.", S["footer"]))
    story.append(PageBreak())

    # ═══════════════════════════════════════════
    # SECTION 1 — Key Metrics Dashboard
    # ═══════════════════════════════════════════
    story.append(Paragraph("1. Report Dashboard", S["sec"]))
    story.append(Paragraph("Key metrics at a glance", S["sec_line"]))
    story.append(hr_subtle())

    obs_count = len(ddr_data.get("area_observations", []))
    total_pages = "—"
    total_images = "—"
    action_count = len(ddr_data.get("recommended_actions", []))

    metrics_data = [[
        metric_card(obs_count, "Areas Analyzed", AMBER),
        metric_card(action_count, "Actions", ORANGE),
        metric_card(overall.upper(), "Severity", SEVERITY_COLORS.get(overall, DIM)),
    ]]
    metrics_table = Table(metrics_data, colWidths=[USABLE_W / 3] * 3)
    metrics_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(metrics_table)

    story.append(Spacer(1, 14))
    story.append(Paragraph("2. Executive Summary", S["sec"]))
    story.append(Paragraph("High-level overview of findings", S["sec_line"]))
    story.append(hr_subtle())
    summary_text = safe_str(ddr_data.get("property_summary"))
    story.append(Paragraph(summary_text, S["body"]))

    root_causes = ddr_data.get("root_causes", [])
    if root_causes:
        story.append(Spacer(1, 10))
        story.append(Paragraph("Key Findings", S["h2"]))
        rc_rows = [[str(i), safe_str(rc.get("issue")), safe_str(rc.get("cause"))] for i, rc in enumerate(root_causes, 1)]
        story.append(build_table(["#", "Finding", "Details"], rc_rows, [22, 50 * mm, 96 * mm]))

    story.append(PageBreak())

    # ═══════════════════════════════════════════
    # SECTION 3 — Area Observations
    # ═══════════════════════════════════════════
    story.append(Paragraph("3. Area Observations", S["sec"]))
    story.append(Paragraph("Detailed per-area analysis", S["sec_line"]))
    story.append(hr_subtle())

    for idx, obs in enumerate(ddr_data.get("area_observations", []), 1):
        area = safe_str(obs.get("area", "Unknown Area"))
        observation = safe_str(obs.get("observation"))
        thermal = safe_str(obs.get("thermal_finding"))
        severity = safe_str(obs.get("severity", "Low"))
        sev_reason = safe_str(obs.get("severity_reason"))
        img_ref = safe_str(obs.get("image_ref", "Not Available"))

        elements = []

        # Card-style header
        card_header = [[
            Paragraph("<b>Area %d:</b>  %s" % (idx, area), S["h2"]),
            sev_badge(severity),
        ]]
        header_table = Table(card_header, colWidths=[USABLE_W - 82, 82])
        header_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (0, 0), 0),
            ("RIGHTPADDING", (0, 0), (0, 0), 0),
            ("BACKGROUND", (0, 0), (-1, -1), DARK_CARD),
            ("BOX", (0, 0), (-1, -1), 0.5, DARK_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 4))

        # Observation details
        obs_data = [
            [Paragraph('<font color="%s"><b>Finding:</b></font>' % MUTED.hexval(), S["sm"]), Paragraph(observation, S["body"])],
            [Paragraph('<font color="%s"><b>Thermal:</b></font>' % MUTED.hexval(), S["sm"]), Paragraph(thermal, S["body"])],
            [Paragraph('<font color="%s"><b>Reasoning:</b></font>' % MUTED.hexval(), S["sm"]), Paragraph(sev_reason, S["body"])],
        ]
        obs_table = Table(obs_data, colWidths=[22 * mm, USABLE_W - 22 * mm])
        obs_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("BACKGROUND", (0, 0), (-1, -1), DARK_CARD),
            ("BOX", (0, 0), (-1, -1), 0.5, DARK_BORDER),
            ("LINEBELOW", (0, 0), (-1, 0), 0.3, DARK_BORDER),
            ("LINEBELOW", (0, 1), (-1, 1), 0.3, DARK_BORDER),
        ]))
        elements.append(obs_table)

        # Image
        img_element = render_image(img_ref)
        if img_element:
            elements.append(Spacer(1, 6))
            img_wrap = Table([[img_element]], colWidths=[USABLE_W])
            img_wrap.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), DARK_CARD),
                ("BOX", (0, 0), (-1, -1), 0.5, DARK_BORDER),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]))
            elements.append(img_wrap)

        elements.append(Spacer(1, 12))
        story.append(KeepTogether(elements))

    story.append(PageBreak())

    # ═══════════════════════════════════════════
    # SECTION 4 — Severity Assessment
    # ═══════════════════════════════════════════
    story.append(Paragraph("4. Severity Assessment", S["sec"]))
    story.append(Paragraph("Overall risk classification", S["sec_line"]))
    story.append(hr_subtle())

    sa = ddr_data.get("severity_assessment", {})
    ov = safe_str(sa.get("overall"))
    reasoning = safe_str(sa.get("reasoning"))

    sev_card_data = [[
        sev_badge(ov, "Overall: " + ov),
        Paragraph(reasoning, S["body"]),
    ]]
    sev_card = Table(sev_card_data, colWidths=[32 * mm, USABLE_W - 32 * mm])
    sev_card.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
        ("BACKGROUND", (0, 0), (-1, -1), DARK_CARD),
        ("BOX", (0, 0), (-1, -1), 0.5, DARK_BORDER),
    ]))
    story.append(sev_card)

    story.append(PageBreak())

    # ═══════════════════════════════════════════
    # SECTION 5 — Recommended Actions
    # ═══════════════════════════════════════════
    story.append(Paragraph("5. Recommended Actions", S["sec"]))
    story.append(Paragraph("Prioritized remediation plan", S["sec_line"]))
    story.append(hr_subtle())

    actions = ddr_data.get("recommended_actions", [])
    if actions:
        pbg = {
            "Immediate": colors.HexColor("#450A0A"),
            "Short-term": colors.HexColor("#422006"),
            "Long-term": colors.HexColor("#052E16"),
        }
        ptc = {
            "Immediate": colors.HexColor("#EF4444"),
            "Short-term": colors.HexColor("#EAB308"),
            "Long-term": colors.HexColor("#22C55E"),
        }

        for i, act in enumerate(actions, 1):
            priority = safe_str(act.get("priority", "Medium"))
            action_text = safe_str(act.get("action"))
            pri_color = ptc.get(priority, DIM)
            pri_bg = pbg.get(priority, DARK_CARD)

            action_data = [[
                Paragraph(
                    '<font color="%s">●</font> <b>%s</b>' % (pri_color.hexval(), priority),
                    ParagraphStyle("ap", fontSize=9, fontName="Helvetica-Bold", textColor=pri_color, leading=13)
                ),
                Paragraph(action_text, S["body"]),
            ]]
            action_table = Table(action_data, colWidths=[32 * mm, USABLE_W - 32 * mm])
            action_table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("BACKGROUND", (0, 0), (-1, -1), pri_bg),
                ("BOX", (0, 0), (-1, -1), 0.5, DARK_BORDER),
                ("LINEBELOW", (0, 0), (-1, 0), 2, pri_color),
            ]))
            story.append(action_table)
            story.append(Spacer(1, 4))
    else:
        story.append(Paragraph("No recommended actions available.", S["body"]))

    story.append(PageBreak())

    # ═══════════════════════════════════════════
    # SECTION 6 — Additional Notes
    # ═══════════════════════════════════════════
    story.append(Paragraph("6. Additional Notes", S["sec"]))
    story.append(Paragraph("Supplementary observations", S["sec_line"]))
    story.append(hr_subtle())

    notes_text = safe_str(ddr_data.get("additional_notes"))
    notes_card = [[Paragraph(notes_text, S["body"])]]
    notes_table = Table(notes_card, colWidths=[USABLE_W])
    notes_table.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
        ("BACKGROUND", (0, 0), (-1, -1), DARK_CARD),
        ("BOX", (0, 0), (-1, -1), 0.5, DARK_BORDER),
    ]))
    story.append(notes_table)

    story.append(Spacer(1, 16))

    # ═══════════════════════════════════════════
    # SECTION 7 — Information Gaps
    # ═══════════════════════════════════════════
    story.append(Paragraph("7. Information Gaps", S["sec"]))
    story.append(Paragraph("Missing or unclear data points", S["sec_line"]))
    story.append(hr_subtle())

    missing = ddr_data.get("missing_or_unclear", [])
    if missing:
        gap_items = []
        for item in missing:
            gap_items.append([Paragraph("—  %s" % item, S["bul"])])
        gap_table = Table(gap_items, colWidths=[USABLE_W])
        gap_table.setStyle(TableStyle([
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 16),
            ("RIGHTPADDING", (0, 0), (-1, -1), 16),
            ("BACKGROUND", (0, 0), (-1, -1), DARK_CARD),
            ("BOX", (0, 0), (-1, -1), 0.5, DARK_BORDER),
        ]))
        story.append(gap_table)
    else:
        story.append(Paragraph("All key information was present in the documents.", S["body"]))

    story.append(Spacer(1, 30))
    story.append(hr_amber(2))
    story.append(Spacer(1, 10))
    story.append(Paragraph("End of Report — Generated by Agentic DDR", S["footer"]))
    story.append(Paragraph("Prepared for %s on %s" % (client_name, datetime.now().strftime("%Y-%m-%d %H:%M")), S["footer"]))

    doc.build(story)
    print("    [OK] PDF built: %s" % output_path)
