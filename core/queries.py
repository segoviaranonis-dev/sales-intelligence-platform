# Ubicación: C:\Users\hecto\Documents\Prg_locales\I_R_G\core\queries.py
import streamlit as st
from .database import get_dataframe
import pandas as pd

class QueryCenter:
    """Motor de Inteligencia Comercial v7.2 - Precisión Quirúrgica PostgreSQL 2026."""

    @staticmethod
    def get_main_sales_query(filters):
        """
        Consulta Maestra: Filtra por IDs y descripciones con casting riguroso para evitar inconsistencias.
        """
        conditions = []
        params = {}

        # 1. Filtros Padre (Casting forzado a TEXT)
        if filters.get('tipo'):
            conditions.append("CAST(v.id_tipo AS TEXT) = :tipo_id")
            val_tipo = "1" if filters['tipo'] == "CALZADOS" else filters['tipo']
            params['tipo_id'] = str(val_tipo)

        if filters.get('categoria'):
            conditions.append("CAST(v.id_categoria AS TEXT) = :cat_id")
            val_cat = "2" if filters['categoria'] == "Programado" else filters['categoria']
            params['cat_id'] = str(val_cat)

        # 2. Filtros de Granularidad con Mapeo de Columnas Correcto
        # Se corrigió el mapeo de codigo_cliente para usar CAST y evitar el error original
        mapping = {
            'marca': 'm.descp_marca',
            'vendedor': 'ven.descp_vendedor',
            'cliente': 'c.descp_cliente',
            'codigo_cliente': 'CAST(v.id_cliente AS TEXT)'
        }

        for key, db_col in mapping.items():
            val = filters.get(key)
            if val and val != "Todos" and val != []:
                if isinstance(val, list):
                    placeholders = [f":{key}_{i}" for i in range(len(val))]
                    conditions.append(f"{db_col} IN ({', '.join(placeholders)})")
                    for i, v in enumerate(val): params[f"{key}_{i}"] = str(v)
                else:
                    conditions.append(f"{db_col} = :{key}")
                    params[key] = str(val)

        # 3. Filtro de Cadena (Join con tabla cadena)
        cadena_val = filters.get('cadena')
        if cadena_val and cadena_val != "Todos" and cadena_val != []:
            if isinstance(cadena_val, list):
                placeholders = [f":cad_{i}" for i in range(len(cadena_val))]
                conditions.append(f"cad.descp_cadena IN ({', '.join(placeholders)})")
                for i, v in enumerate(cadena_val): params[f"cad_{i}"] = str(v)
            else:
                conditions.append("cad.descp_cadena = :cadena")
                params['cadena'] = str(cadena_val)

        # 4. Filtro de Fecha (Periodo 2025-2026)
        if filters.get('start_date') and filters.get('end_date'):
            conditions.append("(v.fecha >= :sd AND v.fecha <= :ed)")
            params['sd'] = filters['start_date']
            params['ed'] = filters['end_date']

        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

        query = f"""
            SELECT
                v.fecha,
                COALESCE(v.monto, 0) as monto,
                COALESCE(v.cantidad, 0) as cantidad,
                t.descp_tipo as tipo,
                m.descp_marca as marca,
                c.descp_cliente as cliente,
                ven.descp_vendedor as vendedor,
                cad.descp_cadena as cadena,
                CAST(v.id_cliente AS TEXT) as codigo_cliente
            FROM registro_ventas_general v
            INNER JOIN tipo t ON CAST(v.id_tipo AS TEXT) = CAST(t.id_tipo AS TEXT)
            INNER JOIN marca m ON CAST(v.id_marca AS TEXT) = CAST(m.id_marca AS TEXT)
            INNER JOIN cliente c ON CAST(v.id_cliente AS TEXT) = CAST(c.id_cliente AS TEXT)
            INNER JOIN vendedor ven ON CAST(v.id_vendedor AS TEXT) = CAST(ven.id_vendedor AS TEXT)
            LEFT JOIN cliente_cadena cc ON CAST(v.id_cliente AS TEXT) = CAST(cc.id_cliente AS TEXT)
            LEFT JOIN cadena cad ON CAST(cc.id_cadena AS TEXT) = CAST(cad.id_cadena AS TEXT)
            {where_clause}
            ORDER BY v.fecha ASC
        """

        try:
            df = get_dataframe(query, params)
            if df is not None and not df.empty:
                df['monto'] = pd.to_numeric(df['monto'], errors='coerce').fillna(0)
                df['cantidad'] = pd.to_numeric(df['cantidad'], errors='coerce').fillna(0)
                df['fecha'] = pd.to_datetime(df['fecha'])
                return df
            return pd.DataFrame(columns=['fecha', 'monto', 'cantidad', 'tipo', 'marca', 'cliente', 'vendedor', 'cadena', 'codigo_cliente'])
        except Exception as e:
            st.error(f"⚠️ Error en Tubería de Datos (SQL): {e}")
            return pd.DataFrame(columns=['fecha', 'monto', 'cantidad', 'tipo', 'marca', 'cliente', 'vendedor', 'cadena', 'codigo_cliente'])

    @staticmethod
    def get_dynamic_filters(universe_df):
        """Genera listas únicas para los selectores de la UI."""
        if universe_df is None or universe_df.empty:
            return {'marcas': [], 'vendedores': [], 'clientes': [], 'cadenas': [], 'codigos': []}

        return {
            'marcas': sorted([str(x) for x in universe_df['marca'].unique() if x and str(x).strip()]),
            'vendedores': sorted([str(x) for x in universe_df['vendedor'].unique() if x and str(x).strip()]),
            'clientes': sorted([str(x) for x in universe_df['cliente'].unique() if x and str(x).strip()]),
            'cadenas': sorted([str(x) for x in universe_df['cadena'].unique() if x and str(x).strip()]),
            'codigos': sorted([str(x) for x in universe_df['codigo_cliente'].unique() if x and str(x).strip()])
        }