# Ubicación: C:\Users\hecto\Documents\Prg_locales\I_R_G\modules\sales_report\ui.py
import streamlit as st
from datetime import datetime
import pandas as pd
from core.queries import QueryCenter
from core.styles import apply_styles, header_section, card_style
from .logic import SalesLogic
from .export import ExportManager
import sys

def color_variance(val):
    """Aplica colores dinámicos a las variaciones porcentuales."""
    try:
        if val is None or str(val) in ['nan', 'None', '']: return None
        clean_val = float(str(val).replace('%', '').replace('+', '').replace('.', '').replace(',', '.'))
        if clean_val > 0.1: return 'color: #15803D; font-weight: bold;'
        if clean_val < -0.1: return 'color: #B91C1C; font-weight: bold;'
        return 'color: #64748B;'
    except: return None

def style_subtotals(row):
    """Resalta visualmente subtotales por Marca, Cliente y Totales Generales."""
    row_str = " ".join(row.astype(str)).upper()
    if "TOTAL" in row_str or "==" in row_str:
        return ['background-color: #F0F9FF; font-weight: bold; border-top: 1.5px solid #BAE6FD; color: #0369A1;'] * len(row)
    if "Σ CLIENTE" in row_str:
        return ['background-color: #F0FDF4; font-weight: bold; color: #166534;'] * len(row)
    if "Σ MARCA" in row_str:
        return ['background-color: #FFF7ED; font-weight: bold; color: #9A3412; font-style: italic;'] * len(row)
    return [''] * len(row)

def safe_style_dataframe(df, subset_cols):
    """Aplica estilos de forma segura verificando existencia de columnas."""
    if df is None or df.empty: return df
    existing_cols = [c for c in subset_cols if c in df.columns]
    styled_df = df.style
    if existing_cols:
        styled_df = styled_df.map(color_variance, subset=existing_cols)
    return styled_df.apply(style_subtotals, axis=1)

def clean_duplicate_labels(df, columns):
    """Oculta nombres repetidos para un diseño minimalista."""
    if df is None or df.empty: return df
    df_clean = df.copy()
    for col in columns:
        if col in df_clean.columns:
            is_summary = df_clean.astype(str).apply(lambda x: x.str.contains("Σ|TOTAL|==", na=False)).any(axis=1)
            mask = (df_clean[col] == df_clean[col].shift()) & (~is_summary)
            df_clean.loc[mask, col] = ""
    return df_clean

