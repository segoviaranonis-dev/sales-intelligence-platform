# Ubicación: C:\Users\hecto\Documents\Prg_locales\I_R_G\pages\00_importar_datos.py

import streamlit as st
from core.styles import apply_styles, header_section
from modules.import_data.ui import render_import_interface

# 1. Inyectar el ADN Visual (Hito 1.1)
apply_styles()

# 2. Dibujar la Cabecera Profesional
header_section("Importación de Datos", "Carga y Sincronización del Cerebro")

# 3. Invocar la interfaz de la habitación (Módulo Atómico)
render_import_interface()