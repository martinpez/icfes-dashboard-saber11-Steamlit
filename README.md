# ICFES Dashboard

## Descripción
Dashboard interactivo para explorar y visualizar los resultados de las pruebas Saber 11 del ICFES Colombia (2018-2021). Permite analizar el rendimiento académico de los estudiantes por departamento, tipo de colegio, género, estrato socioeconómico y más variables.

## Dataset
- **Fuente**: ICFES Colombia
- **URL**: https://www.icfes.gov.co/
- **Descripción**: Pruebas Saber 11 - Evaluación estandarizada de estudiantes de educación media en Colombia. Contiene puntajes por competencia (Lectura Crítica, Matemáticas, Ciencias Naturales, Sociales y Ciudadanas, Inglés), información sociodemográfica (género, estrato socioeconómico), y datos institucionales (tipo de colegio, ubicación).

## Hallazgos Principales
1. **Diferencias regionales significativas**: Existe una brecha notable en el puntaje global promedio entre departamentos. Bogotá y los departamentos andinos presentan los mejores resultados.
2. **Brecha estrato-competencia**: La brecha entre estrato 1 y estrato 6 varía según la competencia, siendo más pronunciada en Matemáticas e Inglés.
3. **Colegios oficiales vs no oficiales**: Los colegios no oficiales mantienen consistentemente mejores puntajes, pero la brecha se ha reducido ligeramente en años recientes.
4. **Diferencias por género**: Las mujeres superan en Lectura Crítica y Sociales; los hombres en Matemáticas e Inglés. La brecha de género varía significativamente por competencia.
5. **Correlación NSE-rendimiento**: Existe una correlación positiva fuerte entre el índice socioeconómico (INSE) y el puntaje global. La pendiente es más pronunciada en colegios oficiales.
6. **Concentración de excelencia**: Los mejores colegios (Top 20) están predominantemente en Bogotá y son mayoritariamente no oficiales.

## Visualizaciones Implementadas
1. Mapa coroplético de puntaje global promedio por departamento
2. Heatmap de promedio por estrato socioeconómico y competencia
3. Serie temporal de puntaje por tipo de collège (oficial/no oficial)
4. Gráfico de barras de distribución por género por competencia
5. Scatter plot de correlación NSE vs puntaje por tipo de colegio
6. Ranking Top 20 de colegios por puntaje global

## Tecnologías Utilizadas
- Framework: Streamlit
- Lenguaje: Python
- Bibliotecas: pandas, plotly, sqlalchemy, psycopg2-binary
- Base de datos: PostgreSQL (Amazon RDS)

## Instalación y Ejecución Local

### Requisitos Previos
- Python 3.9+
- PostgreSQL client (opcional)

### Instrucciones

```bash
# Clonar repositorio
git clone https://github.com/usuario/repo.git
cd repo

# Crear entorno virtual
python -m venv .venv
source .venv/Scripts/activate  # En Windows: .venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno (.env)
# Edita el archivo .env con tus credenciales de base de datos

# Ejecutar aplicación
streamlit run app.py
```

### Variables de entorno (.env)

Crea un archivo `.env` en la raíz del proyecto con tus credenciales:

```env
DB_HOST=tu_host
DB_PORT=5432
DB_NAME=icfes_db
DB_USER=tu_usuario
DB_PASSWORD=tu_password
```