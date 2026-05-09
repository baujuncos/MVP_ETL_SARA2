import os
import pandas as pd
import re

carpeta = "Macros"

regex_grupo = re.compile(r"tabla_\d+_[a-z]_([^_]+(?:_[^_]+)*)_macronutrientes", re.IGNORECASE)

for archivo in os.listdir(carpeta):
    if archivo.endswith(".csv"):
        ruta = os.path.join(carpeta, archivo)

        match = regex_grupo.search(archivo)
        if match:
            grupo = match.group(1).replace("_", " ")
        else:
            grupo = "desconocido"

        # Leer sin encabezados
        df = pd.read_csv(ruta, header=None)

        # Insertar columna sin nombre en posición 2 (índice 1)
        df.insert(1, "", grupo)

        df.to_csv(ruta, index=False, header=False, encoding="utf-8")

        print(f"Actualizado: {archivo} → Grupo agregado: {grupo}")