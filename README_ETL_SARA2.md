# ETL SARA2 — Proceso de extracción y construcción de la base de datos de alimentos

## Descripción general

Este pipeline ETL transforma el PDF oficial del sistema SARA2 (Sistema de Análisis y Registro de Alimentos del Ministerio de Salud de la Nación Argentina) en una base de datos relacional limpia y utilizable para el cálculo automático de macronutrientes en NutriScan.

El proceso consta de 5 scripts que se ejecutan de forma secuencial, cada uno con una responsabilidad específica.

---

## Requisitos previos

```bash
pip install camelot-py[cv] pandas pdfminer.six
```

El archivo de entrada debe llamarse `SARA2_rotated.pdf` y estar ubicado en el mismo directorio que los scripts.

---

## Estructura de carpetas generada

```
/
├── SARA2_rotated.pdf
├── 1_extraccion_tablas.py
├── 2_seleccion_caracteristicas.py
├── 3_limpieza_datos.py
├── 4_data_labeling.py
├── 5_merge_tablas.py
├── Macros/               ← tablas de macronutrientes extraídas
├── Micros/               ← tablas de vitaminas y minerales (uso futuro)
└── base_macros.csv       ← base de datos final unificada
```

---

## Scripts del pipeline

### 1. `1_extraccion_tablas.py` — Extracción de tablas del PDF

**Qué hace:**
Lee el PDF de SARA2 página por página (páginas 18 a 139) usando Camelot con el método `lattice`, que funciona correctamente con tablas de bordes visibles como las del SARA2. Para cada tabla extraída, detecta el título correspondiente mediante coordenadas de texto usando `pdfminer`, lo que permite determinar si la tabla contiene macronutrientes o vitaminas/minerales. Las tablas se guardan automáticamente en la carpeta `Macros/` o `Micros/` según su tipo, con el nombre derivado del título oficial de la tabla en el PDF.

**Decisiones de diseño:**
- Se usa detección por coordenadas (posición Y del texto) para asociar cada título a su tabla, dado que el PDF no tiene una estructura de metadatos confiable.
- Se incluye un override manual para las páginas 74 y 75 donde la detección automática falla por el formato particular de esas páginas.
- Los nombres de archivo se generan automáticamente a partir del título oficial, evitando colisiones con un contador de partes.

**Entrada:** `SARA2_rotated.pdf`  
**Salida:** Archivos CSV individuales en `Macros/` y `Micros/`

---

### 2. `2_seleccion_caracteristicas.py` — Selección de columnas relevantes

**Qué hace:**
Elimina las columnas que no se necesitan para el MVP (ácidos grasos, alcohol, azúcares desagregados, etc.) y las primeras filas de cada CSV que corresponden a encabezados multi-nivel del PDF. Para el MVP se conservan únicamente las columnas de nombre del alimento, valor energético (kcal), proteínas, grasas totales y carbohidratos disponibles.

**Columnas eliminadas:** índices 2, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 18, 19, 20  
**Filas eliminadas:** primeras 4 filas (encabezados del PDF)

**Entrada:** CSVs en `Macros/`  
**Salida:** Los mismos archivos sobreescritos con solo las columnas necesarias

---

### 3. `3_limpieza_datos.py` — Limpieza y normalización de datos

**Qué hace:**
Aplica dos transformaciones sobre cada archivo CSV:

- **Limpieza de nombres de alimentos:** elimina saltos de línea, retornos de carro y guiones que Camelot introduce al parsear celdas multi-línea del PDF. Normaliza los espacios múltiples.
- **Normalización de decimales:** reemplaza la coma decimal por punto en las columnas numéricas (kcal, proteínas, grasas, carbohidratos), ya que SARA2 usa notación argentina con coma y PostgreSQL requiere punto decimal.

**Nota sobre `tr` y `nd`:** los valores `tr` (trazas) y `nd` (no determinado) presentes en SARA2 son manejados en esta etapa. `tr` se convierte a `0` por ser una cantidad insignificante, mientras que `nd` se deja como valor nulo indicando que el dato no fue medido.

**Entrada:** CSVs en `Macros/`  
**Salida:** Los mismos archivos sobreescritos con datos limpios y decimales normalizados

---

### 4. `4_data_labeling.py` — Etiquetado de categorías

**Qué hace:**
Infiere la categoría de cada grupo de alimentos a partir del nombre del archivo CSV, que fue generado en el paso 1 a partir del título oficial de la tabla en SARA2. Usa una expresión regular para extraer el segmento del nombre que identifica el grupo (por ejemplo, `verduras_y_hortalizas`, `carnes_y_aves`, `lacteos`) y lo inserta como una nueva columna en cada CSV.

**Ejemplo:**  
`tabla_1_a_verduras_y_hortalizas_macronutrientes.csv` → categoría: `verduras y hortalizas`

Esta columna permite filtrar alimentos por grupo en el buscador de NutriScan, mejorando la experiencia del usuario al registrar una comida.

**Entrada:** CSVs en `Macros/`  
**Salida:** Los mismos archivos con una columna de categoría agregada en la posición 2

---

### 5. `5_merge_tablas.py` — Unificación en un único dataset

**Qué hace:**
Concatena todos los CSVs de la carpeta `Macros/` en un único archivo `base_macros.csv`, asignando un ID global único y correlativo a cada fila. Este archivo es la base de datos final lista para ser importada a PostgreSQL.

**Estructura del archivo final:**

| Columna | Descripción |
|---|---|
| ID | Identificador único del alimento |
| Alimento | Nombre del alimento según SARA2 |
| Categoría | Grupo alimentario inferido del título de tabla |
| kcal | Valor energético cada 100g |
| Proteínas (g) | Contenido de proteínas cada 100g |
| Grasas (g) | Contenido de grasas totales cada 100g |
| Carbohidratos (g) | Carbohidratos disponibles cada 100g |

**Entrada:** Todos los CSVs en `Macros/`  
**Salida:** `base_macros.csv` con todos los alimentos unificados

---

## Ejecución del pipeline

Ejecutar los scripts en orden desde la carpeta raíz del proyecto:

```bash
python 1_extraccion_tablas.py
python 2_seleccion_caracteristicas.py
python 3_limpieza_datos.py
python 4_data_labeling.py
python 5_merge_tablas.py
```

---

## Carga a PostgreSQL (en caso de utilizar ese motor)

Una vez generado `base_macros.csv`, importarlo a la base de datos de NutriScan:

```python
import pandas as pd
from sqlalchemy import create_engine

df = pd.read_csv('base_macros.csv', header=None)
df.columns = ['id', 'nombre', 'categoria', 'kcal', 'proteinas_g', 'grasas_g', 'carbs_g']

engine = create_engine('postgresql://usuario:password@localhost/nutriscan')
df.to_sql('alimentos', engine, if_exists='append', index=False)
```

---

## Alcance y limitaciones

- El pipeline extrae únicamente tablas de **macronutrientes**. Las tablas de vitaminas y minerales se guardan en `Micros/` para uso futuro en el proyecto final.
- Algunas páginas del PDF con formatos atípicos requirieron overrides manuales en el script 1. Si se actualiza el PDF de SARA2, estos overrides deben revisarse.
- Los valores `nd` (no determinado) quedan como `NULL` en la base de datos. Esto es intencional: representan datos no medidos, no ausencia del nutriente.

---

## Fuente de datos

**SARA2 — Sistema de Análisis y Registro de Alimentos**  
Ministerio de Salud de la Nación Argentina  
Tabla de Composición Química de Alimentos de Argentina