def render_sales_report_interface():
    apply_styles()
    header_section("Inteligencia de Mercado", "Visión 360° de Cartera y Desempeño")

    with st.sidebar:
        st.title("🛡️ Centro de Control")
        st.subheader("🎯 Objetivo")
        objetivo_pct = st.select_slider("Incremento sobre 2025 (%):", options=list(range(0, 105, 5)), value=20)

        tipo_opciones = ["CALZADOS", "VARIOS"]
        tipo = st.selectbox("Departamento:", options=tipo_opciones, index=0)

        cat_map = SalesLogic.CATEGORIA_MAP
        categoria_sel = st.selectbox("Categoría de Venta:", options=list(cat_map.keys()), index=2)

        st.divider()
        periodo_tipo = st.radio("Sugerencia de Periodo:", ["1er Semestre", "2do Semestre", "Personalizado"], horizontal=True)
        meses_nombres = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

        if periodo_tipo == "1er Semestre": default_meses = meses_nombres[0:6]
        elif periodo_tipo == "2do Semestre": default_meses = meses_nombres[6:12]
        else: default_meses = st.session_state.get('last_months', meses_nombres[0:6])

        meses_sel = st.multiselect("Meses a Evaluar:", options=meses_nombres, default=default_meses)
        st.session_state.last_months = meses_sel

        filtros_base = {"tipo": tipo, "categoria": cat_map[categoria_sel], "start_date": datetime(2025, 1, 1), "end_date": datetime(2026, 12, 31)}
        df_universo = QueryCenter.get_main_sales_query(filtros_base)
        opciones = QueryCenter.get_dynamic_filters(df_universo)

        with st.expander("🔍 Filtros de Granularidad"):
            cadena = st.multiselect("Cadenas:", options=opciones['cadenas'])
            vendedor = st.multiselect("Vendedores:", options=opciones['vendedores'])
            marca = st.multiselect("Marcas:", options=opciones['marcas'])
            cliente = st.multiselect("Clientes:", options=opciones['clientes'])
            # RESTAURADO: Filtro por código de cliente
            codigo_cliente = st.multiselect("Código Cliente (ID):", options=opciones['codigos'])

        generar = st.button("🚀 GENERAR ANÁLISIS ÍNTEGRO", type="primary", use_container_width=True)

    filtros_finales = {
        "tipo": tipo, "categoria": cat_map[categoria_sel],
        "cadena": cadena if cadena else "Todos",
        "vendedor": vendedor if vendedor else "Todos",
        "marca": marca if marca else "Todos",
        "cliente": cliente if cliente else "Todos",
        "codigo_cliente": codigo_cliente if codigo_cliente else "Todos",
        "start_date": datetime(2025, 1, 1), "end_date": datetime(2026, 12, 31)
    }

    if generar or 'df_ventas' not in st.session_state:
        st.session_state.df_ventas = QueryCenter.get_main_sales_query(filtros_finales)

    df_raw = st.session_state.df_ventas

    if df_raw is not None and not df_raw.empty:
        t_evolucion = SalesLogic.process_comparison_matrix(df_raw, objetivo_pct, meses_sel)
        d_cartera = SalesLogic.process_customer_opportunity(df_raw, objetivo_pct, meses_sel)
        t_mar_gen, t_mar_det = SalesLogic.process_brand_drilldown(df_raw, objetivo_pct, meses_sel)
        t_ven_gen, t_ven_det = SalesLogic.process_seller_drilldown(df_raw, objetivo_pct, meses_sel)
        kpis = SalesLogic.get_kpis(df_raw, objetivo_pct, meses_sel)

        tab_gen, tab_cli, tab_mar, tab_ven = st.tabs(["📊 Dashboard", "👥 Clientes", "🏷️ Marcas", "💼 Vendedores"])

        with tab_gen:
            m1, m2, m3 = st.columns(3)
            with m1: card_style("Alcance Clientes 2026", f"{kpis['clientes_26']}")
            with m2: card_style("% Atendimiento", f"{kpis['atendimiento']:.1f}%")
            with m3:
                pdf_full = ExportManager.generate_consolidated_report({"Evolución": t_evolucion, "Ranking": t_ven_gen, "Marcas": t_mar_gen})
                st.download_button("📄 PDF Informe Completo", data=pdf_full, file_name="Informe_General.pdf", use_container_width=True)
            st.subheader("📈 Evolución Mensual")
            st.dataframe(safe_style_dataframe(t_evolucion, ['Var %']), use_container_width=True, hide_index=True)

        with tab_cli:
            for key, label in [('crecimiento', '✅ Crecimiento'), ('decrecimiento', '⚠️ Riesgo'), ('sin_compra', '📉 Sin Compra')]:
                c1, c2 = st.columns([0.8, 0.2])
                with c1: st.subheader(label)
                with c2: # RESTAURADO: Botón PDF individual para Clientes
                    pdf_cli = ExportManager.generate_consolidated_report({label: d_cartera[key]})
                    st.download_button(f"📥 PDF {key.capitalize()}", data=pdf_cli, file_name=f"Reporte_Clientes_{key}.pdf", key=f"btn_cli_{key}")
                st.dataframe(safe_style_dataframe(d_cartera[key], ['Variación']), use_container_width=True, hide_index=True)

        with tab_mar:
            m_c1, m_c2 = st.columns([0.8, 0.2])
            with m_c1: st.subheader("Resumen por Marca")
            with m_c2: # RESTAURADO: Botón PDF individual para Marcas
                pdf_mar = ExportManager.generate_consolidated_report({"Resumen Marcas": t_mar_gen})
                st.download_button("📥 PDF Marcas", data=pdf_mar, file_name="Reporte_Marcas.pdf")
            st.dataframe(safe_style_dataframe(t_mar_gen, ['Variación']), use_container_width=True, hide_index=True)
            with st.expander("🔍 Detalle Marca > Cliente"):
                st.dataframe(safe_style_dataframe(clean_duplicate_labels(t_mar_det, ['Marca']), ['Variación']), use_container_width=True, hide_index=True)

        with tab_ven:
            v_c1, v_c2 = st.columns([0.8, 0.2])
            with v_c1: st.subheader("Ranking Vendedores")
            with v_c2: # RESTAURADO: Botón PDF individual para Vendedores
                pdf_ven = ExportManager.generate_consolidated_report({"Ranking Vendedores": t_ven_gen})
                st.download_button("📥 PDF Ranking", data=pdf_ven, file_name="Ranking_Vendedores.pdf")
            st.dataframe(safe_style_dataframe(t_ven_gen, ['Variación']), use_container_width=True, hide_index=True)
            st.markdown("### 📊 Matriz Operativa (Vendedor > Cadena > Marca)")
            st.dataframe(safe_style_dataframe(clean_duplicate_labels(t_ven_det, ['Vendedor', 'Cadena', 'Marca']), ['% Var Cant', '% Var Mont']), use_container_width=True, hide_index=True)
            st.download_button("📦 GENERAR ZIP VENDEDORES", data=ExportManager.generate_batch_zip_reports(t_ven_det), file_name="Reportes.zip", use_container_width=True)
    else:
        st.warning("⚠️ No se encontraron datos para la combinación de filtros seleccionada.")