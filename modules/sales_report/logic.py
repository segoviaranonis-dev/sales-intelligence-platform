# Ubicación: C:\Users\hecto\Documents\Prg_locales\I_R_G\modules\sales_report\logic.py
import pandas as pd
import numpy as np
import sys

class SalesLogic:
    """Motor de Inteligencia v6.7: Blindaje de Identificadores y Consistencia de Datos 2026."""

    CATEGORIA_MAP = {"Stock": "1", "Pre-Venta": "2", "Programado": "3"}

    MESES_ES = {
        1: "01 - Enero", 2: "02 - Febrero", 3: "03 - Marzo", 4: "04 - Abril",
        5: "05 - Mayo", 6: "06 - Junio", 7: "07 - Julio", 8: "08 - Agosto",
        9: "09 - Septiembre", 10: "10 - Octubre", 11: "11 - Noviembre", 12: "12 - Diciembre"
    }

    MESES_ABREVIADOS = {
        1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
        7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"
    }

    @staticmethod
    def _add_total_data(df, label_col):
        """Calcula filas de total general respetando el formato de puntos y comas."""
        if df is None or df.empty: return df
        df_res = df.copy()

        # Columnas que NO deben sumarse
        exclude = [label_col, 'Variación', 'Var %', 'Mes', 'Vendedor', 'Cliente',
                   'Marca', 'Identificador', 'Cadena', '% Var Cant', '% Var Mont']
        num_cols = [c for c in df.columns if c in df_res.columns and c not in exclude]

        total_row = {col: "" for col in df.columns}
        total_row[label_col] = "== TOTAL GENERAL =="

        sums = []
        for col in num_cols:
            try:
                # Limpieza de formato Gs. (puntos a vacio, coma a punto)
                series_clean = df[col].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                val = pd.to_numeric(series_clean, errors='coerce').fillna(0).sum()
                total_row[col] = f"{int(val):,}".replace(",", ".")
                sums.append(val)
            except:
                total_row[col] = "0"
                sums.append(0)

        # Recálculo de variaciones para el Total General basado en las sumas reales
        if '% Var Cant' in df.columns and len(sums) >= 4:
            def calc_v(n, b): return ((n - b) / b * 100) if b > 0 else 0
            # sums[0]=ObjCant, sums[1]=ObjMont, sums[2]=Cant26, sums[3]=Mont26
            total_row['% Var Cant'] = f"{calc_v(sums[2], sums[0]):+.1f}%"
            total_row['% Var Mont'] = f"{calc_v(sums[3], sums[1]):+.1f}%"
        elif len(sums) >= 2:
            v_obj, v_real = sums[0], sums[1]
            var = ((v_real - v_obj) / v_obj * 100) if v_obj > 0 else 0
            v_name = 'Var %' if 'Var %' in df.columns else 'Variación'
            if v_name in total_row: total_row[v_name] = f"{var:+.1f}%"

        return pd.concat([df_res, pd.DataFrame([total_row])], ignore_index=True)

    @staticmethod
    def _sanitize_dataframe(df, objetivo_pct=0, meses_filtro=None):
        """Limpia datos y construye el Identificador Único para evitar cruce de clientes."""
        if df is None or df.empty: return pd.DataFrame()
        df = df.copy()

        # Asegurar tipos básicos
        df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
        df = df.dropna(subset=['fecha'])
        df['anio'] = df['fecha'].dt.year
        df['mes_idx'] = df['fecha'].dt.month
        df['monto'] = pd.to_numeric(df['monto'], errors='coerce').fillna(0)
        df['cantidad'] = pd.to_numeric(df['cantidad'], errors='coerce').fillna(0)

        factor = float(1 + (objetivo_pct / 100))
        df['monto_25'] = np.where(df['anio'] == 2025, df['monto'], 0.0)
        df['monto_26'] = np.where(df['anio'] == 2026, df['monto'], 0.0)
        df['cant_25'] = np.where(df['anio'] == 2025, df['cantidad'], 0.0)
        df['cant_26'] = np.where(df['anio'] == 2026, df['cantidad'], 0.0)

        df['monto_obj'] = df['monto_25'] * factor
        df['cant_obj'] = df['cant_25'] * factor

        # Filtrado de meses
        df['mes_nombre'] = df['mes_idx'].map(lambda x: SalesLogic.MESES_ES[x].split(" - ")[1])
        if meses_filtro:
            df = df[df['mes_nombre'].isin(meses_filtro)]

        # --- CORRECCIÓN CRÍTICA DE IDENTIFICADOR ---
        # Limpiamos la columna cadena de cualquier residuo de base de datos
        df['cadena'] = df['cadena'].astype(str).replace(['SIN CADENA', 'None', 'nan', 'S/C', 'None ', ' nan'], np.nan)

        # El Identificador ahora es sagrado: Si hay cadena, manda la cadena; si no, el nombre del cliente.
        # Se aplica strip() para evitar que "CLIENTE A" y "CLIENTE A " se consideren distintos
        df['cliente'] = df['cliente'].astype(str).str.strip()
        df['Identificador'] = df['cadena'].fillna(df['cliente']).str.strip()

        return df

    @staticmethod
    def process_seller_drilldown(df, objetivo_pct, meses_filtro):
        df_p = SalesLogic._sanitize_dataframe(df, objetivo_pct, meses_filtro)
        if df_p.empty: return pd.DataFrame(), pd.DataFrame()

        # Ranking
        rank = df_p.groupby('vendedor').agg({'monto_obj': 'sum', 'monto_26': 'sum'}).reset_index()
        rank['Variación'] = np.where(rank['monto_obj'] > 0, (rank['monto_26'] - rank['monto_obj']) / rank['monto_obj'] * 100, 0.0)
        rank.columns = ['Vendedor', f'Objetivo (+{objetivo_pct}%)', 'Venta 2026', 'Variación']

        for col in rank.columns[1:3]:
            rank[col] = rank[col].apply(lambda x: f"{int(x):,}".replace(",", "."))
        rank['Variación'] = rank['Variación'].apply(lambda x: f"{x:+.1f}%")
        rank_final = SalesLogic._add_total_data(rank, 'Vendedor')

        # Matriz 10 Columnas (Vendedor > Identificador > Marca)
        hier = df_p.groupby(['vendedor', 'Identificador', 'marca', 'mes_idx']).agg({
            'cant_obj': 'sum', 'cant_26': 'sum', 'monto_obj': 'sum', 'monto_26': 'sum'
        }).reset_index()

        rows = []
        vendedores_sorted = rank.sort_values(rank.columns[2], ascending=False)['Vendedor'].tolist()

        for v in vendedores_sorted:
            df_v = hier[hier['vendedor'] == v]
            if df_v.empty: continue
            for c in df_v['Identificador'].unique():
                df_c = df_v[df_v['Identificador'] == c]
                for m in df_c['marca'].unique():
                    df_m = df_c[df_c['marca'] == m]
                    for _, r in df_m.iterrows():
                        rows.append(SalesLogic._row10(r, v, c, m, r['mes_idx']))
                    rows.append(SalesLogic._row10(df_m.sum(numeric_only=True), v, c, f"Σ MARCA {m}", 0))
                rows.append(SalesLogic._row10(df_c.sum(numeric_only=True), v, f"Σ CLIENTE {c}", "---", 0))
            rows.append(SalesLogic._row10(df_v.sum(numeric_only=True), f"== TOTAL {v} ==", "---", "---", 0))

        return rank_final, pd.DataFrame(rows)

    @staticmethod
    def _row10(d, v, c, m, midx):
        def vp(n, b): return ((n - b) / b * 100) if b > 0 else 0
        mes_txt = SalesLogic.MESES_ABREVIADOS.get(midx, "---")
        return {
            'Vendedor': v, 'Cadena': c, 'Marca': m, 'Mes': mes_txt,
            'Obj. 25 Cant': f"{int(d.get('cant_obj', 0)):,}".replace(",", "."),
            'Obj. 25 Mont': f"{int(d.get('monto_obj', 0)):,}".replace(",", "."),
            'Cant 26': f"{int(d.get('cant_26', 0)):,}".replace(",", "."),
            'Mont 26': f"{int(d.get('monto_26', 0)):,}".replace(",", "."),
            '% Var Cant': f"{vp(d.get('cant_26', 0), d.get('cant_obj', 0)):+.1f}%",
            '% Var Mont': f"{vp(d.get('monto_26', 0), d.get('monto_obj', 0)):+.1f}%"
        }

    @staticmethod
    def process_comparison_matrix(df, objetivo_pct, meses_filtro):
        df_p = SalesLogic._sanitize_dataframe(df, objetivo_pct, meses_filtro)
        if df_p.empty: return pd.DataFrame()
        res = df_p.groupby(['mes_idx']).agg({'monto_obj': 'sum', 'monto_26': 'sum'}).reset_index()
        res['Mes'] = res['mes_idx'].map(SalesLogic.MESES_ES)
        res['Var %'] = np.where(res['monto_obj'] > 0, ((res['monto_26'] - res['monto_obj']) / res['monto_obj'] * 100), 0.0)

        col_obj = f"Objetivo (+{objetivo_pct}%)"
        res = res.rename(columns={'monto_obj': col_obj, 'monto_26': 'Monto 2026 (Gs.)'})
        for col in [col_obj, 'Monto 2026 (Gs.)']:
            res[col] = res[col].apply(lambda x: f"{int(x):,}".replace(",", "."))
        res['Var %'] = res['Var %'].apply(lambda x: f"{x:+.1f}%")
        return SalesLogic._add_total_data(res[['Mes', col_obj, 'Monto 2026 (Gs.)', 'Var %']], 'Mes')

    @staticmethod
    def process_brand_drilldown(df, objetivo_pct, meses_filtro):
        df_p = SalesLogic._sanitize_dataframe(df, objetivo_pct, meses_filtro)
        if df_p.empty: return pd.DataFrame(), pd.DataFrame()

        rank = df_p.groupby('marca').agg({'monto_obj': 'sum', 'monto_26': 'sum'}).reset_index()
        det = df_p.groupby(['marca', 'Identificador', 'vendedor']).agg({'monto_obj': 'sum', 'monto_26': 'sum'}).reset_index()

        def _fmt(df_in, head, label_col):
            df_in = df_in.sort_values('monto_26', ascending=False)
            df_in['Var'] = np.where(df_in['monto_obj'] > 0, (df_in['monto_26']-df_in['monto_obj'])/df_in['monto_obj']*100, 0)
            df_in.columns = head + [f"Objetivo (+{objetivo_pct}%)", "Venta 2026", "Variación"]
            for col in df_in.columns[-3:-1]:
                df_in[col] = df_in[col].apply(lambda x: f"{int(x):,}".replace(",", "."))
            df_in["Variación"] = df_in["Variación"].apply(lambda x: f"{x:+.1f}%")
            return SalesLogic._add_total_data(df_in, label_col)

        return _fmt(rank, ['Marca'], 'Marca'), _fmt(det, ['Marca', 'Cliente', 'Vendedor'], 'Marca')

    @staticmethod
    def process_customer_opportunity(df, objetivo_pct, meses_filtro):
        df_p = SalesLogic._sanitize_dataframe(df, objetivo_pct, meses_filtro)
        if df_p.empty: return {k: pd.DataFrame() for k in ['crecimiento', 'decrecimiento', 'sin_compra']}

        piv = df_p.groupby('Identificador').agg({'monto_obj': 'sum', 'monto_26': 'sum'}).reset_index()

        def _f(s):
            if s.empty: return pd.DataFrame(columns=['Identificador', f"Objetivo (+{objetivo_pct}%)", "Venta 2026", "Variación"])
            s = s.sort_values('monto_26', ascending=False)
            s['Var'] = np.where(s['monto_obj'] > 0, (s['monto_26']-s['monto_obj'])/s['monto_obj']*100, 0)
            s.columns = ['Identificador', f"Objetivo (+{objetivo_pct}%)", "Venta 2026", "Variación"]
            for c in s.columns[1:3]: s[c] = s[c].apply(lambda x: f"{int(x):,}".replace(",", "."))
            s['Variación'] = s['Variación'].apply(lambda x: f"{x:+.1f}%")
            return SalesLogic._add_total_data(s, 'Identificador')

        return {
            "crecimiento": _f(piv[piv['monto_26'] > piv['monto_obj']]),
            "decrecimiento": _f(piv[(piv['monto_26'] <= piv['monto_obj']) & (piv['monto_26'] > 0)]),
            "sin_compra": _f(piv[(piv['monto_26'] == 0) & (piv['monto_obj'] > 0)])
        }

    @staticmethod
    def get_kpis(df, objetivo_pct, meses_filtro):
        df_proc = SalesLogic._sanitize_dataframe(df, objetivo_pct, meses_filtro)
        if df_proc.empty: return {'clientes_26': 0, 'atendimiento': 0}
        c26 = df_proc[df_proc['monto_26'] > 0]['codigo_cliente'].nunique()
        total = df_proc['codigo_cliente'].nunique()
        return {'clientes_26': c26, 'atendimiento': (c26 / total * 100) if total > 0 else 0}