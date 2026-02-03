# Ubicación: C:\Users\hecto\Documents\Prg_locales\I_R_G\modules\sales_report\export.py
import pandas as pd
import zipfile
import sys
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet

class ExportManager:
    """Gestor de exportación v6.4: Matriz 10 cols con Mes, Subtotales de Marca y Estilo Pastel."""

    @staticmethod
    def _log_terminal(msg, level="EXPORT"):
        """Reporte directo a la terminal de VS Code para depuración."""
        print(f"\033[95m[{level}]\033[0m {msg}", file=sys.stderr)

    @staticmethod
    def _prepare_pdf_buffer():
        return BytesIO()

    @staticmethod
    def _clean_df_for_print(df):
        """Limpia duplicados y trunca texto largo para evitar desbordamiento en celdas."""
        if df is None or df.empty: return df
        df_print = df.copy()

        # 1. Truncado de seguridad para evitar invasión de celdas
        trunc_map = {'Vendedor': 15, 'Cadena': 25, 'Marca': 12, 'Cliente': 25, 'Identificador': 25}
        for col, length in trunc_map.items():
            if col in df_print.columns:
                df_print[col] = df_print[col].astype(str).apply(lambda x: x[:length] if len(x) > length else x)

        # 2. Limpieza de etiquetas consecutivas (Minimalismo)
        # No ocultamos en filas que contengan Σ o ==
        cols_to_clean = [c for c in ['Vendedor', 'Cadena', 'Marca', 'Cliente', 'Identificador', 'Mes'] if c in df_print.columns]
        for col in cols_to_clean:
            is_summary = df_print.astype(str).apply(lambda x: x.str.contains("Σ|TOTAL|==", na=False)).any(axis=1)
            mask = (df_print[col] == df_print[col].shift()) & (~is_summary)
            df_print.loc[mask, col] = ""

        return df_print

    @staticmethod
    def _create_table_style(df, header_color="#1E3A8A"):
        """Define la estética de la tabla: Colores pastel para Marcas y Clientes."""
        style_list = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(header_color)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]

        # Aplicar colores por contenido de fila
        for i, row in enumerate(df.values):
            idx = i + 1
            row_str = " ".join([str(c) for c in row]).upper()

            # 1. TOTAL GENERAL (Azul Pastel)
            if "TOTAL" in row_str or "==" in row_str:
                style_list.append(('BACKGROUND', (0, idx), (-1, idx), colors.HexColor("#E0F2FE")))
                style_list.append(('FONTNAME', (0, idx), (-1, idx), 'Helvetica-Bold'))

            # 2. SUBREPORTE CLIENTE (Verde Pastel)
            elif "Σ CLIENTE" in row_str:
                style_list.append(('BACKGROUND', (0, idx), (-1, idx), colors.HexColor("#F0FDF4")))
                style_list.append(('TEXTCOLOR', (0, idx), (-1, idx), colors.HexColor("#166534")))
                style_list.append(('FONTNAME', (0, idx), (-1, idx), 'Helvetica-Bold'))

            # 3. SUBREPORTE MARCA (Crema Pastel - Minimalista)
            elif "Σ MARCA" in row_str:
                style_list.append(('BACKGROUND', (0, idx), (-1, idx), colors.HexColor("#FFF7ED")))
                style_list.append(('TEXTCOLOR', (0, idx), (-1, idx), colors.HexColor("#9A3412")))
                style_list.append(('FONTNAME', (0, idx), (-1, idx), 'Helvetica-Bold'))

        return TableStyle(style_list)

    @staticmethod
    def generate_single_table_pdf(df, title, subtitle=""):
        if df is None or df.empty: return None
        buffer = ExportManager._prepare_pdf_buffer()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), leftMargin=10, rightMargin=10, topMargin=20, bottomMargin=20)
        styles = getSampleStyleSheet()

        elements = [Paragraph(f"<b>{title}</b>", styles['Title'])]
        if subtitle: elements.append(Paragraph(subtitle, styles['Normal']))
        elements.append(Spacer(1, 15))

        df_print = ExportManager._clean_df_for_print(df)
        data = [df_print.columns.tolist()] + df_print.values.tolist()

        n_cols = len(df.columns)
        # Sincronización de anchos para 10 columnas
        col_widths = None
        if n_cols == 10:
            col_widths = [85, 130, 75, 40, 65, 75, 65, 75, 55, 55]
        elif n_cols == 4:
            col_widths = [200, 150, 150, 100]
        else:
            col_widths = None # Auto-size

        t = Table(data, hAlign='CENTER', repeatRows=1, colWidths=col_widths)
        t.setStyle(ExportManager._create_table_style(df_print))
        elements.append(t)

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

    @staticmethod
    def generate_batch_zip_reports(df_master):
        """Genera reportes individuales para cada vendedor en un archivo ZIP."""
        if df_master.empty or 'Vendedor' not in df_master.columns:
            return BytesIO().getvalue()

        # Filtrar vendedores reales (ignorando vacíos o filas de totales)
        vendedores = [v for v in df_master['Vendedor'].unique()
                     if v and str(v).strip() != "" and "TOTAL" not in str(v).upper()]

        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for vend in vendedores:
                # Filtrar datos del vendedor
                df_v = df_master[df_master['Vendedor'] == vend].copy()

                # Para el PDF individual, el nombre del vendedor ya va en el título,
                # así que lo limpiamos en la tabla para mayor minimalismo
                pdf_data = ExportManager.generate_single_table_pdf(df_v, f"REPORTE: {vend}", "Matriz Operativa de Ventas")
                if pdf_data:
                    zf.writestr(f"Reporte_{str(vend).replace(' ', '_')}.pdf", pdf_data)

        zip_buffer.seek(0)
        return zip_buffer.getvalue()

    @staticmethod
    def generate_consolidated_report(tables_dict):
        """Genera un solo PDF con todas las tablas del dashboard."""
        buffer = ExportManager._prepare_pdf_buffer()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), leftMargin=15, rightMargin=15)
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph("<b>INFORME ESTRATÉGICO DE VENTAS 2026</b>", styles['Title']))
        elements.append(Spacer(1, 20))

        for name, df in tables_dict.items():
            if df is None or df.empty: continue
            elements.append(Paragraph(f"<b>{name.upper()}</b>", styles['Heading2']))
            elements.append(Spacer(1, 10))

            df_p = ExportManager._clean_df_for_print(df)
            data = [df_p.columns.tolist()] + df_p.values.tolist()

            n_cols = len(df.columns)
            c_widths = None
            if n_cols == 10: c_widths = [85, 130, 75, 40, 65, 75, 65, 75, 55, 55]
            elif n_cols == 4: c_widths = [200, 150, 150, 100]

            t = Table(data, hAlign='CENTER', repeatRows=1, colWidths=c_widths)
            t.setStyle(ExportManager._create_table_style(df_p))
            elements.append(t)
            elements.append(PageBreak())

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()