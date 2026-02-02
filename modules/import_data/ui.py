# Ubicación: C:\Users\hecto\Documents\Prg_locales\I_R_G\modules\import_data\ui.py

import streamlit as st
from .logic import ImportLogic
from core.styles import apply_styles, header_section, card_style

def render_import_interface():
    apply_styles()
    header_section("Centro de Carga Masiva", "Gestión de Integridad y Sincronización")

    st.markdown("### 1. Selecciona el destino de los datos")

    tipo_carga = st.radio(
        "¿Qué tipo de información vas a procesar?",
        [
            "Registro de Ventas General (Histórico)",
            "Tablas Maestras (Individuales)",
            "Relaciones y Cadenas (Intermedias)",
            "Sincronización Total (Excel Multi-hoja)"
        ],
        help="Recuerda: Las ventas dependen de que las tablas maestras ya existan."
    )

    # Lógica de Mapeo
    multiple = False

    if "Registro de Ventas General" in tipo_carga:
        tabla_db = "registro_ventas_general"
        instruccion = "Archivo requerido: **registro_ventas_general.xlsx**"

    elif "Tablas Maestras" in tipo_carga:
        # AGREGADO 'cliente_cadena' a la lista para que aparezca en el selectbox de la captura
        tabla_db = st.selectbox("Selecciona la Tabla Maestra:",
            ["cliente", "vendedor", "marca", "producto", "proveedor", "tipo", "cadena", "cliente_cadena", "comision", "grupo", "plazo"])
        instruccion = f"Archivo requerido: **{tabla_db}.xlsx**"

    elif "Relaciones y Cadenas" in tipo_carga:
        # Esta opción del radio button ya la tenías bien, pero ahora también está en el selectbox de arriba
        tabla_db = "cliente_cadena"
        instruccion = "Archivo requerido: **cliente_cadena.xlsx** (Columnas: id_cliente, id_cadena)"

    else:
        tabla_db = "total"
        instruccion = "El Excel debe contener pestañas: 'clientes', 'marcas', 'vendedores', 'tipo', 'cadena', 'cliente_cadena' y 'ventas'."
        multiple = True

    st.info(instruccion)


    archivo = st.file_uploader("Arrastra tu archivo Excel aquí", type=["xlsx"])

    if archivo is not None:
        nombre_correcto = True
        # Validación de nombre (solo para cargas individuales)
        if not multiple:
            if archivo.name != f"{tabla_db}.xlsx":
                st.error(f"❌ Error de Identidad: El archivo es '{archivo.name}', pero debe ser '{tabla_db}.xlsx'.")
                nombre_correcto = False

        if nombre_correcto:
            st.success(f"✅ Archivo listo para procesar: {tabla_db}")

            # --- PRE-VISUALIZACIÓN ---
            with st.expander("👁️ Vista previa de los datos a importar"):
                dict_dfs = ImportLogic.process_excel(archivo)
                if dict_dfs:
                    # Si es múltiple, mostramos la primera hoja, si es simple, la única que hay
                    hoja_preview = list(dict_dfs.keys())[0]
                    st.dataframe(dict_dfs[hoja_preview].head(10), use_container_width=True)

            # --- BOTÓN DE CARGA ---
            if st.button("🚀 Iniciar Carga en Base de Datos"):
                with st.spinner("Ejecutando Smart Importer..."):
                    try:
                        if dict_dfs:
                            if multiple:
                                ImportLogic.run_full_import(dict_dfs)
                                st.balloons()
                                card_style("Sincronización Total Exitosa", "Todas las tablas han sido actualizadas.")
                            else:
                                # Procesar carga individual
                                hoja_a_procesar = list(dict_dfs.keys())[0]
                                exito = ImportLogic.upload_to_db(
                                    dict_dfs[hoja_a_procesar],
                                    tabla_db,
                                    f"Carga de {tabla_db.replace('_', ' ').title()}"
                                )
                                if exito:
                                    st.balloons()
                                    st.success(f"Datos integrados correctamente en la tabla '{tabla_db}'")
                    except Exception as e:
                        st.error(f"Error en comunicación con la base de datos: {e}")