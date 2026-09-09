"""Client-facing PDF document rendering for Black Office records."""
from __future__ import annotations

from io import BytesIO
from html import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.core.models import Agreement, Business, Client, Invoice, Project


def _money(currency: str, amount) -> str:
    return f"{currency} {amount:.2f}"


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Meta", parent=styles["BodyText"], textColor=colors.HexColor("#555555"), fontSize=9, leading=12))
    styles.add(ParagraphStyle(name="Right", parent=styles["BodyText"], alignment=TA_RIGHT))
    styles.add(ParagraphStyle(name="Warning", parent=styles["BodyText"], textColor=colors.HexColor("#6E4B00"), backColor=colors.HexColor("#FFF4D6"), borderPadding=8, leading=13))
    return styles


def build_agreement_pdf(*, business: Business, agreement: Agreement, project: Project | None, client: Client | None) -> bytes:
    buffer = BytesIO()
    styles = _styles()
    doc = SimpleDocTemplate(buffer, pagesize=LETTER, rightMargin=0.65 * inch, leftMargin=0.65 * inch, topMargin=0.65 * inch, bottomMargin=0.65 * inch, title=agreement.title, author=business.name)
    story = [
        Paragraph(escape(business.name), styles["Title"]),
        Paragraph("AGREEMENT", styles["Heading2"]),
        Paragraph(f"Record: {escape(agreement.agreement_id)} | Status: {escape(agreement.status.value.upper())}", styles["Meta"]),
        Spacer(1, 14),
    ]
    context = []
    if client is not None:
        context.append(["Client", escape(client.name)])
    if project is not None:
        context.append(["Project", escape(project.name)])
    if agreement.amount is not None:
        context.append(["Agreed price", _money(agreement.currency, agreement.amount)])
    if context:
        table = Table(context, colWidths=[1.35 * inch, 5.55 * inch])
        table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#DDDDDD")),
        ]))
        story.extend([table, Spacer(1, 18)])
    story.extend([
        Paragraph(escape(agreement.title), styles["Heading1"]),
        Spacer(1, 8),
        Paragraph(escape(agreement.scope).replace("\n", "<br/>"), styles["BodyText"]),
        Spacer(1, 24),
        Paragraph("This document reflects the terms recorded in the Black Office. Client acceptance is a separate event from internal preparation or proposal status.", styles["Meta"]),
    ])
    doc.build(story)
    return buffer.getvalue()


def build_invoice_pdf(*, business: Business, invoice: Invoice, project: Project | None, client: Client | None) -> bytes:
    buffer = BytesIO()
    styles = _styles()
    doc = SimpleDocTemplate(buffer, pagesize=LETTER, rightMargin=0.65 * inch, leftMargin=0.65 * inch, topMargin=0.65 * inch, bottomMargin=0.65 * inch, title=invoice.invoice_id, author=business.name)
    story = [
        Paragraph(escape(business.name), styles["Title"]),
        Paragraph("INVOICE", styles["Heading2"]),
        Paragraph(f"Invoice: {escape(invoice.invoice_id)} | Status: {escape(invoice.status.value.upper())}", styles["Meta"]),
        Spacer(1, 14),
    ]
    context = []
    if client is not None:
        context.append(["Bill to", escape(client.name)])
    if project is not None:
        context.append(["Project", escape(project.name)])
    if invoice.due_date is not None:
        context.append(["Due date", invoice.due_date.isoformat()])
    if invoice.agreement_id:
        context.append(["Agreement", escape(invoice.agreement_id)])
    if context:
        table = Table(context, colWidths=[1.35 * inch, 5.55 * inch])
        table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#DDDDDD")),
        ]))
        story.extend([table, Spacer(1, 18)])

    rows = [[Paragraph("Description", styles["BodyText"]), Paragraph("Amount", styles["Right"])]]
    for line in invoice.line_items:
        rows.append([Paragraph(escape(line.description), styles["BodyText"]), Paragraph(_money(invoice.currency, line.amount), styles["Right"])])
    if not invoice.line_items:
        rows.append([Paragraph("No persisted line items", styles["Meta"]), Paragraph(_money(invoice.currency, invoice.total), styles["Right"])])
    line_table = Table(rows, colWidths=[5.3 * inch, 1.6 * inch], repeatRows=1)
    line_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEEEEE")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CCCCCC")),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.extend([line_table, Spacer(1, 14)])

    subtotal = invoice.subtotal if invoice.subtotal is not None else invoice.total
    totals = [["Subtotal", _money(invoice.currency, subtotal)]]
    if invoice.tax_total is not None:
        totals.append(["Tax", _money(invoice.currency, invoice.tax_total)])
    totals.append(["Total", _money(invoice.currency, invoice.total)])
    total_table = Table(totals, colWidths=[5.3 * inch, 1.6 * inch])
    total_table.setStyle(TableStyle([
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("LINEABOVE", (0, -1), (-1, -1), 0.8, colors.black),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.extend([total_table, Spacer(1, 16)])
    if invoice.tax_total is None:
        story.append(Paragraph("Tax treatment has not been resolved. Review tax before issuing this invoice.", styles["Warning"]))
        story.append(Spacer(1, 10))
    for note in invoice.review_notes:
        story.append(Paragraph(escape(note), styles["Meta"]))
    doc.build(story)
    return buffer.getvalue()
