# Ubicación: C:\Users\hecto\Documents\Prg_locales\I_R_G\core\database.py

import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

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
            connect_args={
                "connect_timeout": 15,
                "options": "-c client_encoding=utf8"
            }
        )
    except Exception as e:
        st.error(f"Error de configuración: {e}")
        return None

def get_dataframe(query, params=None):
    """
    Motor de lectura: Transforma consultas SQL en DataFrames.
    Ajustado para manejar la inconsistencia de tipos TEXT vs INT.
    """
    engine = get_engine()
    if engine:
        try:
            # Forzamos que los parámetros sean tratados limpiamente
            df = pd.read_sql(text(query), engine, params=params or {})

            # Limpieza post-lectura: Si una columna se llama 'id_...' y es texto,
            # eliminamos espacios en blanco que puedan venir de la DB
            for col in df.columns:
                if col.startswith('id_') and df[col].dtype == 'object':
                    df[col] = df[col].astype(str).str.strip()

            return df
        except Exception as e:
            st.error(f"Error al obtener datos: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

def commit_query(query, params=None, show_error=True):
    """Ejecuta sentencias de escritura (INSERT, DELETE, UPDATE)."""
    engine = get_engine()
    if engine:
        try:
            with engine.begin() as conn:
                conn.execute(text(query), params or {})
                return True
        except Exception as e:
            if show_error:
                st.error(f"Error en ejecución SQL: {e}")
            return False
    return False

def reset_id_sequence(table_name):
    """Resetea el contador de IDs de una tabla."""
    try:
        # Nota: Como tus IDs son TEXT, esta función solo servirá
        # para tablas con PK autoincremental real (bigint).
        query = f"SELECT setval(pg_get_serial_sequence('{table_name}', 'id_venta'), 1, false);"
        commit_query(query, show_error=False)
    except:
        pass