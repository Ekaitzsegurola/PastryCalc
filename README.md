# PastryCalc - Calculadora Profesional de Pastelería

Aplicación de escritorio para análisis técnico de recetas de pastelería.
Calcula el desglose completo de componentes (azúcares, grasas, materia seca,
líquidos, POD, PAC, Kcal, coste) y valida si la receta está equilibrada
según su categoría.

## Características

- **Base de datos de ~50 ingredientes** con perfiles completos de composición
- **Motor de cálculo** con desglose por ingrediente y totales agrupados
- **Validación por categoría** (ganache, helado, sorbete, mousse, etc.)
- **Interfaz gráfica moderna** con tema oscuro/claro
- **Guardar/cargar recetas** en formato JSON
- **Exportar a CSV**

## Requisitos

- Python 3.10+

## Instalación (desarrollo)

```bash
cd PastryCalc
uv venv --python 3.11 .venv
source .venv/bin/activate   # Linux/Mac
# .venv\Scripts\activate    # Windows
uv pip install -r requirements.txt
```

## Ejecutar

```bash
python run.py
```

## Tests

```bash
pytest
```

## Compilar .exe (Windows)

```bat
pip install -r requirements.txt
pip install pyinstaller
pyinstaller --onefile --windowed --name PastryCalc src/main.py
```

El ejecutable estará en `dist/PastryCalc.exe`.
