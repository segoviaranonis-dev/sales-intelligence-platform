# Ubicación: C:\Users\hecto\Documents\Prg_locales\I_R_G\core\styles.py
import streamlit as st

def apply_styles():
    st.markdown("""
        <style>
        .stApp { background-color: #F1F5F9; }
        .main-title { color: #0F172A !important; font-size: 2rem; font-weight: 800; }
        .title-underline { height: 4px; width: 60px; background-color: #2563EB; border-radius: 2px; margin-bottom: 25px; }

        /* Estilos de Tarjetas */
        .rimec-card {
            background-color: #FFFFFF; padding: 25px; border-radius: 8px;
            border-left: 5px solid #2563EB; box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: left; margin-bottom: 15px; height: 130px;
        }
        .card-title { color: #475569; font-size: 0.85rem; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase; }
        .card-value { color: #1E293B; font-size: 1.6rem; font-weight: 800; margin-top: 5px; }

        /* Badges para Deltas */
        .delta-tag {
            display: inline-block; padding: 2px 8px; border-radius: 4px;
            font-size: 0.75rem; font-weight: 700; margin-top: 8px;
        }
        .tag-riesgo { background-color: #FEE2E2; color: #B91C1C; }
        .tag-nuevo { background-color: #DCFCE7; color: #15803D; }
        </style>
    """, unsafe_allow_html=True)

def header_section(title, subtitle=None):
    st.markdown(f'<h1 class="main-title">{title}</h1>', unsafe_allow_html=True)
    st.markdown('<div class="title-underline"></div>', unsafe_allow_html=True)
    if subtitle: st.markdown(f'<p style="color:#64748B;">{subtitle}</p>', unsafe_allow_html=True)

def card_style(titulo, valor, is_delta=False, delta_val=None):
    """
    Versión robustecida para aceptar métricas de cohorte.
    is_delta: Activa el badge de color.
    delta_val: Texto a mostrar en el badge (Riesgo/Nuevos).
    """
    # Lógica de color según la etiqueta
    tag_class = ""
    if is_delta:
        tag_class = "tag-riesgo" if delta_val == "Riesgo" else "tag-nuevo"
        delta_html = f'<div class="delta-tag {tag_class}">{delta_val}</div>'
    else:
        delta_html = ""

    st.markdown(f"""
        <div class="rimec-card">
            <div class="card-title">{titulo}</div>
            <div class="card-value">{valor}</div>
            {delta_html}
        </div>
    """, unsafe_allow_html=True)