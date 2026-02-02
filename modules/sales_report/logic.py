# Ubicación: C:\Users\hecto\Documents\Prg_locales\I_R_G\modules\sales_report\logic.py
import pandas as pd
import numpy as np

class SalesLogic:
    """Motor de Inteligencia de Cartera y Performance - Análisis Jerárquico Drill-Down."""

    CATEGORIA_MAP = {"Stock": 1, "Pre-Venta": 2, "Programado": 3}

    MESES_ES = {
        1: "01 - Enero", 2: "02 - Febrero", 3: "03 - Marzo", 4: "04 - Abril",
        5: "05 - Mayo", 6: "06 - Junio", 7: "07 - Julio", 8: "08 - Agosto",
        9: "09 - Septiembre", 10: "10 - Octubre", 11: "11 - Noviembre", 12: "12 - Diciembre"
    }

    @staticmethod
    def _sanitize_dataframe(df, objetivo_pct=0, meses_filtro=None):
        """Limpia datos, aplica incremento objetivo al 2025 y filtra estrictamente por meses."""
        if df is None or df.empty: return pd.DataFrame()

        # Trabajamos con copia y forzamos float64 para evitar desbordamientos de enteros
        df = df.copy()
        df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
        df['monto'] = pd.to_numeric(df['monto'], errors='coerce').fillna(0).astype(float)
        df['anio'] = df['fecha'].dt.year

        # Mapeo de nombre de mes para el filtro
        df['mes_nombre'] = df['fecha'].dt.month.map(lambda x: SalesLogic.MESES_ES[x].split(" - ")[1] if pd.notnull(x) else None)

        # 1. FILTRO DE MESES DESTRUCTIVO (Si no está en la lista, el dato se borra aquí mismo)
        if meses_filtro and len(meses_filtro) > 0:
            df = df[df['mes_nombre'].isin(meses_filtro)]

        # 2. Aplicación del Monto Objetivo al Año Base (2025)
        # Usamos float para evitar el error de números negativos extraños
        factor = float(1 + (objetivo_pct / 100))
        mask_25 = df['anio'] == 2025
        df.loc[mask_25, 'monto'] = df.loc[mask_25, 'monto'] * factor

        # Identificador robusto
        df['Identificador'] = df['cadena'].astype(str).replace(['SIN CADENA', 'None', 'nan', 'NaN', ''], np.nan).fillna(df['cliente'])
        return df

    @staticmethod
    def _add_total_row(df_pivot, index_name="TOTAL GENERAL", sort_by_performance=True):
        """Calcula variaciones y añade la fila de totales al final del DataFrame."""
        if df_pivot.empty: return df_pivot

        for anio in [2025, 2026]:
            if anio not in df_pivot.columns: df_pivot[anio] = 0.0

        # Protección contra división por cero y valores infinitos
        with np.errstate(divide='ignore', invalid='ignore'):
            df_pivot['Variación %'] = ((df_pivot[2026] - df_pivot[2025]) / df_pivot[2025] * 100)
            df_pivot['Variación %'] = df_pivot['Variación %'].replace([np.inf, -np.inf], 0).fillna(0)

        if sort_by_performance:
            df_body = df_pivot.sort_values(by='Variación %', ascending=False)
        else:
            df_body = df_pivot.sort_index()

        totales = pd.DataFrame({
            2025: [df_pivot[2025].sum()],
            2026: [df_pivot[2026].sum()]
        }, index=[f"== {index_name} =="])

        with np.errstate(divide='ignore', invalid='ignore'):
            totales['Variación %'] = ((totales[2026] - totales[2025]) / totales[2025] * 100)
            totales['Variación %'] = totales['Variación %'].replace([np.inf, -np.inf], 0).fillna(0)

        return pd.concat([df_body, totales])

    @staticmethod
    def _apply_formatting(df, cols_to_format, objetivo_pct=0):
        """Transforma números en strings con formato moneda (puntos) y signo de variación."""
        if df.empty: return df
        res = df.copy()
        for col in [2025, 2026]:
            if col in res.columns:
                # CAMBIO: Etiqueta dinámica con el porcentaje del slider
                label = f"Venta {col}" if col == 2026 else f"Objetivo 2025 (+{objetivo_pct}%)"
                # Formateo seguro para Guaraníes (sin decimales)
                res[label] = res[col].apply(lambda x: f"{max(0, x):,.0f}".replace(",", "."))

        if 'Variación %' in res.columns:
            res['Variación'] = res['Variación %'].apply(lambda x: f"{x:+.1f}%")

        return res

    @staticmethod
    def get_kpis(df, objetivo_pct=0, meses_filtro=None):
        """Calcula KPIs considerando el filtro de meses."""
        df = SalesLogic._sanitize_dataframe(df, objetivo_pct, meses_filtro)
        if df.empty: return {"clientes_25": 0, "clientes_26": 0, "solo_25": 0, "solo_26": 0, "atendimiento": 0}

        ids_25 = set(df[df['anio'] == 2025]['Identificador'].unique())
        ids_26 = set(df[df['anio'] == 2026]['Identificador'].unique())

        recurrentes = len(ids_25 & ids_26)
        return {
            "clientes_25": len(ids_25),
            "clientes_26": len(ids_26),
            "solo_25": len(ids_25 - ids_26),
            "solo_26": len(ids_26 - ids_25),
            "atendimiento": (recurrentes / len(ids_25) * 100) if ids_25 else 0
        }

    @staticmethod
    def process_comparison_matrix(df, objetivo_pct=0, meses_filtro=None):
        """Genera la matriz mensual comparativa filtrada."""
        df = SalesLogic._sanitize_dataframe(df, objetivo_pct, meses_filtro)
        if df.empty: return pd.DataFrame()

        df['Mes'] = df['fecha'].dt.month.map(SalesLogic.MESES_ES)

        # Pivotamos. Al estar sanitizado el DF, solo aparecerán los meses seleccionados.
        matrix = df.pivot_table(index='Mes', columns='anio', values='monto', aggfunc='sum').fillna(0)

        res = SalesLogic._add_total_row(matrix, sort_by_performance=False)
        res = res.reset_index().rename(columns={'index': 'Mes'})

        # CAMBIO: Nombres de columnas dinámicos con el porcentaje
        col_obj = f"Objetivo 2025 (+{objetivo_pct}%)"
        col_real = f"Monto 2026 (Gs.)"

        res[col_obj] = res[2025].apply(lambda x: f"{max(0, x):,.0f}".replace(",", "."))
        res[col_real] = res[2026].apply(lambda x: f"{max(0, x):,.0f}".replace(",", "."))

        res['Var %'] = res['Variación %'].apply(lambda x: f"{x:+.1f}%")
        return res[['Mes', col_obj, col_real, 'Var %']]

    @staticmethod
    def process_customer_opportunity(df, objetivo_pct=0, meses_filtro=None):
        """Segmenta la cartera filtrada."""
        df = SalesLogic._sanitize_dataframe(df, objetivo_pct, meses_filtro)
        if df.empty: return {"crecimiento": pd.DataFrame(), "decrecimiento": pd.DataFrame(), "sin_compra": pd.DataFrame()}

        pivot = df.pivot_table(index='Identificador', columns='anio', values='monto', aggfunc='sum').fillna(0)
        for anio in [2025, 2026]:
            if anio not in pivot.columns: pivot[anio] = 0.0

        with np.errstate(divide='ignore', invalid='ignore'):
            pivot['Variación %'] = ((pivot[2026] - pivot[2025]) / pivot[2025] * 100).replace([np.inf, -np.inf], 0).fillna(0)

        def _final_format(df_seg, label):
            if df_seg.empty: return pd.DataFrame()
            res = SalesLogic._add_total_row(df_seg[[2025, 2026]], label)
            res = res.reset_index().rename(columns={'index': 'Identificador'})
            formatted = SalesLogic._apply_formatting(res, [2025, 2026], objetivo_pct)
            # Retornar con el nombre de columna dinámico
            col_target = f"Objetivo 2025 (+{objetivo_pct}%)"
            return formatted[['Identificador', col_target, 'Venta 2026', 'Variación']]

        return {
            "crecimiento": _final_format(pivot[pivot['Variación %'] > 0], "TOTAL CRECIMIENTO"),
            "decrecimiento": _final_format(pivot[(pivot['Variación %'] <= 0) & (pivot[2026] > 0)], "TOTAL DECRECIMIENTO"),
            "sin_compra": _final_format(pivot[(pivot[2026] == 0) & (pivot[2025] > 0)], "TOTAL SIN COMPRA")
        }

    @staticmethod
    def process_brand_drilldown(df, objetivo_pct=0, meses_filtro=None):
        """Pestaña Marcas filtrada."""
        df = SalesLogic._sanitize_dataframe(df, objetivo_pct, meses_filtro)
        if df.empty: return pd.DataFrame(), pd.DataFrame()

        pivot_gen = df.pivot_table(index='marca', columns='anio', values='monto', aggfunc='sum').fillna(0)
        res_gen = SalesLogic._add_total_row(pivot_gen, "TOTAL MARCAS")
        tabla_gen = SalesLogic._apply_formatting(res_gen.reset_index().rename(columns={'index': 'Marca'}), [2025, 2026], objetivo_pct)

        hier = df.groupby(['marca', 'Identificador', 'vendedor', 'anio'])['monto'].sum().unstack('anio').fillna(0)
        for anio in [2025, 2026]:
            if anio not in hier.columns: hier[anio] = 0.0

        hier['Variación %'] = ((hier[2026] - hier[2025]) / hier[2025] * 100).replace([np.inf, -np.inf], 0).fillna(0)
        marcas_order = pivot_gen.sort_values(by=2026, ascending=False).index

        final_rows = []
        for marca in marcas_order:
            df_marca = hier.loc[marca].sort_values('Variación %', ascending=False)
            for idx, row in df_marca.iterrows():
                final_rows.append({
                    'Marca': marca, 'Cliente': idx[0], 'Vendedor': idx[1],
                    2025: row[2025], 2026: row[2026], 'Variación %': row['Variación %']
                })
            final_rows.append({
                'Marca': f"Σ SUBTOTAL {marca}", 'Cliente': '---', 'Vendedor': '---',
                2025: df_marca[2025].sum(), 2026: df_marca[2026].sum(),
                'Variación %': ((df_marca[2026].sum() - df_marca[2025].sum()) / df_marca[2025].sum() * 100) if df_marca[2025].sum() > 0 else 0
            })

        tabla_det = SalesLogic._apply_formatting(pd.DataFrame(final_rows), [2025, 2026], objetivo_pct)
        col_target = f"Objetivo 2025 (+{objetivo_pct}%)"
        return tabla_gen[['Marca', col_target, 'Venta 2026', 'Variación']], \
                tabla_det[['Marca', 'Cliente', 'Vendedor', col_target, 'Venta 2026', 'Variación']]

    @staticmethod
    def process_seller_drilldown(df, objetivo_pct=0, meses_filtro=None):
        """Pestaña Vendedores filtrada."""
        df = SalesLogic._sanitize_dataframe(df, objetivo_pct, meses_filtro)
        if df.empty: return pd.DataFrame(), pd.DataFrame()

        pivot_gen = df.pivot_table(index='vendedor', columns='anio', values='monto', aggfunc='sum').fillna(0)
        res_gen = SalesLogic._add_total_row(pivot_gen, "TOTAL VENDEDORES")
        tabla_gen = SalesLogic._apply_formatting(res_gen.reset_index().rename(columns={'index': 'Vendedor'}), [2025, 2026], objetivo_pct)

        hier = df.groupby(['vendedor', 'marca', 'Identificador', 'anio'])['monto'].sum().unstack('anio').fillna(0)
        for anio in [2025, 2026]:
            if anio not in hier.columns: hier[anio] = 0.0

        hier['Variación %'] = ((hier[2026] - hier[2025]) / hier[2025] * 100).replace([np.inf, -np.inf], 0).fillna(0)
        vendedores_order = pivot_gen.sort_values(by=2026, ascending=False).index

        final_rows = []
        for vend in vendedores_order:
            df_vend = hier.loc[vend]
            marcas_in_vend = df_vend.groupby('marca')[[2025, 2026]].sum()
            marcas_order = marcas_in_vend.sort_values(by=2026, ascending=False).index

            for marca in marcas_order:
                df_cli = df_vend.loc[marca].sort_values('Variación %', ascending=False)
                for idx, row in df_cli.iterrows():
                    final_rows.append({
                        'Vendedor': vend, 'Marca': marca, 'Cliente': idx,
                        2025: row[2025], 2026: row[2026], 'Variación %': row['Variación %']
                    })
                final_rows.append({
                    'Vendedor': vend, 'Marca': f"Σ {marca}", 'Cliente': '---',
                    2025: df_cli[2025].sum(), 2026: df_cli[2026].sum(),
                    'Variación %': ((df_cli[2026].sum() - df_cli[2025].sum()) / df_cli[2025].sum() * 100) if df_cli[2025].sum() > 0 else 0
                })

            final_rows.append({
                'Vendedor': f"Σ TOTAL {vend}", 'Marca': '---', 'Cliente': '---',
                2025: df_vend[2025].sum(), 2026: df_vend[2026].sum(),
                'Variación %': ((df_vend[2026].sum() - df_vend[2025].sum()) / df_vend[2025].sum() * 100) if df_vend[2025].sum() > 0 else 0
            })

        tabla_det = SalesLogic._apply_formatting(pd.DataFrame(final_rows), [2025, 2026], objetivo_pct)
        col_target = f"Objetivo 2025 (+{objetivo_pct}%)"
        return tabla_gen[['Vendedor', col_target, 'Venta 2026', 'Variación']], \
                tabla_det[['Vendedor', 'Marca', 'Cliente', col_target, 'Venta 2026', 'Variación']]
# forced update: 02/02/2026 08:59:11
