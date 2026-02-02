# Ubicación: C:\Users\hecto\Documents\Prg_locales\I_R_G\audit_terminal.py
from core.database import get_dataframe

def prueba_fuego_con_casting():
    print("🎯 PROBANDO FILTRADO CON CONVERSIÓN DE TIPOS (CASTING)")

    # El ID que vimos que existía físicamente
    id_prueba = "2047"

    # Forzamos a la DB a tratar la columna text como si fuera integer
    query = f"""
        SELECT id_cliente, fecha, monto
        FROM registro_ventas_general
        WHERE CAST(id_cliente AS INTEGER) = {id_prueba}
        LIMIT 5
    """

    try:
        df = get_dataframe(query)
        if not df.empty:
            print(f"✅ ¡CONEXIÓN EXITOSA! Usando CAST logramos ver al cliente {id_prueba}")
            print(df.to_string(index=False))
        else:
            print(f"❌ Ni con CAST encontramos el ID {id_prueba}. Verifica si tiene decimales como '2047.0'")
    except Exception as e:
        print(f"⚠️ Error en la conversión: {e}")

if __name__ == "__main__":
    prueba_fuego_con_casting()