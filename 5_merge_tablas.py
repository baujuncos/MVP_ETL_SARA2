import os
import pandas as pd

carpeta = "Macros"

dfs = []
id_counter = 1  # ID global

# Definir los nombres de las columnas en el orden deseado
columnas_finales = ["id_alimento", "nombre", "categoria", "kcal_100g", "proteinas_100g", "grasas_100g", "carbs_100g"]

for archivo in os.listdir(carpeta):
    if archivo.endswith(".csv"):
        ruta = os.path.join(carpeta, archivo)

        # Leer sin encabezados
        df = pd.read_csv(ruta, header=None)

        # Crear columna ID para este archivo
        filas = len(df)
        df.insert(0, "id_alimento", range(id_counter, id_counter + filas))

        # Actualizar contador global
        id_counter += filas

        # Asignar nombres de columnas si el archivo tiene el número correcto de columnas
        if df.shape[1] == len(columnas_finales):
            df.columns = columnas_finales
        else:
            # Si no coincide, asignar nombres genéricos y luego renombrar las primeras columnas
            columnas_actuales = [f"col_{i}" for i in range(df.shape[1])]
            df.columns = columnas_actuales
            for i, col in enumerate(columnas_finales):
                if i < len(df.columns):
                    df.rename(columns={df.columns[i]: col}, inplace=True)

        # Reordenar columnas por si acaso
        df = df[[col for col in columnas_finales if col in df.columns]]

        dfs.append(df)

        print(f"Merged: {archivo} ({filas} filas)")

# Concatenar todo
df_final = pd.concat(dfs, ignore_index=True)

# Guardar CSV final con encabezado
df_final.to_csv("base_macros.csv", index=False, header=True, encoding="utf-8")

print("\nMerge completo → archivo generado: base_macros.csv")