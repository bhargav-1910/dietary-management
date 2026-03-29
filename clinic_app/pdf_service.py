from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


class PDFService:
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _as_path(output_path: str | Path | None, default_path: Path) -> Path:
        if output_path is None:
            return default_path
        return Path(output_path)

    def generate_invoice_pdf(
        self,
        quotation_id: int,
        patient: dict[str, Any],
        selected_items: list[dict[str, Any]],
        totals: dict[str, float],
        quotation_date: str,
        output_path: str | Path | None = None,
        invoice_number: str | None = None,
    ) -> Path:
        file_path = self._as_path(output_path, self.output_dir / f"invoice_{quotation_id}.pdf")
        file_path.parent.mkdir(parents=True, exist_ok=True)

        doc = SimpleDocTemplate(str(file_path), pagesize=A4, rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
        styles = getSampleStyleSheet()
        elements: list[Any] = []
        invoice_label = invoice_number or f"INV-{quotation_id:04d}"

        elements.append(Paragraph("Dietary Clinic", styles["Title"]))
        elements.append(Paragraph(f"Invoice Number: {invoice_label}", styles["Normal"]))
        elements.append(Paragraph(f"Date: {quotation_date}", styles["Normal"]))
        elements.append(Spacer(1, 8))

        patient_text = (
            f"Patient: {patient['name']}<br/>"
            f"Age/Gender: {patient.get('age', '-')}/{patient.get('gender', '-')}<br/>"
            f"Phone: {patient.get('phone', '-')}"
        )
        elements.append(Paragraph(patient_text, styles["Normal"]))
        elements.append(Spacer(1, 12))

        table_data = [["Product", "Qty", "Base Price", "Tax %", "Line Total"]]
        for item in selected_items:
            qty = int(item["quantity"])
            base = float(item["base_price"])
            tax_percent = float(item["tax_percent"])
            line_total = (base + (base * tax_percent / 100.0)) * qty
            table_data.append(
                [
                    item["name"],
                    str(qty),
                    f"{base:.2f}",
                    f"{tax_percent:.0f}%",
                    f"{line_total:.2f}",
                ]
            )

        table = Table(table_data, colWidths=[70 * mm, 20 * mm, 30 * mm, 20 * mm, 30 * mm])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ]
            )
        )
        elements.append(table)
        elements.append(Spacer(1, 10))

        elements.append(Paragraph(f"Subtotal: {totals['subtotal']:.2f}", styles["Normal"]))
        elements.append(Paragraph(f"Tax: {totals['total_tax']:.2f}", styles["Normal"]))
        elements.append(Paragraph(f"Grand Total: {totals['grand_total']:.2f}", styles["Heading3"]))

        doc.build(elements)
        return file_path

    def generate_package_sheet(
        self,
        patient: dict[str, Any],
        selected_items: list[dict[str, Any]],
        output_path: str | Path | None = None,
    ) -> Path:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = self._as_path(output_path, self.output_dir / f"package_sheet_{patient['id']}_{stamp}.pdf")
        file_path.parent.mkdir(parents=True, exist_ok=True)

        doc = SimpleDocTemplate(str(file_path), pagesize=A4, rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
        styles = getSampleStyleSheet()
        elements: list[Any] = []

        elements.append(Paragraph("Package Sheet", styles["Title"]))
        elements.append(Paragraph(f"Patient: {patient['name']}", styles["Heading3"]))
        elements.append(Paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d')}", styles["Normal"]))
        elements.append(Spacer(1, 12))

        data = [["Selected Products"]]
        for item in selected_items:
            data.append([item["name"]])

        table = Table(data, colWidths=[150 * mm])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ]
            )
        )
        elements.append(table)

        doc.build(elements)
        return file_path
