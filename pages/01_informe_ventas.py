# Ubicación: C:\Users\hecto\Documents\Prg_locales\I_R_G\pages\01_informe_ventas.py

import streamlit as st
from modules.sales_report.ui import render_sales_report_interface

# 1. Configuración de la Ventana (Máximo espacio para datos)
st.set_page_config(
    page_title="Informe de Ventas | RIMEC",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """
    Punto de entrada para el Análisis de Ventas.
    Llama a la interfaz modular que ahora contiene las 4 pestañas
    y la lógica de exportación PDF.
    """
    try:
        # 2. Renderizar la Interfaz Modular
        render_sales_report_interface()

    except Exception as e:
        # Este bloque ahora mostrará errores específicos de datos o librerías faltantes
        st.error(f"⚠️ Error al cargar el Módulo de Ventas: {e}")
        st.info("Verifica la conexión con la base de datos o si faltan dependencias (pip install reportlab).")

if __name__ == "__main__":
    main()