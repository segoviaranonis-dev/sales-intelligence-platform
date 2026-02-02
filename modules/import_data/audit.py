# Ubicación: C:\Users\hecto\Documents\Prg_locales\I_R_G\modules\import_data\audit.py

import streamlit as st
from core.database import get_dataframe

class DataAuditor:
    """Herramienta de diagnóstico para verificar la estructura real de la DB."""

    @staticmethod
    def get_table_columns(table_name):
        """Consulta el esquema de información de la base de datos."""
        query = """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = :table
            ORDER BY ordinal_position
        """
        df = get_dataframe(query, {"table": table_name})
        return df['column_name'].tolist() if not df.empty else []

    @staticmethod
    def run_full_audit():
        """Muestra en pantalla la estructura técnica de las tablas maestras."""
        st.subheader("🕵️ Auditoría de Estructura de Datos")
        tables = ['cliente', 'vendedor', 'marca', 'venta']

        audit_data = {}
        for table in tables:
            cols = DataAuditor.get_table_columns(table)
            audit_data[table] = cols
            st.text(f"Tabla '{table}': {', '.join(cols)}")

        return audit_data