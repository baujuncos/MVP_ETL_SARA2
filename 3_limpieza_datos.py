import pandas as pd
from pathlib import Path

# Configuración de carpetas
carpeta_macros = Path(__file__).parent / "Macros"

def sanitizar_datos_sara():
    archivos = list(carpeta_macros.glob("*.csv"))
    
    if not archivos:
        print("No se encontraron archivos en la carpeta 'Macros'.")
        return

    for archivo in archivos:
        try:
            # 1. Leer el CSV (usamos utf8 por compatibilidad con SARA)
            df = pd.read_csv(archivo, header=None, encoding='utf-8')

            # --- PARTE A: Limpiar Columna 1 (Nombres) ---
            def limpiar_nombre(valor):
                if pd.isnull(valor): return valor
                texto = str(valor).replace('\n', ' ').replace('\r', ' ').replace('-', '')
                return ' '.join(texto.split())

            df[0] = df[0].apply(limpiar_nombre)


            # --- PARTE B: Normalizar Decimales (Columnas 3, 4 y 5 -> índices 2, 3, 4) ---
            columnas_decimales = [2, 3, 4]
            
            import re
            for col in columnas_decimales:
                if col < len(df.columns):
                    def normalizar_numero(valor):
                        if pd.isnull(valor):
                            return valor
                        s = str(valor)
                        # Detectar número entre comillas dobles
                        match = re.fullmatch(r'"([0-9]+,[0-9]+|[0-9]+)"', s)
                        if match:
                            s = match.group(1)
                        s = s.replace(',', '.')
                        return s
                    df[col] = df[col].apply(normalizar_numero)
            

            # 4. Guardar los cambios
            # Usamos utf-8-sig para que Excel y VS Code reconozcan bien los acentos
            df.to_csv(archivo, index=False, header=False, encoding='utf-8-sig')
            print(f"✓ Procesado: {archivo.name} (Nombres y Decimales limpios)")

        except Exception as e:
            print(f"✗ Error en {archivo.name}: {e}")

if __name__ == "__main__":
    sanitizar_datos_sara()
    print("\nSanitización completa: Columna 1 sin saltos/guiones y Cols 3-5 con punto decimal.")