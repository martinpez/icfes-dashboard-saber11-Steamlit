import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from db import (
    COLORS, CHOROPLETH_SCALE,
    get_score_by_department, get_heatmap_estrato_competencia,
    get_timeseries_by_school_type, get_score_distribution_by_gender,
    get_nse_vs_score, get_school_ranking, get_departamentos
)

@st.cache_data
def load_geojson():
    with open("colombia.geo.json", "r", encoding="utf-8") as f:
        return json.load(f)

geojson = load_geojson()

def normalize_department_name(name):
    if not name:
        return name
    name = name.upper().strip()
    mapping = {
        "SANTAFE DE BOGOTA D.C": "BOGOTA",
        "BOGOTA D.C.": "BOGOTA",
        "BOGOTA": "BOGOTA",
    }
    return mapping.get(name, name)

st.set_page_config(
    page_title="ICFES Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        font-size: 28px;
        font-weight: 600;
        color: #003857;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">ICFES Dashboard - Resultados Saber 11</div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("Filtros")
    
    anio = st.selectbox(
        "Año",
        options=[None, "2018", "2019", "2020", "2021"],
        format_func=lambda x: "Todos los años" if x is None else x,
        index=0
    )
    
    genero = st.selectbox(
        "Género",
        options=[None, "M", "F"],
        format_func=lambda x: "Todos" if x is None else ("Masculino" if x == "M" else "Femenino"),
        index=0
    )
    
    estrato = st.selectbox(
        "Estrato Socioeconómico",
        options=[None, "Estrato 1", "Estrato 2", "Estrato 3", "Estrato 4", "Estrato 5", "Estrato 6"],
        format_func=lambda x: "Todos" if x is None else x,
        index=0
    )
    
    naturaleza = st.selectbox(
        "Tipo de Colegio",
        options=[None, "OFICIAL", "NO OFICIAL"],
        format_func=lambda x: "Todos" if x is None else x,
        index=0
    )
    
    deptos_df = get_departamentos()
    deptos_list = [None] + sorted(deptos_df['departamento'].dropna().tolist())
    depto = st.selectbox(
        "Departamento",
        options=deptos_list,
        format_func=lambda x: "Todos" if x is None else x,
        index=0
    )

st.markdown("### 1. ¿Dónde aprende mejor Colombia?")
st.markdown("**Puntaje global promedio Saber 11 por departamento.**")
df_dept = get_score_by_department(anio, genero, estrato, naturaleza, depto)

if not df_dept.empty:
    df_dept_filtered = df_dept
    if anio:
        df_dept_filtered = df_dept[df_dept['anio'] == anio]
    
    df_dept_agg = df_dept_filtered.groupby('departamento').agg({
        'prom_global': 'mean',
        'total_estudiantes': 'sum'
    }).reset_index()
    
    geojson_names = set()
    for f in geojson['features']:
        geojson_names.add(f['properties']['NOMBRE_DPT'])
    
    df_dept_agg['departamento_norm'] = df_dept_agg['departamento'].apply(
        lambda x: normalize_department_name(x) if normalize_department_name(x) in geojson_names else None
    )
    df_dept_agg = df_dept_agg[df_dept_agg['departamento_norm'].notna()]
    
    if not df_dept_agg.empty:
        valores = df_dept_agg['prom_global']
        min_val = valores.min()
        max_val = valores.max()
        
        fig_map = px.choropleth_mapbox(
            df_dept_agg,
            geojson=geojson,
            locations='departamento_norm',
            featureidkey='properties.NOMBRE_DPT',
            color='prom_global',
            color_continuous_scale=CHOROPLETH_SCALE,
            range_color=[min_val, max_val],
            hover_name='departamento',
            hover_data={'prom_global': ':.2f', 'total_estudiantes': True},
            mapbox_style="carto-positron",
            zoom=4,
            center={"lat": 4.570868, "lon": -74.297333},
            opacity=0.7
        )
        fig_map.update_layout(
            title="",
            font=dict(family="Inter", size=11),
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            height=500,
            paper_bgcolor='#ffffff'
        )
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.warning("No hay datos disponibles para el mapa")
else:
    st.warning("No hay datos disponibles")

st.markdown("---")

st.markdown("### 2. La Desigualdad Competencia a Competencia")
st.markdown("**¿Qué tanto separa el estrato el rendimiento de cada prueba?**")
df_heat = get_heatmap_estrato_competencia(anio, genero, estrato, naturaleza, depto)

if not df_heat.empty:
    estratos_order = ['Estrato 1', 'Estrato 2', 'Estrato 3', 'Estrato 4', 'Estrato 5', 'Estrato 6']
    df_heat['estrato'] = pd.Categorical(df_heat['estrato'], categories=estratos_order, ordered=True)
    df_heat = df_heat.sort_values('estrato')
    
    heat_data = df_heat.set_index('estrato')[['prom_lectura', 'prom_matematicas', 'prom_naturales', 'prom_sociales', 'prom_ingles']]
    heat_data.columns = ['Lectura Crítica', 'Matemáticas', 'C. Naturales', 'Sociales', 'Inglés']
    
    fig_heat = go.Figure(data=go.Heatmap(
        z=heat_data.values,
        x=heat_data.columns,
        y=heat_data.index,
        colorscale='RdYlGn',
        text=heat_data.values,
        texttemplate='%{z:.1f}',
        textfont={"size": 12},
        showscale=True
    ))
    fig_heat.update_layout(
        xaxis_title="Competencia",
        yaxis_title="Estrato Socioeconómico",
        plot_bgcolor='#ffffff',
        paper_bgcolor='#ffffff',
        font=dict(family="Inter", size=11)
    )
    st.plotly_chart(fig_heat, use_container_width=True)
else:
    st.warning("No hay datos disponibles")

st.markdown("---")

st.markdown("### 3. La Brecha que No Cierra: Oficial vs. No Oficial")
st.markdown("**Trayectoria del puntaje promedio de colegios oficiales y no oficiales.**")
df_ts = get_timeseries_by_school_type(anio, genero, estrato, naturaleza, depto)

if not df_ts.empty:
    fig_ts = go.Figure()
    
    for tipo, color in [('OFICIAL', COLORS['oficial']), ('NO OFICIAL', COLORS['nooficial'])]:
        df_tipo = df_ts[df_ts['tipo_colegio'] == tipo]
        fig_ts.add_trace(go.Scatter(
            x=df_tipo['anio'],
            y=df_tipo['prom_global'],
            name=tipo,
            mode='lines+markers',
            line=dict(color=color, width=3),
            marker=dict(size=10),
            error_y=dict(type='data', array=df_tipo['desv_std'], visible=True),
            hovertemplate=f"{tipo}<br>Año: %{{x}}<br>Puntaje: %{{y:.2f}}<extra></extra>"
        ))
    
    fig_ts.update_layout(
        shapes=[dict(
            type="line", x0="2020", x1="2020", y0=0, y1=1,
            xref="x", yref="paper",
            line=dict(color=COLORS['warning'], width=1, dash="dash")
        )],
        annotations=[dict(
            x="2020", y=1, xref="x", yref="paper",
            text="COVID-19", showarrow=False,
            font=dict(color=COLORS['warning'])
        )],
        xaxis_title="Año",
        yaxis_title="Puntaje Global Promedio",
        plot_bgcolor='#ffffff',
        paper_bgcolor='#ffffff',
        font=dict(family="Inter", size=11),
        legend=dict(title="Tipo de Colegio")
    )
    st.plotly_chart(fig_ts, use_container_width=True)
else:
    st.warning("No hay datos disponibles")

st.markdown("---")

st.markdown("### 4. ¿Quién Puntúa Más?")
st.markdown("**Distribución por género en cada competencia.**")
df_box = get_score_distribution_by_gender(anio, genero, estrato, naturaleza, depto)

if not df_box.empty:
    df_box['genero_label'] = df_box['genero'].map({'M': 'Masculino', 'F': 'Femenino'})
    
    competencias_order = ['Matemáticas', 'Lectura Crítica', 'Ciencias Naturales', 'Sociales y Ciudadanas', 'Inglés']
    df_box['competencia'] = pd.Categorical(df_box['competencia'], categories=competencias_order, ordered=True)
    df_box = df_box.sort_values(['competencia', 'genero'])
    
    fig_box = go.Figure()
    
    for genero in ['Masculino', 'Femenino']:
        df_gen = df_box[df_box['genero_label'] == genero]
        fig_box.add_trace(go.Bar(
            x=df_gen['competencia'],
            y=df_gen['mediana'],
            name=genero,
            error_y=dict(
                type='data',
                array=df_gen['q3'] - df_gen['mediana'],
                arrayminus=df_gen['mediana'] - df_gen['q1'],
                visible=True
            ),
            marker_color=COLORS['male'] if genero == 'Masculino' else COLORS['female']
        ))
    
    fig_box.update_layout(
        xaxis_title="Competencia",
        yaxis_title="Mediana del Puntaje",
        plot_bgcolor='#ffffff',
        paper_bgcolor='#ffffff',
        font=dict(family="Inter", size=11),
        legend_title="Género",
        barmode='group'
    )
    st.plotly_chart(fig_box, use_container_width=True)
else:
    st.warning("No hay datos disponibles")

st.markdown("---")

st.markdown("### 5. Capital Social vs. Académico")
st.markdown("**Correlación entre NSE y puntaje global por tipo de colegio.**")
df_nse = get_nse_vs_score(anio, genero, estrato, naturaleza, depto)

st.write("DEBUG df_nse filtros:", {"anio": anio, "genero": genero, "estrato": estrato, "naturaleza": naturaleza, "depto": depto})
st.write("DEBUG df_nse resultado:", df_nse is not None, "len:", len(df_nse) if df_nse is not None else "None")
st.write("DEBUG df_nse columnas:", df_nse.columns.tolist() if df_nse is not None else "None")

if df_nse is not None and len(df_nse) > 0:
    fig_scatter = go.Figure()
    
    for tipo, color in [('OFICIAL', COLORS['oficial']), ('NO OFICIAL', COLORS['nooficial'])]:
        df_tipo = df_nse[df_nse['tipo_colegio'] == tipo]
        sizes = df_tipo['n_estudiantes'] / df_tipo['n_estudiantes'].max() * 40 + 10
        
        fig_scatter.add_trace(go.Scatter(
            x=df_tipo['nse_bucket'],
            y=df_tipo['prom_global'],
            mode='markers',
            name=tipo,
            marker=dict(size=sizes, color=color, opacity=0.7, line=dict(width=1, color='#ffffff')),
            text=df_tipo.apply(lambda r: f"NSE: {r['nse_bucket']}<br>Puntaje: {r['prom_global']}<br>Estudiantes: {r['n_estudiantes']}", axis=1),
            hovertemplate="%{text}<extra></extra>"
        ))
        
        if len(df_tipo) > 1:
            z = df_tipo.sort_values('nse_bucket')
            fig_scatter.add_trace(go.Scatter(
                x=z['nse_bucket'], y=z['prom_global'],
                mode='lines', line=dict(color=color, dash='dash'),
                showlegend=False, hoverinfo='skip'
            ))
    
    fig_scatter.update_layout(
        xaxis_title="Índice de Nivel Socioeconómico (NSE)",
        yaxis_title="Puntaje Global Promedio",
        plot_bgcolor='#ffffff',
        paper_bgcolor='#ffffff',
        font=dict(family="Inter", size=11)
    )
    st.plotly_chart(fig_scatter, use_container_width=True)
else:
    st.warning("No hay datos disponibles")

st.markdown("---")

st.markdown("### 6. Top 20 Colegios")
st.markdown("**Establecimientos con mayor puntaje global.**")
df_rank = get_school_ranking(anio, genero, estrato, naturaleza, depto)

st.write("DEBUG df_rank filtros:", {"anio": anio, "genero": genero, "estrato": estrato, "naturaleza": naturaleza, "depto": depto})
st.write("DEBUG df_rank resultado:", df_rank is not None, "len:", len(df_rank) if df_rank is not None else "None")
st.write("DEBUG df_rank columnas:", df_rank.columns.tolist() if df_rank is not None else "None")

if df_rank is not None and len(df_rank) > 0:
    df_rank = df_rank.head(20)
    
    fig_rank = go.Figure(go.Bar(
        y=df_rank['colegio'].str[:40],
        x=df_rank['prom_global'],
        orientation='h',
        marker_color=[COLORS['oficial'] if t == 'OFICIAL' else COLORS['nooficial'] for t in df_rank['tipo']],
        text=df_rank['prom_global'],
        textposition='outside',
        hovertemplate="<b>%{y}</b><br>Puntaje: %{x}<br>Tipo: %{customdata}<extra></extra>",
        customdata=df_rank[['tipo', 'departamento']].values
    ))
    fig_rank.update_layout(
        xaxis_title="Puntaje Global Promedio",
        yaxis_title="",
        plot_bgcolor='#ffffff',
        paper_bgcolor='#ffffff',
        font=dict(family="Inter", size=10),
        height=600,
        margin=dict(l=250)
    )
    fig_rank.update_traces(texttemplate='%{x:.1f}', textposition='outside')
    st.plotly_chart(fig_rank, use_container_width=True)
else:
    st.warning("No hay datos disponibles")

st.markdown("---")
st.caption("Datos: ICFES Colombia - Pruebas Saber 11 (2018-2021)")