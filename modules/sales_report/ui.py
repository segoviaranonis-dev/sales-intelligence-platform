# Ubicación: C:\Users\hecto\Documents\Prg_locales\I_R_G\modules\sales_report\ui.py
import streamlit as st
from datetime import datetime
from core.queries import QueryCenter
from core.styles import apply_styles, header_section, card_style
from .logic import SalesLogic
from .export import ExportManager

def color_variance(val):
    """Aplica colores dinámicos a las variaciones porcentuales."""
    try:
        if not val or val == 'nan': return None
        clean_val = float(str(val).replace('%', '').replace('+', '').replace('.', '').replace(',', '.'))
        color = 'color: #15803D;' if clean_val > 0 else 'color: #B91C1C;' if clean_val < 0 else 'color: #64748B;'
        return color
    except:
        return None

def style_subtotals(row):
    """Resalta visualmente cualquier fila que sea un subtotal (Σ) o un total (==)."""
    row_str = " ".join(row.astype(str)).upper()
    if "Σ" in row_str or "TOTAL" in row_str or "==" in row_str:
        return ['background-color: #F1F5F9; font-weight: bold; border-top: 1.5px solid #CBD5E1; color: #1E293B;'] * len(row)
    return [''] * len(row)

def clean_duplicate_labels(df, columns):
    """Oculta nombres repetidos consecutivos para emular una tabla dinámica."""
    if df.empty: return df
    df_clean = df.copy()
    for col in columns:
        mask = (df_clean[col] == df_clean[col].shift()) & (~df_clean.astype(str).apply(lambda x: x.str.contains("Σ|TOTAL|==", na=False)).any(axis=1))
        df_clean.loc[mask, col] = ""
    return df_clean

