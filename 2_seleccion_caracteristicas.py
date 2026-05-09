# Limpieza de columnas y filas en archivos CSV

import pandas as pd
from pathlib import Path

# Carpeta con los archivos CSV
# Asegúrate de que la carpeta "Macros" esté en el mismo lugar que este script
carpeta_macros = Path(__file__).parent / "Macros"

# Columnas a eliminar (índices base 0)
columnas_a_eliminar = [2, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 18, 19, 20]

# Filas a eliminar (1 a 5 del archivo original)
# Al usar header=None, la fila 1 es el índice 0, la fila 2 el 1, etc.
filas_a_eliminar = [0, 1, 2, 3] 

# Procesar cada CSV en la carpeta
for archivo_csv in carpeta_macros.glob("*.csv"):
    try:
        # IMPORTANTE: header=None hace que la primera fila sea tratada como datos
        df = pd.read_csv(archivo_csv, header=None)

        # 1. Eliminar columnas primero (es más seguro por si las filas varían)
        columnas_existentes = [c for c in columnas_a_eliminar if c < len(df.columns)]
        df = df.drop(df.columns[columnas_existentes], axis=1)

        # 2. Eliminar filas (0 a 4)
        df = df.drop(index=filas_a_eliminar, errors='ignore')

        # 3. Guardar el archivo procesado
        # header=False para que no invente encabezados (0, 1, 2...) al guardar
        df.to_csv(archivo_csv, index=False, header=False)
        
        print(f"✓ Procesado: {archivo_csv.name}")
        
    except Exception as e:
        print(f"✗ Error en {archivo_csv.name}: {e}")

print("\nLimpieza de base de datos completada con éxito.")

# Mover archivo específico a la carpeta Micros
archivo_a_mover = carpeta_macros / "tabla_19_a_sales_macronutrientes_parte_2.csv"
carpeta_micros = Path(__file__).parent / "Micros"
if archivo_a_mover.exists():
    carpeta_micros.mkdir(exist_ok=True)
    destino = carpeta_micros / archivo_a_mover.name
    archivo_a_mover.rename(destino)
    print(f"Archivo movido a Micros: {archivo_a_mover.name}")
else:
    print("El archivo 'tabla_19_a_sales_macronutrientes_parte_2.csv' no se encontró para mover.")