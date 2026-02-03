# Ubicación: C:\Users\hecto\Documents\Prg_locales\I_R_G\core\database.py
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import time
import sys

class DBInspector:
    """Protocolo de validación y diagnóstico para la terminal."""
    @staticmethod
    def log(msg, level="DB-AUDIT"):
        color = "\033[96m" if level == "DB-AUDIT" else "\033[93m"
        print(f"{color}[{level}]{reset} {msg}", file=sys.stderr)

# Variable auxiliar para colores en terminal
reset = "\033[0m"

def get_engine():
    try:
        s = st.secrets["postgres"]
        project_id = "extrlcvcgypwazxipvqm"

        conn_str = (
            f"postgresql://{s['user']}:{s['password']}@"
            f"{s['host']}:{s['port']}/{s['dbname']}"
            f"?sslmode=require&application_name={project_id}"
        )

        return create_engine(
            conn_str,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            connect_args={
                "connect_timeout": 15,
                "options": "-c client_encoding=utf8"
            }
        )
    except Exception as e:
        DBInspector.log(f"Fallo crítico en configuración de Engine: {e}", "ERROR")
        st.error(f"Error de configuración: {e}")
        return None

def get_dataframe(query, params=None):
    """Lectura con monitoreo de rendimiento y limpieza de IDs."""
    start_time = time.time()
    engine = get_engine()

    if engine:
        try:
            # Ejecución de la consulta
            df = pd.read_sql(text(query), engine, params=params or {})

            # Cálculo de latencia
            duration = (time.time() - start_time) * 1000

            # Limpieza y Auditoría de IDs
            clean_count = 0
            for col in df.columns:
                if col.startswith('id_') or 'codigo' in col:
                    if df[col].dtype == 'object':
                        # Verificamos si hay espacios antes de limpiar para reportar
                        original = df[col].astype(str)
                        cleaned = original.str.strip()
                        if not (original == cleaned).all():
                            clean_count += 1
                        df[col] = cleaned

            # Reporte en Terminal
            DBInspector.log(
                f"Consulta exitosa | Filas: {len(df)} | Latencia: {duration:.2f}ms"
            )
            if clean_count > 0:
                DBInspector.log(f"Se normalizaron {clean_count} columnas de IDs con espacios en blanco.", "AVISO")

            return df
        except Exception as e:
            DBInspector.log(f"Error en consulta SQL: {e}", "ERROR")
            st.error(f"Error al obtener datos: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

def commit_query(query, params=None, show_error=True):
    """Escritura con reporte de transacciones."""
    start_time = time.time()
    engine = get_engine()
    if engine:
        try:
            with engine.begin() as conn:
                result = conn.execute(text(query), params or {})
                duration = (time.time() - start_time) * 1000
                DBInspector.log(f"Commit exitoso | Afectadas: {result.rowcount} filas | {duration:.2f}ms")
                return True
        except Exception as e:
            if show_error:
                DBInspector.log(f"Fallo en Commit: {e}", "ERROR")
                st.error(f"Error en ejecución SQL: {e}")
            return False
    return False

def reset_id_sequence(table_name):
    """Protocolo de reseteo de secuencias."""
    DBInspector.log(f"Intentando resetear secuencia de tabla: {table_name}", "MANTENIMIENTO")
    try:
        query = f"SELECT setval(pg_get_serial_sequence('{table_name}', 'id_venta'), 1, false);"
        commit_query(query, show_error=False)
    except Exception as e:
        DBInspector.log(f"No se pudo resetear la secuencia (puede ser PK manual): {e}", "INFO")