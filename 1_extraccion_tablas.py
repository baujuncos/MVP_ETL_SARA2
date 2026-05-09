import camelot
import pandas as pd
import re
import os
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTTextLine

file_path = "SARA2_rotated.pdf"

# Crear carpetas si no existen
os.makedirs("Macros", exist_ok=True)
os.makedirs("Micros", exist_ok=True)

# Regex para títulos reales de tabla
regex_titulo = re.compile(r"^TABLA\s+\d+\.[A-Z]:", re.IGNORECASE)

def limpiar_nombre(texto):
    texto = texto.lower()
    texto = re.sub(r'[^a-z0-9áéíóúñ]+', '_', texto)
    return texto.strip('_')

def extraer_lineas_con_posicion(pdf_path, page_number):
    lineas = []
    for page_layout in extract_pages(pdf_path, page_numbers=[page_number - 1]):
        for element in page_layout:
            if isinstance(element, LTTextContainer):
                for text_line in element:
                    if isinstance(text_line, LTTextLine):
                        texto = text_line.get_text().strip()
                        x0, y0, x1, y1 = text_line.bbox
                        lineas.append((texto, x0, y0, x1, y1))
    return lineas

def obtener_titulos_con_posicion(lineas):
    titulos = []
    for texto, x0, y0, x1, y1 in lineas:
        if regex_titulo.match(texto):
            titulos.append((texto, y0, y1))
    return titulos

def asignar_titulo_a_tabla(titulos, bbox_tabla):
    x1, y1, x2, y2 = bbox_tabla
    y_top_tabla = y2

    candidatos = []
    for texto, y0, y1_titulo in titulos:
        if y1_titulo > y_top_tabla:  # título arriba de la tabla
            distancia = y1_titulo - y_top_tabla
            candidatos.append((distancia, texto))

    if candidatos:
        candidatos.sort(key=lambda x: x[0])
        return candidatos[0][1]

    return None

# Contador para evitar sobrescrituras
contador_titulos = {}

def generar_nombre_unico(titulo):
    base = limpiar_nombre(titulo)

    if base not in contador_titulos:
        contador_titulos[base] = 1
        return base

    contador_titulos[base] += 1
    return f"{base}_parte_{contador_titulos[base]}"

# Extraer tablas
tables = camelot.read_pdf(file_path, pages='18-139', flavor='lattice')
print(f"Se encontraron {tables.n} tablas.")

cache_lineas = {}

for i, table in enumerate(tables):
    page_number = table.page
    print(f"\nProcesando tabla {i} en página {page_number}...")

    # Extraer texto con coordenadas
    if page_number not in cache_lineas:
        lineas = extraer_lineas_con_posicion(file_path, page_number)
        cache_lineas[page_number] = lineas
    else:
        lineas = cache_lineas[page_number]

    titulos = obtener_titulos_con_posicion(lineas)
    bbox = table._bbox

    # Asignar título por coordenadas
    titulo_detectado = asignar_titulo_a_tabla(titulos, bbox)

    # OVERRIDE manual para tablas 56 y 57
    if page_number == 74:
        titulo_detectado = "TABLA 5.A: YOGURES, MACRONUTRIENTES"
    if page_number == 75:
        titulo_detectado = "TABLA 5.A: YOGURES, VITAMINAS Y MINERALES"

    # Generar nombre único
    if titulo_detectado:
        nombre_archivo = generar_nombre_unico(titulo_detectado)
    else:
        nombre_archivo = f"tabla_quimica_{i}"

    # Elegir carpeta según tipo
    titulo_lower = titulo_detectado.lower() if titulo_detectado else ""

    if "macronutrientes" in titulo_lower:
        carpeta = "Macros"
    elif "vitaminas" in titulo_lower or "minerales" in titulo_lower:
        carpeta = "Micros"
    else:
        carpeta = "Macros"  # fallback

    ruta_salida = os.path.join(carpeta, f"{nombre_archivo}.csv")

    print(f"Título asignado: {titulo_detectado}")
    print(f"Guardando en: {ruta_salida}")

    df = table.df
    df.to_csv(ruta_salida, index=False, encoding='utf-8')

print("\n¡Extracción completada!")