def render_sales_report_interface():
    apply_styles()
    header_section("Inteligencia de Mercado", "Visión 360° de Cartera y Desempeño")

    with st.sidebar:
        st.title("🛡️ Filtros de Control")

        st.subheader("🎯 Incremento Objetivo (%)")
        objetivo_pct = st.select_slider(
            "Sobre Año Base (2025):",
            options=list(range(0, 105, 5)),
            value=20,
            help="Define el aumento porcentual que se aplicará a las ventas del 2025."
        )
        st.divider()

        tipo_opciones = QueryCenter.get_filter_options("descp_tipo", "tipo")
        index_calzados = tipo_opciones.index("CALZADOS") if "CALZADOS" in tipo_opciones else 0
        tipo = st.selectbox("Tipo:", options=tipo_opciones, index=index_calzados)

        categoria_humana = st.selectbox("Categoría:", options=list(SalesLogic.CATEGORIA_MAP.keys()), index=2)
        id_categoria = SalesLogic.CATEGORIA_MAP[categoria_humana]

        st.divider()

        st.subheader("📅 Periodo Comparativo")
        periodo_tipo = st.radio("Preselección:", ["1er Semestre", "2do Semestre", "Personalizado"], horizontal=True)

        meses_nombres = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]

        # Lógica de preselección de meses corregida
        if periodo_tipo == "1er Semestre":
            default_meses = meses_nombres[0:6]
        elif periodo_tipo == "2do Semestre":
            default_meses = meses_nombres[6:12]
        else:
            # Si es personalizado, mantenemos lo que el usuario elija o el semestre 1 por defecto
            default_meses = meses_nombres[0:6]

        meses_sel = st.multiselect("Seleccionar Meses:", options=meses_nombres, default=default_meses)

        col_f1, col_f2 = st.columns(2)
        with col_f1: st.info("**Base:** 2025")
        with col_f2: st.success("**Actual:** 2026")

        st.divider()

        # --- FILTROS DE CARTERA ---
        query_marcas_dept = f"""
            SELECT DISTINCT m.descp_marca
            FROM registro_ventas_general v
            INNER JOIN tipo t ON CAST(v.id_tipo AS TEXT) = CAST(t.id_tipo AS TEXT)
            INNER JOIN marca m ON CAST(v.id_marca AS TEXT) = CAST(m.id_marca AS TEXT)
            WHERE UPPER(t.descp_tipo) = '{tipo.upper()}'
            ORDER BY m.descp_marca
        """
        try:
            from core.database import get_dataframe
            marcas_filtradas = get_dataframe(query_marcas_dept)['descp_marca'].tolist()
        except:
            marcas_filtradas = []

        marca_sel = st.multiselect("Filtrar Marcas:", options=marcas_filtradas)
        marca = marca_sel if marca_sel else "Todos"
        cadena = st.multiselect("Cadena de Negocio:", options=QueryCenter.get_filter_options("descp_cadena", "cadena"))
        cadena = cadena if cadena else "Todos"
        cliente = st.multiselect("Nombre del Cliente:", options=QueryCenter.get_filter_options("descp_cliente", "cliente"))
        id_cliente = st.multiselect("Código de Cliente:", options=QueryCenter.get_filter_options("id_cliente", "cliente"))

        cliente = cliente if cliente else "Todos"
        id_cliente = id_cliente if id_cliente else "Todos"

        generar = st.button("🚀 GENERAR ANÁLISIS", type="primary", use_container_width=True)

    filtros_activos = {
        "tipo": tipo, "categoria": id_categoria, "marca": marca,
        "cliente": cliente, "cadena": cadena, "id_cliente": id_cliente,
        "start_date": datetime(2025, 1, 1), "end_date": datetime(2026, 12, 31)
    }

    if 'df_ventas' not in st.session_state:
        st.session_state.df_ventas = QueryCenter.get_main_sales_query(filtros_activos)

    if generar:
        st.session_state.df_ventas = QueryCenter.get_main_sales_query(filtros_activos)

    if 'df_ventas' in st.session_state and not st.session_state.df_ventas.empty:
        df = st.session_state.df_ventas

        # --- CRÍTICO: PASAR objetivo_pct Y meses_sel A LA LÓGICA ---
        # Ahora la lógica sanitizará el dataframe antes de procesar cada tabla
        tabla_mes = SalesLogic.process_comparison_matrix(df, objetivo_pct, meses_sel)
        dict_cartera = SalesLogic.process_customer_opportunity(df, objetivo_pct, meses_sel)
        tabla_mar_gen, tabla_mar_det = SalesLogic.process_brand_drilldown(df, objetivo_pct, meses_sel)
        tabla_ven_gen, tabla_ven_det = SalesLogic.process_seller_drilldown(df, objetivo_pct, meses_sel)

        tab_gen, tab_cli, tab_mar, tab_ven = st.tabs([
            "📊 Resumen General", "👥 Análisis Clientes",
            "🏷️ Desempeño Marcas", "💼 Gestión Vendedores"
        ])

        with tab_gen:
            col_t1, col_t2 = st.columns([3, 1])
            with col_t1: st.subheader("Resumen Ejecutivo (Cronológico)")
            with col_t2:
                full_report = ExportManager.generate_consolidated_report({
                    "Evolución Mensual": tabla_mes,
                    "Clientes: Crecimiento": dict_cartera['crecimiento'],
                    "Clientes: Riesgo": dict_cartera['decrecimiento'],
                    "Clientes: Sin Compra": dict_cartera['sin_compra'],
                    "Marcas: Resumen": tabla_mar_gen,
                    "Vendedores: Resumen": tabla_ven_gen
                })
                st.download_button("📄 Informe Completo (PDF)", data=full_report,
                                  file_name="Reporte_Ventas_360.pdf", mime="application/pdf")

            # KPIs sincronizados con los filtros
            kpis = SalesLogic.get_kpis(df, objetivo_pct, meses_sel)
            m1, m2, m3, m4, m5 = st.columns(5)
            with m1: card_style("Clientes 2025", f"{kpis['clientes_25']}")
            with m2: card_style("Clientes 2026", f"{kpis['clientes_26']}")
            with m3: card_style("Solo 2025", f"{kpis['solo_25']}", is_delta=True, delta_val="Riesgo")
            with m4: card_style("Solo 2026", f"{kpis['solo_26']}", is_delta=True, delta_val="Nuevos")
            with m5: card_style("% Retención", f"{kpis['atendimiento']:.1f}%")

            st.markdown("### 📈 Evolución Mensual Comparativa")
            st.dataframe(tabla_mes.style.map(color_variance, subset=['Var %']).apply(style_subtotals, axis=1),
                         width='stretch', hide_index=True)

        with tab_cli:
            st.subheader("Segmentación Estratégica de Cartera")
            config = [
                ('crecimiento', '✅ CLIENTES CON CRECIMIENTO', 'info'),
                ('decrecimiento', '⚠️ CLIENTES EN RIESGO (CAÍDA)', 'warning'),
                ('sin_compra', '📉 OPORTUNIDADES PERDIDAS (SIN COMPRA)', 'error')
            ]
            for key, label, func in config:
                with st.expander(label, expanded=(key=='crecimiento')):
                    df_seg = dict_cartera[key]
                    c1, c2 = st.columns([3, 1])
                    with c1: getattr(st, func)(f"Registros detectados: {max(0, len(df_seg)-1)}")
                    with c2:
                        pdf = ExportManager.generate_single_table_pdf(df_seg, label)
                        st.download_button(f"📥 PDF {key.title()}", data=pdf, file_name=f"{key}.pdf", key=f"btn_{key}")
                    st.dataframe(df_seg.style.map(color_variance, subset=['Variación']).apply(style_subtotals, axis=1), width='stretch', hide_index=True)

        with tab_mar:
            st.subheader("🏷️ Análisis de Marcas")
            with st.expander("📊 RESUMEN GENERAL POR MARCA", expanded=True):
                st.dataframe(tabla_mar_gen.style.map(color_variance, subset=['Variación']).apply(style_subtotals, axis=1),
                               width='stretch', hide_index=True)

            with st.expander("🔍 DETALLE: MARCA > CLIENTE > VENDEDOR", expanded=False):
                c1, c2 = st.columns([3, 1])
                with c1: st.info(f"Desglose detallado de marcas con sus respectivos clientes.")
                with c2:
                    pdf_mar_det = ExportManager.generate_single_table_pdf(tabla_mar_det, "DETALLE DE MARCAS POR CLIENTE")
                    st.download_button("📥 Descargar Detalle (PDF)", data=pdf_mar_det, file_name="Detalle_Marcas.pdf", key="btn_pdf_mar_det")

                df_mar_det_clean = clean_duplicate_labels(tabla_mar_det, ['Marca'])
                st.dataframe(df_mar_det_clean.style.map(color_variance, subset=['Variación']).apply(style_subtotals, axis=1),
                               width='stretch', hide_index=True)

        with tab_ven:
            st.subheader("💼 Gestión de Vendedores")
            st.markdown("### 📲 Generar Reportes para WhatsApp")
            zip_data = ExportManager.generate_batch_zip_reports(tabla_ven_det)
            st.download_button(
                label="📥 DESCARGAR TODOS LOS PDF (ZIP)",
                data=zip_data,
                file_name=f"Reportes_Vendedores_{datetime.now().strftime('%Y%m%d')}.zip",
                mime="application/zip",
                type="primary",
                use_container_width=True
            )
            st.divider()
            with st.expander("📊 RANKING DE VENDEDORES", expanded=True):
                st.dataframe(tabla_ven_gen.style.map(color_variance, subset=['Variación']).apply(style_subtotals, axis=1),
                               width='stretch', hide_index=True)
            with st.expander("🔍 DETALLE: VENDEDOR > MARCA > CLIENTE", expanded=True):
                df_ven_det_clean = clean_duplicate_labels(tabla_ven_det, ['Vendedor', 'Marca'])
                st.dataframe(df_ven_det_clean.style.map(color_variance, subset=['Variación']).apply(style_subtotals, axis=1),
                               width='stretch', hide_index=True)

    elif 'df_ventas' in st.session_state and st.session_state.df_ventas.empty:
        st.warning("⚠️ No hay datos para los filtros seleccionados.")