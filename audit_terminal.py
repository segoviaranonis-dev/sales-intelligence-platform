# Ubicación: C:\Users\hecto\Documents\Prg_locales\I_R_G\audit_terminal.py
import pandas as pd
import time
from sqlalchemy import create_engine, text
from core.database import get_dataframe

# --- CONFIGURACIÓN DE EMERGENCIA ---
# Reemplaza con tus datos reales si el import falla
DB_URL = "postgresql://postgres:postgres@localhost:5432/postgres" # <--- AJUSTA ESTO

def vaciar_tablas_directo():
    print("\n" + "!"*50)
    print("⚠️  EJECUTANDO LIMPIEZA FORZADA (VÍA SQL DIRECTO)")
    print("!"*50)

    confirmacion = input("\n¿Confirmas vaciar 'cadena' y 'cliente_cadena'? (SI): ")
    if confirmacion.upper() == 'SI':
        try:
            # Creamos un engine local para esta operación de mantenimiento
            engine_local = create_engine(DB_URL)

            with engine_local.connect() as conn:
                # Iniciamos una transacción manual
                with conn.begin():
                    print("🧹 Vaciando cliente_cadena...")
                    conn.execute(text("TRUNCATE TABLE cliente_cadena RESTART IDENTITY CASCADE;"))
                    print("🧹 Vaciando cadena...")
                    conn.execute(text("TRUNCATE TABLE cadena RESTART IDENTITY CASCADE;"))

            print("\n✅ LIMPIEZA TOTAL COMPLETADA CON ÉXITO.")
            time.sleep(1) # Pausa para que el DB respire
        except Exception as e:
            print(f"❌ ERROR CRÍTICO AL VACIAR: {e}")
            print("\nPosible causa: La URL de conexión en este script no es correcta.")
    else:
        print("\n❌ Operación cancelada.")

def ejecutar_auditoria():
    print("\n" + "="*80)
    print("🔍 MÓDULO DE MANTENIMIENTO DE BASE DE DATOS")
    print("="*80)

    accion = input("¿Deseas VACIAR las tablas 'cadena' y 'cliente_cadena' ahora? (s/n): ")
    if accion.lower() == 's':
        vaciar_tablas_directo()

    print("\n[ VERIFICACIÓN DE RESULTADOS ]")
    try:
        for tabla in ['cadena', 'cliente_cadena']:
            df = get_dataframe(f"SELECT * FROM {tabla} LIMIT 5;")
            if df is not None and not df.empty:
                print(f"❌ LA TABLA '{tabla}' AÚN TIENE DATOS.")
            else:
                print(f"✨ LA TABLA '{tabla}' ESTÁ TOTALMENTE VACÍA.")
    except:
        print("No se pudo verificar el estado de las tablas.")

    print("\n" + "="*80)
    print("✅ PROCESO FINALIZADO")

if __name__ == "__main__":
    ejecutar_auditoria()