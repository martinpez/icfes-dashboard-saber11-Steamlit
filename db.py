import os
import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "icfes-db-prod.c5uoemycu8hy.us-east-2.rds.amazonaws.com")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "icfes_db")
DB_USER = os.getenv("DB_USER", "icfes_admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Colombia.CO")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

COLORS = {
    'primary': '#003857',
    'secondary': '#006687',
    'accent': '#9dcbf4',
    'success': '#2A9D8F',
    'danger': '#D62828',
    'warning': '#F77F00',
    'female': '#D4537E',
    'male': '#457B9D',
    'oficial': '#003857',
    'nooficial': '#2A9D8F',
}

CHOROPLETH_SCALE = ['#D62828', '#F77F00', '#2A9D8F']

COMPETENCIAS = ['Lectura Crítica', 'Matemáticas', 'Ciencias Naturales', 'Sociales y Ciudadanas', 'Inglés']
COMPETENCIAS_COLS = ['PUNT_LECTURA_CRITICA', 'PUNT_MATEMATICAS', 'PUNT_C_NATURALES', 'PUNT_SOCIALES_CIUDADANAS', 'PUNT_INGLES']

@st.cache_resource
def get_engine():
    return create_engine(
        DATABASE_URL,
        poolclass=NullPool,
        connect_args={"connect_timeout": 30}
    )

def fetch_data(query: str, params: tuple = None):
    engine = get_engine()
    try:
        with engine.connect() as conn:
            if params:
                result = pd.read_sql(query, conn, params=params)
            else:
                result = pd.read_sql(query, conn)
            return result
    except Exception as e:
        print(f"Error: {e}")
        return pd.DataFrame()

def build_filters(anio=None, genero=None, estrato=None, naturaleza=None, depto=None):
    conditions = []
    params = []
    
    if anio:
        conditions.append("LEFT(i.\"PERIODO\"::varchar, 4) = %s")
        params.append(anio)
    if genero:
        conditions.append("i.\"ESTU_GENERO\" = %s")
        params.append(genero)
    if estrato:
        conditions.append("i.\"FAMI_ESTRATOVIVIENDA\" = %s")
        params.append(estrato)
    if naturaleza:
        conditions.append("i.\"COLE_NATURALEZA\" = %s")
        params.append(naturaleza)
    if depto:
        conditions.append("i.\"COLE_DEPTO_UBICACION\" = %s")
        params.append(depto)
    
    base_filters = [
        'i."PUNT_GLOBAL" BETWEEN 0 AND 500',
        'i."ESTU_GENERO" IN (\'M\', \'F\')'
    ]
    
    all_conditions = conditions + base_filters
    where_clause = " AND ".join(all_conditions)
    
    return where_clause, tuple(params)

@st.cache_data(ttl=300)
def get_score_by_department(anio=None, genero=None, estrato=None, naturaleza=None, depto=None):
    where_clause, params = build_filters(anio, genero, estrato, naturaleza, depto)
    
    query = f"""
    SELECT
        i."COLE_DEPTO_UBICACION" AS departamento,
        LEFT(i."PERIODO"::varchar, 4) AS anio,
        ROUND(AVG(i."PUNT_GLOBAL")::numeric, 2) AS prom_global,
        COUNT(*) AS total_estudiantes
    FROM icfes i
    WHERE {where_clause}
    GROUP BY i."COLE_DEPTO_UBICACION", LEFT(i."PERIODO"::varchar, 4)
    ORDER BY prom_global DESC
    """
    return fetch_data(query, params)

@st.cache_data(ttl=300)
def get_heatmap_estrato_competencia(anio=None, genero=None, estrato=None, naturaleza=None, depto=None):
    where_clause, params = build_filters(anio, genero, estrato, naturaleza, depto)
    
    query = f"""
    SELECT
        i."FAMI_ESTRATOVIVIENDA" AS estrato,
        ROUND(AVG(i."PUNT_LECTURA_CRITICA")::numeric, 2) AS prom_lectura,
        ROUND(AVG(i."PUNT_MATEMATICAS")::numeric, 2) AS prom_matematicas,
        ROUND(AVG(i."PUNT_C_NATURALES")::numeric, 2) AS prom_naturales,
        ROUND(AVG(i."PUNT_SOCIALES_CIUDADANAS")::numeric, 2) AS prom_sociales,
        ROUND(AVG(i."PUNT_INGLES")::numeric, 2) AS prom_ingles,
        COUNT(*) AS n
    FROM icfes i
    WHERE {where_clause}
    GROUP BY i."FAMI_ESTRATOVIVIENDA"
    ORDER BY i."FAMI_ESTRATOVIVIENDA"
    """
    return fetch_data(query, params)

@st.cache_data(ttl=300)
def get_timeseries_by_school_type(anio=None, genero=None, estrato=None, naturaleza=None, depto=None):
    where_clause, params = build_filters(anio, genero, estrato, naturaleza, depto)
    
    query = f"""
    SELECT
        LEFT(i."PERIODO"::varchar, 4) AS anio,
        i."COLE_NATURALEZA" AS tipo_colegio,
        ROUND(AVG(i."PUNT_GLOBAL")::numeric, 2) AS prom_global,
        ROUND(STDDEV(i."PUNT_GLOBAL")::numeric, 2) AS desv_std,
        COUNT(*) AS total
    FROM icfes i
    WHERE {where_clause}
    GROUP BY LEFT(i."PERIODO"::varchar, 4), i."COLE_NATURALEZA"
    ORDER BY anio, tipo_colegio
    """
    return fetch_data(query, params)

