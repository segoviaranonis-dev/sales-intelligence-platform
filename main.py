# Ubicación: C:\Users\hecto\Documents\Prg_locales\I_R_G\main.py

import streamlit as st
from core.database import get_engine
from core.styles import apply_styles, header_section

# 1. Configuración de página (Debe ser la primera instrucción)
st.set_page_config(
    page_title="RIMEC - ERP Inteligente",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Aplicar ADN Visual (Hito 1.1)
apply_styles()

# 3. Cabecera con identidad RIMEC
header_section("Ciudad RIMEC", "Infraestructura de Gestión BI v2.0")

# 4. Orquestación de Conexión y Estado del Sistema
try:
    engine = get_engine()

    if engine:
        with st.container():
            st.success("✅ Conexión al cerebro (sa-east-1) establecida correctamente.")

            # Guía visual para el usuario
            st.markdown("""
            ### Estado de la Obra:
            Actualmente nos encontramos en la **Etapa 1: Infraestructura**.

            **Siguientes pasos:**
            1. Diríjase al menú lateral izquierdo.
            2. Seleccione la **Habitación 0: Importación** para cargar sus archivos Excel.
            3. Verifique que los nombres de los archivos coincidan con las tablas maestras.
            """)

            # Sidebar info
            st.sidebar.markdown("---")
            st.sidebar.info("Conectado a: Supabase Pooler (Port 6543)")
    else:
        st.error("❌ Fallo crítico: El motor de energía no pudo iniciarse.")
        st.warning("Verifique la configuración en su archivo .streamlit/secrets.toml")

except Exception as e:
    st.error(f"Hubo un error inesperado al iniciar la ciudad: {e}")