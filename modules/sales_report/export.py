# Ubicación: C:\Users\hecto\Documents\Prg_locales\I_R_G\modules\sales_report\export.py
import pandas as pd
import zipfile
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

class ExportManager:
    """Gestor de exportación robusto con soporte para jerarquías y empaquetado ZIP."""

    @staticmethod
    def _prepare_pdf_buffer():
        return BytesIO()

    @staticmethod
    def _create_table_style(df, header_color="#2563EB"):
        style_list = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(header_color)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]

        for i, row in enumerate(df.values):
            row_str = " ".join([str(c) for c in row]).upper()
            row_idx = i + 1
            # Resaltado para subtotales (Marcas) y Totales (Vendedores)
            if "Σ" in row_str or "TOTAL" in row_str or "==" in row_str:
                style_list.append(('FONTNAME', (0, row_idx), (-1, row_idx), 'Helvetica-Bold'))
                style_list.append(('BACKGROUND', (0, row_idx), (-1, row_idx), colors.HexColor("#F1F5F9")))

            # Línea divisoria robusta para el final del reporte del vendedor
            if "Σ TOTAL" in row_str or "TOTAL GENERAL" in row_str:
                style_list.append(('LINEABOVE', (0, row_idx), (-1, row_idx), 1.5, colors.black))

        return TableStyle(style_list)

    @staticmethod
    def _clean_df_for_print(df, columns=['Vendedor', 'Marca']):
        df_print = df.copy()
        for col in columns:
            if col in df_print.columns:
                mask = (df_print[col] == df_print[col].shift()) & \
                       (~df_print.astype(str).apply(lambda x: x.str.contains("Σ|TOTAL|==", na=False)).any(axis=1))
                df_print.loc[mask, col] = ""
        return df_print

    @staticmethod
    def generate_single_table_pdf(df, title, subtitle=""):
        if df is None or df.empty: return None
        df_clean = ExportManager._clean_df_for_print(df)
        buffer = ExportManager._prepare_pdf_buffer()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter),
                               leftMargin=30, rightMargin=30, topMargin=30, bottomMargin=30)

        styles = getSampleStyleSheet()
        elements = [Paragraph(f"<b>{title}</b>", styles['Title'])]
        if subtitle: elements.append(Paragraph(subtitle, styles['Normal']))
        elements.append(Spacer(1, 20))

        data = [df_clean.columns.to_list()] + df_clean.values.tolist()
        t = Table(data, hAlign='CENTER', repeatRows=1)
        t.setStyle(ExportManager._create_table_style(df_clean))

        elements.append(t)
        doc.build(elements)
        buffer.seek(0)
        return buffer

    @staticmethod
    def generate_batch_zip_reports(df_det_vendedor):
        """Genera un archivo ZIP con PDFs que incluyen la fila de total calculada en SalesLogic."""
        # Identificar vendedores reales omitiendo etiquetas de totales
        vendedores = [v for v in df_det_vendedor['Vendedor'].unique()
                     if v and str(v).strip() != "" and "Σ" not in str(v) and "TOTAL" not in str(v)]

        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for vendedor in vendedores:
                # Filtrar el cuerpo del vendedor Y su fila de total correspondiente (ya creada en logic.py)
                mask = (df_det_vendedor['Vendedor'] == vendedor) | \
                       (df_det_vendedor['Vendedor'] == f"Σ TOTAL {vendedor}")

                df_v = df_det_vendedor[mask].copy()

                if not df_v.empty:
                    pdf_data = ExportManager.generate_single_table_pdf(
                        df_v,
                        f"REPORTE DE GESTIÓN: {vendedor}",
                        "Auditoría de Ventas por Marca y Cliente"
                    )
                    if pdf_data:
                        zf.writestr(f"Reporte_{vendedor}.pdf", pdf_data.getvalue())

        zip_buffer.seek(0)
        return zip_buffer

    @staticmethod
    def generate_consolidated_report(data_dict, main_title="AUDITORÍA INTEGRAL DE VENTAS 360°"):
        if not data_dict: return None
        buffer = ExportManager._prepare_pdf_buffer()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
        styles = getSampleStyleSheet()
        elements = [Paragraph(f"<b>{main_title}</b>", styles['Title']), Spacer(1, 20)]

        for section_name, df in data_dict.items():
            if df is None or df.empty: continue
            elements.append(Paragraph(f"<b>{section_name.upper()}</b>", styles['Heading2']))

            df_to_print = ExportManager._clean_df_for_print(df) if "DETALLE" in section_name.upper() else df
            data = [df_to_print.columns.to_list()] + df_to_print.values.tolist()
            t = Table(data, hAlign='CENTER', repeatRows=1)
            t.setStyle(ExportManager._create_table_style(df_to_print))

            elements.append(t)
            elements.append(PageBreak() if "DETALLE" in section_name.upper() else Spacer(1, 25))

        doc.build(elements)
        buffer.seek(0)
        return buffer