@st.cache_data(ttl=300)
def get_score_distribution_by_gender(anio=None, genero=None, estrato=None, naturaleza=None, depto=None):
    where_clause, params = build_filters(anio, genero, estrato, naturaleza, depto)
    
    results = []
    for comp, col in zip(COMPETENCIAS, COMPETENCIAS_COLS):
        query = f"""
        SELECT
            i."ESTU_GENERO" AS genero,
            '{comp}' AS competencia,
            ROUND(PERCENTILE_CONT(0.10) WITHIN GROUP (ORDER BY i."{col}")::numeric, 2) AS p10,
            ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY i."{col}")::numeric, 2) AS q1,
            ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY i."{col}")::numeric, 2) AS mediana,
            ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY i."{col}")::numeric, 2) AS q3,
            ROUND(PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY i."{col}")::numeric, 2) AS p90,
            ROUND(AVG(i."{col}")::numeric, 2) AS media,
            ROUND(STDDEV(i."{col}")::numeric, 2) AS desv_std,
            COUNT(*) AS n
        FROM icfes i
        WHERE {where_clause}
        GROUP BY i."ESTU_GENERO"
        """
        df = fetch_data(query, params)
        if not df.empty:
            results.append(df)
    
    if results:
        return pd.concat(results, ignore_index=True)
    return pd.DataFrame()

@st.cache_data(ttl=300)
def get_nse_vs_score(anio=None, genero=None, estrato=None, naturaleza=None, depto=None):
    where_parts = []
    params = []
    
    if anio:
        where_parts.append("LEFT(i.\"PERIODO\"::varchar, 4) = %s")
        params.append(anio)
    if genero:
        where_parts.append("i.\"ESTU_GENERO\" = %s")
        params.append(genero)
    if naturaleza:
        where_parts.append("i.\"COLE_NATURALEZA\" = %s")
        params.append(naturaleza)
    if depto:
        where_parts.append("i.\"COLE_DEPTO_UBICACION\" = %s")
        params.append(depto)
    
    where_parts.append("i.\"ESTU_INSE_INDIVIDUAL\" IS NOT NULL")
    where_parts.append("i.\"PUNT_GLOBAL\" BETWEEN 0 AND 500")
    
    where_clause = " AND ".join(where_parts)
    
    query = f"""
    SELECT
        ROUND(i."ESTU_INSE_INDIVIDUAL"::numeric, 1) AS nse_bucket,
        i."COLE_NATURALEZA" AS tipo_colegio,
        ROUND(AVG(i."PUNT_GLOBAL")::numeric, 2) AS prom_global,
        COUNT(*) AS n_estudiantes
    FROM icfes i
    WHERE {where_clause}
    GROUP BY ROUND(i."ESTU_INSE_INDIVIDUAL"::numeric, 1), i."COLE_NATURALEZA"
    ORDER BY nse_bucket
    """
    return fetch_data(query, tuple(params) if params else None)

@st.cache_data(ttl=300)
def get_school_ranking(anio=None, genero=None, estrato=None, naturaleza=None, depto=None):
    where_parts = []
    params = []
    
    if anio:
        where_parts.append("LEFT(i.\"PERIODO\"::varchar, 4) = %s")
        params.append(anio)
    if genero:
        where_parts.append("i.\"ESTU_GENERO\" = %s")
        params.append(genero)
    if naturaleza:
        where_parts.append("i.\"COLE_NATURALEZA\" = %s")
        params.append(naturaleza)
    if depto:
        where_parts.append("i.\"COLE_DEPTO_UBICACION\" = %s")
        params.append(depto)
    
    where_parts.append("i.\"COLE_NOMBRE_ESTABLECIMIENTO\" IS NOT NULL")
    where_parts.append("i.\"PUNT_GLOBAL\" BETWEEN 0 AND 500")
    
    where_clause = " AND ".join(where_parts)
    
    query = f"""
    SELECT
        i."COLE_NOMBRE_ESTABLECIMIENTO" AS colegio,
        i."COLE_NATURALEZA" AS tipo,
        i."COLE_DEPTO_UBICACION" AS departamento,
        ROUND(AVG(i."PUNT_GLOBAL")::numeric, 2) AS prom_global,
        ROUND(AVG(i."PUNT_MATEMATICAS")::numeric, 2) AS prom_matematicas,
        ROUND(AVG(i."PUNT_INGLES")::numeric, 2) AS prom_ingles,
        COUNT(*) AS total_alumnos
    FROM icfes i
    WHERE {where_clause}
    GROUP BY i."COLE_NOMBRE_ESTABLECIMIENTO", i."COLE_NATURALEZA", i."COLE_DEPTO_UBICACION"
    HAVING COUNT(*) >= 5
    ORDER BY prom_global DESC
    LIMIT 100
    """
    return fetch_data(query, tuple(params) if params else None)

@st.cache_data(ttl=300)
def get_departamentos():
    query = """
    SELECT DISTINCT "COLE_DEPTO_UBICACION" AS departamento
    FROM icfes
    WHERE "COLE_DEPTO_UBICACION" IS NOT NULL
    ORDER BY departamento
    """
    return fetch_data(query)