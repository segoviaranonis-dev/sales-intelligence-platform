# Ubicación: C:\Users\hecto\Documents\Prg_locales\I_R_G\modules\import_data\logic.py

import pandas as pd
import streamlit as st
from core.database import get_engine, commit_query, reset_id_sequence

class ImportLogic:
    @staticmethod
    def process_excel(file):
        """Lee el Excel y asegura que los IDs no se carguen con decimales."""
        try:
            dict_dfs = pd.read_excel(file, sheet_name=None)
            # Sanitización inmediata al leer
            for sheet in dict_dfs:
                df = dict_dfs[sheet]
                for col in df.columns:
                    if col.startswith('id_'):
                        # Convertimos a numérico, quitamos nulos, pasamos a Int y luego a String limpio
                        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int).astype(str)
                        # Si quedó algún "0" por nulo, lo ideal es dejarlo vacío o manejarlo
                        df[col] = df[col].replace('0', '')
                dict_dfs[sheet] = df
            return dict_dfs
        except Exception as e:
            st.error(f"Error al leer el Excel: {e}")
            return None

    @staticmethod
    def validate_integrity(df, table_name):
        """Comprueba que los IDs en el Excel existan en las tablas maestras."""
        engine = get_engine()
        # Nombres de columnas corregidos según auditoría real
        if table_name in ['venta', 'registro_ventas_general']:
            check_map = {
                'id_cliente': 'cliente',
                'id_vendedor': 'vendedor',
                'id_marca': 'marca'
            }
            for col, master_table in check_map.items():
                if col in df.columns:
                    # Traemos IDs como texto y limpiamos
                    query = f"SELECT id_{master_table} FROM {master_table}"
                    db_ids = pd.read_sql(query, engine).iloc[:, 0].astype(str).unique()

                    # Detectamos huérfanos
                    huerfanos = df[~df[col].astype(str).isin(db_ids)][col].unique()

                    if len(huerfanos) > 0 and huerfanos[0] != '':
                        st.error(f"❌ Error de Integridad: Los IDs {huerfanos} en '{col}' no existen en '{master_table}'.")
                        return False
        return True

    @staticmethod
    def upload_to_db(df, table_name, display_name):
        """Sube un DataFrame aplicando limpieza y conversión forzada de tipos."""
        engine = get_engine()
        if engine is None: return False

        try:
            # 1. Limpieza previa
            if table_name not in ['venta', 'registro_ventas_general']:
                # Para tablas maestras, reseteamos y borramos todo
                commit_query(f"DELETE FROM {table_name}")
            else:
                # Para ventas, borramos solo el rango que vamos a re-subir
                if 'fecha' in df.columns:
                    df['fecha'] = pd.to_datetime(df['fecha'])
                    fecha_min = df['fecha'].min().strftime('%Y-%m-%d')
                    commit_query(f"DELETE FROM {table_name} WHERE fecha >= '{fecha_min}'")
                    st.info(f"🧹 Limpieza: Registros de {display_name} eliminados desde {fecha_min}.")

            # 2. Validación de Integridad
            if not ImportLogic.validate_integrity(df, table_name):
                return False

            # 3. Carga masiva (Asegurando que Pandas no cambie tipos al subir)
            df.to_sql(table_name, engine, if_exists='append', index=False, method='multi')

            st.success(f"✅ {display_name} cargado correctamente ({len(df)} registros).")
            return True
        except Exception as e:
            st.error(f"❌ Error al cargar {display_name}: {e}")
            return False

    @classmethod
    def run_full_import(cls, dict_dfs):
        """Orquestador de carga actualizado con tablas reales."""
        mapping = {
            'cliente': ('cliente', 'Maestra de Clientes'),
            'marca': ('marca', 'Maestra de Marcas'),
            'vendedor': ('vendedor', 'Maestra de Vendedores'),
            'cadena': ('cadena', 'Maestra de Cadenas'),
            'cliente_cadena': ('cliente_cadena', 'Relación Cliente-Cadena'),
            'ventas': ('registro_ventas_general', 'Histórico de Ventas')
        }

        for sheet, (table, name) in mapping.items():
            if sheet in dict_dfs:
                cls.upload_to_db(dict_dfs[sheet], table, name)