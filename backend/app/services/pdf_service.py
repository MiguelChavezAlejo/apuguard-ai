from io import BytesIO
from textwrap import shorten
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    PageTemplate,
    Paragraph,
    PageBreak,
    Spacer,
    Table,
    TableStyle,
)

from app.schemas.report import SecurityReportResponse


class PdfService:
    PAGE_WIDTH, PAGE_HEIGHT = A4

    NAVY = colors.HexColor("#0F172A")
    BLUE = colors.HexColor("#1D4ED8")
    LIGHT_BLUE = colors.HexColor("#DBEAFE")
    SLATE = colors.HexColor("#475569")
    LIGHT_GRAY = colors.HexColor("#F1F5F9")
    BORDER = colors.HexColor("#CBD5E1")
    WHITE = colors.white

    RISK_COLORS = {
        "CRITICAL": colors.HexColor("#7F1D1D"),
        "HIGH": colors.HexColor("#DC2626"),
        "MEDIUM": colors.HexColor("#D97706"),
        "LOW": colors.HexColor("#2563EB"),
        "INFORMATIONAL": colors.HexColor("#64748B"),
    }

    @classmethod
    def _styles(cls):
        styles = getSampleStyleSheet()

        styles.add(
            ParagraphStyle(
                name="CoverTitle",
                parent=styles["Title"],
                fontName="Helvetica-Bold",
                fontSize=30,
                leading=36,
                textColor=cls.WHITE,
                alignment=TA_CENTER,
                spaceAfter=16,
            )
        )

        styles.add(
            ParagraphStyle(
                name="CoverSubtitle",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=13,
                leading=18,
                textColor=colors.HexColor("#CBD5E1"),
                alignment=TA_CENTER,
            )
        )

        styles.add(
            ParagraphStyle(
                name="SectionTitle",
                parent=styles["Heading2"],
                fontName="Helvetica-Bold",
                fontSize=15,
                leading=19,
                textColor=cls.NAVY,
                spaceBefore=14,
                spaceAfter=8,
            )
        )

        styles.add(
            ParagraphStyle(
                name="SubsectionTitle",
                parent=styles["Heading3"],
                fontName="Helvetica-Bold",
                fontSize=11,
                leading=15,
                textColor=cls.BLUE,
                spaceBefore=8,
                spaceAfter=5,
            )
        )

        styles.add(
            ParagraphStyle(
                name="BodyCustom",
                parent=styles["BodyText"],
                fontName="Helvetica",
                fontSize=9,
                leading=13,
                textColor=cls.NAVY,
                alignment=TA_JUSTIFY,
                spaceAfter=7,
            )
        )

        styles.add(
            ParagraphStyle(
                name="SmallCustom",
                parent=styles["BodyText"],
                fontName="Helvetica",
                fontSize=7.5,
                leading=10,
                textColor=cls.SLATE,
                alignment=TA_LEFT,
            )
        )

        styles.add(
            ParagraphStyle(
                name="WhiteSmall",
                parent=styles["BodyText"],
                fontName="Helvetica",
                fontSize=8,
                leading=11,
                textColor=cls.WHITE,
                alignment=TA_CENTER,
            )
        )

        return styles

    @classmethod
    def _header_footer(cls, canvas, doc):
        canvas.saveState()

        if doc.page > 1:
            canvas.setFillColor(cls.NAVY)
            canvas.rect(
                0,
                cls.PAGE_HEIGHT - 1.25 * cm,
                cls.PAGE_WIDTH,
                1.25 * cm,
                fill=1,
                stroke=0,
            )

            canvas.setFillColor(cls.WHITE)
            canvas.setFont("Helvetica-Bold", 9)
            canvas.drawString(
                1.5 * cm,
                cls.PAGE_HEIGHT - 0.8 * cm,
                "ApuGuard AI - Informe de Seguridad",
            )

            canvas.setFillColor(cls.SLATE)
            canvas.setFont("Helvetica", 8)
            canvas.drawRightString(
                cls.PAGE_WIDTH - 1.5 * cm,
                0.8 * cm,
                f"Página {doc.page}",
            )

            canvas.setStrokeColor(cls.BORDER)
            canvas.line(
                1.5 * cm,
                1.1 * cm,
                cls.PAGE_WIDTH - 1.5 * cm,
                1.1 * cm,
            )

            canvas.setFillColor(cls.SLATE)
            canvas.setFont("Helvetica", 7)
            canvas.drawString(
                1.5 * cm,
                0.55 * cm,
                "Uso autorizado exclusivamente para evaluación de seguridad.",
            )

        canvas.restoreState()

    @classmethod
    def _risk_badge(cls, report, styles):
        risk = report.overall_risk.upper()
        risk_color = cls.RISK_COLORS.get(risk, cls.SLATE)

        data = [
            [
                Paragraph(
                    "<b>NIVEL DE RIESGO GENERAL</b>",
                    styles["WhiteSmall"],
                ),
                Paragraph(
                    f"<b>{escape(risk)}</b>",
                    styles["WhiteSmall"],
                ),
            ]
        ]

        table = Table(
            data,
            colWidths=[10.5 * cm, 5 * cm],
            rowHeights=[0.85 * cm],
        )

        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, 0), cls.NAVY),
                    ("BACKGROUND", (1, 0), (1, 0), risk_color),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("BOX", (0, 0), (-1, -1), 0.5, cls.BORDER),
                ]
            )
        )

        return table

    @classmethod
    def _distribution_table(cls, report, styles):
        distribution = report.risk_distribution

        rows = [
            ["Severidad", "Cantidad"],
            ["Crítica", distribution.critical],
            ["Alta", distribution.high],
            ["Media", distribution.medium],
            ["Baja", distribution.low],
            ["Informativa", distribution.informational],
        ]

        table = Table(
            rows,
            colWidths=[9 * cm, 6.5 * cm],
            repeatRows=1,
        )

        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), cls.NAVY),
                    ("TEXTCOLOR", (0, 0), (-1, 0), cls.WHITE),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("ALIGN", (1, 1), (1, -1), "CENTER"),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("BACKGROUND", (0, 1), (-1, -1), cls.LIGHT_GRAY),
                    ("GRID", (0, 0), (-1, -1), 0.5, cls.BORDER),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ]
            )
        )

        return table

    @classmethod
    def _findings_summary_table(cls, report, styles):
        rows = [
            [
                Paragraph("<b>Hallazgo</b>", styles["SmallCustom"]),
                Paragraph("<b>Severidad</b>", styles["SmallCustom"]),
                Paragraph("<b>Ocurrencias</b>", styles["SmallCustom"]),
                Paragraph("<b>CWE</b>", styles["SmallCustom"]),
            ]
        ]

        for finding in report.findings[:30]:
            rows.append(
                [
                    Paragraph(
                        escape(shorten(finding.name, width=60)),
                        styles["SmallCustom"],
                    ),
                    Paragraph(
                        escape(finding.severity),
                        styles["SmallCustom"],
                    ),
                    str(finding.occurrences),
                    str(finding.cwe_id or "-"),
                ]
            )

        table = Table(
            rows,
            colWidths=[8.5 * cm, 2.7 * cm, 2.3 * cm, 2 * cm],
            repeatRows=1,
        )

        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), cls.NAVY),
                    ("TEXTCOLOR", (0, 0), (-1, 0), cls.WHITE),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                    ("GRID", (0, 0), (-1, -1), 0.4, cls.BORDER),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
                        cls.WHITE,
                        cls.LIGHT_GRAY,
                    ]),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )

        return table

    @classmethod
    def generate_pdf(
        cls,
        report: SecurityReportResponse,
    ) -> bytes:
        buffer = BytesIO()
        styles = cls._styles()

        document = BaseDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=1.5 * cm,
            leftMargin=1.5 * cm,
            topMargin=1.7 * cm,
            bottomMargin=1.5 * cm,
            title=f"Reporte de Seguridad - {report.project_name}",
            author="ApuGuard AI",
            subject="Informe de análisis de vulnerabilidades",
        )

        frame = Frame(
            document.leftMargin,
            document.bottomMargin,
            document.width,
            document.height,
            id="normal",
        )

        document.addPageTemplates(
            [
                PageTemplate(
                    id="report",
                    frames=[frame],
                    onPage=cls._header_footer,
                )
            ]
        )

        story = []

        # Portada
        cover_table = Table(
            [
                [
                    Paragraph(
                        "ApuGuard AI",
                        styles["CoverTitle"],
                    )
                ],
                [
                    Paragraph(
                        "Plataforma autónoma de pentesting inteligente",
                        styles["CoverSubtitle"],
                    )
                ],
                [
                    Spacer(1, 1.2 * cm)
                ],
                [
                    Paragraph(
                        "INFORME PROFESIONAL DE SEGURIDAD",
                        styles["CoverSubtitle"],
                    )
                ],
                [
                    Spacer(1, 1 * cm)
                ],
                [
                    Paragraph(
                        f"<b>Proyecto:</b> {escape(report.project_name)}",
                        styles["CoverSubtitle"],
                    )
                ],
                [
                    Paragraph(
                        f"<b>Objetivo:</b> {escape(report.target_url)}",
                        styles["CoverSubtitle"],
                    )
                ],
                [
                    Paragraph(
                        (
                            "<b>Fecha:</b> "
                            f"{report.generated_at.strftime('%d/%m/%Y %H:%M UTC')}"
                        ),
                        styles["CoverSubtitle"],
                    )
                ],
                [
                    Paragraph(
                        (
                            "<b>Proveedor del análisis:</b> "
                            f"{escape(report.ai_provider)}"
                        ),
                        styles["CoverSubtitle"],
                    )
                ],
            ],
            colWidths=[16.5 * cm],
            rowHeights=[
                1.6 * cm,
                1 * cm,
                1.3 * cm,
                1 * cm,
                1 * cm,
                0.7 * cm,
                0.7 * cm,
                0.7 * cm,
                0.7 * cm,
            ],
        )

        cover_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), cls.NAVY),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("BOX", (0, 0), (-1, -1), 0, cls.NAVY),
                    ("TOPPADDING", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ]
            )
        )

        story.append(Spacer(1, 2.5 * cm))
        story.append(cover_table)
        story.append(Spacer(1, 1.5 * cm))
        story.append(cls._risk_badge(report, styles))
        story.append(PageBreak())

        # Resumen ejecutivo
        story.append(
            Paragraph(
                "1. Resumen ejecutivo",
                styles["SectionTitle"],
            )
        )
        story.append(
            Paragraph(
                escape(report.executive_summary),
                styles["BodyCustom"],
            )
        )

        story.append(
            Paragraph(
                "2. Información del análisis",
                styles["SectionTitle"],
            )
        )

        project_data = [
            ["Proyecto", report.project_name],
            ["Objetivo", report.target_url],
            ["Identificador del escaneo", str(report.scan_id)],
            ["Nivel de riesgo", report.overall_risk],
            ["Proveedor del reporte", report.ai_provider],
            [
                "Fecha de generación",
                report.generated_at.strftime("%d/%m/%Y %H:%M UTC"),
            ],
        ]

        info_table = Table(
            project_data,
            colWidths=[5 * cm, 10.5 * cm],
        )

        info_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), cls.LIGHT_BLUE),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                    ("GRID", (0, 0), (-1, -1), 0.5, cls.BORDER),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )

        story.append(info_table)

        story.append(
            Paragraph(
                "3. Distribución de riesgos",
                styles["SectionTitle"],
            )
        )
        story.append(cls._distribution_table(report, styles))

        story.append(
            Paragraph(
                "4. Resumen técnico",
                styles["SectionTitle"],
            )
        )
        story.append(
            Paragraph(
                escape(report.technical_summary),
                styles["BodyCustom"],
            )
        )

        story.append(PageBreak())

        # Hallazgos
        story.append(
            Paragraph(
                "5. Hallazgos consolidados",
                styles["SectionTitle"],
            )
        )

        if report.findings:
            story.append(
                cls._findings_summary_table(report, styles)
            )
        else:
            story.append(
                Paragraph(
                    "No se identificaron hallazgos para mostrar.",
                    styles["BodyCustom"],
                )
            )

        story.append(
            Paragraph(
                "6. Detalle de hallazgos prioritarios",
                styles["SectionTitle"],
            )
        )

        for index, finding in enumerate(report.findings[:15], start=1):
            urls = "<br/>".join(
                escape(url)
                for url in finding.affected_urls[:3]
            ) or "Sin URL registrada"

            detail_data = [
                [
                    Paragraph(
                        (
                            f"<b>{index}. "
                            f"{escape(finding.name)}</b>"
                        ),
                        styles["SubsectionTitle"],
                    )
                ],
                [
                    Paragraph(
                        (
                            f"<b>Severidad:</b> "
                            f"{escape(finding.severity)} | "
                            f"<b>Ocurrencias:</b> "
                            f"{finding.occurrences} | "
                            f"<b>CWE:</b> "
                            f"{finding.cwe_id or '-'}"
                        ),
                        styles["SmallCustom"],
                    )
                ],
                [
                    Paragraph(
                        (
                            "<b>Categoría OWASP:</b> "
                            f"{escape(finding.owasp_category or 'No clasificada')}"
                        ),
                        styles["SmallCustom"],
                    )
                ],
                [
                    Paragraph(
                        (
                            "<b>Descripción:</b><br/>"
                            f"{escape(finding.description or 'Sin descripción.')}"
                        ),
                        styles["BodyCustom"],
                    )
                ],
                [
                    Paragraph(
                        (
                            "<b>Recomendación:</b><br/>"
                            f"{escape(finding.recommendation or 'Revisión manual requerida.')}"
                        ),
                        styles["BodyCustom"],
                    )
                ],
                [
                    Paragraph(
                        f"<b>URLs representativas:</b><br/>{urls}",
                        styles["SmallCustom"],
                    )
                ],
            ]

            detail_table = Table(
                detail_data,
                colWidths=[15.5 * cm],
            )

            detail_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), cls.LIGHT_BLUE),
                        ("BACKGROUND", (0, 1), (-1, -1), cls.WHITE),
                        ("BOX", (0, 0), (-1, -1), 0.6, cls.BORDER),
                        ("INNERGRID", (0, 0), (-1, -1), 0.3, cls.BORDER),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 8),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                        ("TOPPADDING", (0, 0), (-1, -1), 6),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )

            story.append(
                KeepTogether(
                    [
                        detail_table,
                        Spacer(1, 0.25 * cm),
                    ]
                )
            )

        story.append(PageBreak())

        # Acciones
        story.append(
            Paragraph(
                "7. Plan priorizado de remediación",
                styles["SectionTitle"],
            )
        )

        for index, action in enumerate(
            report.prioritized_actions,
            start=1,
        ):
            story.append(
                Paragraph(
                    f"<b>{index}.</b> {escape(action)}",
                    styles["BodyCustom"],
                )
            )

        story.append(
            Paragraph(
                "8. Conclusiones",
                styles["SectionTitle"],
            )
        )
        story.append(
            Paragraph(
                escape(report.conclusions),
                styles["BodyCustom"],
            )
        )

        story.append(
            Paragraph(
                "9. Consideraciones y alcance",
                styles["SectionTitle"],
            )
        )
        story.append(
            Paragraph(
                (
                    "Este informe corresponde a una evaluación automatizada "
                    "realizada mediante OWASP ZAP sobre un entorno de laboratorio "
                    "autorizado. Los resultados deben validarse mediante revisión "
                    "manual antes de aplicarse en un entorno productivo. "
                    "ApuGuard AI no debe utilizarse contra sistemas sin autorización "
                    "expresa del propietario."
                ),
                styles["BodyCustom"],
            )
        )

        document.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()

        return pdf_bytes