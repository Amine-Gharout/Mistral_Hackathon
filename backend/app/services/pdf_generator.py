"""PDF report generator using fpdf2."""

from __future__ import annotations

import io
import json
from datetime import datetime
from typing import Optional

from fpdf import FPDF

from ..models.report import EntitlementReport


class GreenRightsPDF(FPDF):
    """Custom PDF class for GreenRights reports."""

    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(34, 139, 34)  # Forest green
        self.cell(0, 10, "GreenRights", border=0, align="L")
        self.set_font("Helvetica", "", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Genere le {datetime.now().strftime('%d/%m/%Y')}",
                  border=0, align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(34, 139, 34)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def add_section_title(self, title: str):
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(34, 100, 34)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def add_subsection(self, title: str):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(60, 60, 60)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")

    def add_body_text(self, text: str):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(40, 40, 40)
        self.multi_cell(0, 6, text)
        self.ln(2)

    def add_amount_line(self, label: str, amount: float, note: str = ""):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(40, 40, 40)
        self.cell(120, 7, f"  {label}", border=0)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(34, 139, 34)
        amount_str = f"{amount:,.0f} EUR".replace(",", " ")
        self.cell(30, 7, amount_str, border=0, align="R")
        if note:
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(128, 128, 128)
            self.cell(30, 7, f"  {note}", border=0)
        self.ln(7)

    def add_warning(self, text: str):
        self.set_fill_color(255, 243, 205)
        self.set_font("Helvetica", "I", 9)
        self.set_text_color(133, 100, 4)
        self.cell(0, 8, f"  Attention : {text}",
                  fill=True, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)


def generate_report_pdf(report: EntitlementReport) -> bytes:
    """Generate a PDF report from an EntitlementReport and return bytes."""
    pdf = GreenRightsPDF()
    pdf.alias_nb_pages()
    pdf.add_page()

    # ── Title ──
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(34, 139, 34)
    pdf.cell(0, 12, "Votre bilan d'aides a la transition ecologique",
             align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # ── Renovation aids ──
    if report.renovation_aids:
        pdf.add_section_title("Aides a la renovation energetique")

        for aid in report.renovation_aids:
            label = aid.label_fr or aid.aid_id
            pdf.add_amount_line(label, aid.amount)
            if aid.conditions:
                for cond in aid.conditions[:2]:
                    pdf.set_font("Helvetica", "I", 8)
                    pdf.set_text_color(100, 100, 100)
                    pdf.cell(
                        0, 5, f"    Condition: {cond}", new_x="LMARGIN", new_y="NEXT")
            if aid.source:
                pdf.set_font("Helvetica", "I", 8)
                pdf.set_text_color(100, 100, 100)
                pdf.cell(
                    0, 5, f"    Source: {aid.source}", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)

    # ── Mobility aids ──
    if report.mobility_aids:
        pdf.add_section_title("Aides a la mobilite propre")

        for aid in report.mobility_aids:
            label = aid.label_fr or aid.aid_id
            pdf.add_amount_line(label, aid.amount)
            if aid.source:
                pdf.set_font("Helvetica", "I", 8)
                pdf.set_text_color(100, 100, 100)
                pdf.cell(
                    0, 5, f"    Source: {aid.source}", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)

    # ── Eco-PTZ ──
    if report.eco_ptz:
        pdf.add_section_title("Eco-PTZ (Pret a taux zero)")
        ecoptz = report.eco_ptz
        pdf.add_amount_line(
            f"Montant maximum empruntable",
            ecoptz.max_amount,
            f"Duree: {ecoptz.duration_years} ans"
        )
        pdf.ln(2)

    # ── Stacking ──
    if report.stacking:
        pdf.add_section_title("Cumul des aides")
        stacking = report.stacking
        if stacking.compatible:
            pdf.add_body_text("Les aides selectionnees sont cumulables.")
        if stacking.warnings:
            for w in stacking.warnings:
                pdf.add_warning(w)

    # ── Totals ──
    pdf.add_section_title("Estimation totale")
    pdf.set_draw_color(34, 139, 34)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)

    if report.total_conservative:
        pdf.add_amount_line("Estimation basse (conservatrice)",
                            report.total_conservative)
    if report.total_optimistic:
        pdf.add_amount_line("Estimation haute (optimiste)",
                            report.total_optimistic)

    pdf.ln(5)

    # ── Action steps ──
    if report.action_steps:
        pdf.add_section_title("Plan d'action")
        for i, step in enumerate(report.action_steps, 1):
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(40, 40, 40)
            pdf.cell(0, 7, f"Etape {i}: {step.title}",
                     new_x="LMARGIN", new_y="NEXT")
            pdf.add_body_text(step.description)
            if step.url:
                pdf.set_font("Helvetica", "", 8)
                pdf.set_text_color(0, 0, 200)
                pdf.cell(0, 5, step.url, new_x="LMARGIN", new_y="NEXT")
                pdf.ln(2)

    # ── Sources ──
    if report.sources:
        pdf.add_section_title("Sources")
        for src in report.sources:
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(60, 60, 60)
            pdf.cell(0, 5, f"- {src}", new_x="LMARGIN", new_y="NEXT")

    # ── Disclaimer ──
    pdf.ln(10)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(128, 128, 128)
    pdf.multi_cell(0, 4, (
        "Ce document est genere automatiquement par GreenRights a titre informatif uniquement. "
        "Les montants sont calcules sur la base des baremes officiels en vigueur mais peuvent varier "
        "selon votre situation specifique. Consultez un conseiller France Renov' pour une evaluation "
        "definitive. Les donnees utilisees datent de mars 2026."
    ))

    return pdf.output()
