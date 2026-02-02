# Ubicación: C:\Users\hecto\Documents\Prg_locales\I_R_G\core\queries.py
import streamlit as st
from .database import get_dataframe

class QueryCenter:
    """Motor de Inteligencia Comercial - Blindado contra inconsistencias de tipo TEXT."""

    @staticmethod
    @st.cache_data(ttl=600, show_spinner=False)
    def check_column_exists(table, column):
        query = f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = '{table}' AND column_name = '{column}'
            );
        """
        try:
            df = get_dataframe(query)
            return df.iloc[0, 0] if not df.empty else False
        except:
            return False

    @staticmethod
    @st.cache_data(ttl=600, show_spinner=False)
    def get_filter_options(target_column, table):
        if not QueryCenter.check_column_exists(table, target_column):
            return []

        query = f"SELECT DISTINCT {target_column} FROM {table} WHERE {target_column} IS NOT NULL ORDER BY {target_column}"
        try:
            df = get_dataframe(query)
            return df[target_column].astype(str).tolist() if not df.empty else []
        except:
            return []

    @staticmethod
    def get_main_sales_query(filters):
        """Consulta optimizada con CAST y soporte para Vendedores y Cadenas."""
        conditions = []
        params = {}

        # Mapeo con sanitización de tipos
        mapping = {
            'tipo': 'UPPER(t.descp_tipo)',
            'marca': 'm.descp_marca',
            'cliente': 'c.descp_cliente',
            'cadena': 'cad.descp_cadena',
            'categoria': 'CAST(v.id_categoria AS INTEGER)'
        }

        for key, db_col in mapping.items():
            val = filters.get(key)
            if val and val != "Todos":
                if isinstance(val, list) and len(val) > 0:
                    placeholders = [f":{key}_{i}" for i in range(len(val))]
                    conditions.append(f"{db_col} IN ({', '.join(placeholders)})")
                    for i, v in enumerate(val): params[f"{key}_{i}"] = str(v)
                elif not isinstance(val, list):
                    conditions.append(f"{db_col} = :{key}")
                    params[key] = int(val) if key == 'categoria' else str(val)

        # Filtro de Fechas
        if filters.get('start_date') and filters.get('end_date'):
            sd, ed = filters['start_date'], filters['end_date']
            conditions.append("((v.fecha BETWEEN :sd_25 AND :ed_25) OR (v.fecha BETWEEN :sd_26 AND :ed_26))")
            params.update({
                'sd_25': sd.replace(year=2025), 'ed_25': ed.replace(year=2025),
                'sd_26': sd.replace(year=2026), 'ed_26': ed.replace(year=2026)
            })

        where_sql = " WHERE " + " AND ".join(conditions) if conditions else ""

        # QUERY ACTUALIZADA: Se agrega tabla Vendedor y se selecciona descp_vendedor
        query = f"""
            SELECT
                v.fecha,
                CAST(v.monto AS NUMERIC) as monto,
                v.id_categoria,
                t.descp_tipo as tipo,
                m.descp_marca as marca,
                c.descp_cliente as cliente,
                ven.descp_vendedor as vendedor,
                cad.descp_cadena as cadena,
                c.id_cliente as codigo_cliente
            FROM registro_ventas_general v
            INNER JOIN tipo t ON CAST(v.id_tipo AS TEXT) = CAST(t.id_tipo AS TEXT)
            INNER JOIN marca m ON CAST(v.id_marca AS TEXT) = CAST(m.id_marca AS TEXT)
            INNER JOIN cliente c ON CAST(v.id_cliente AS TEXT) = CAST(c.id_cliente AS TEXT)
            INNER JOIN vendedor ven ON CAST(v.id_vendedor AS TEXT) = CAST(ven.id_vendedor AS TEXT)
            LEFT JOIN cliente_cadena cc ON CAST(c.id_cliente AS TEXT) = CAST(cc.id_cliente AS TEXT)
            LEFT JOIN cadena cad ON CAST(cc.id_cadena AS TEXT) = CAST(cad.id_cadena AS TEXT)
            {where_sql}
            ORDER BY v.fecha ASC
        """
        return get_dataframe(query, params)