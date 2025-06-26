import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# ============================
# 🔄 Carga y preparación de datos
# ============================

# Cargar como texto para mantener ceros a la izquierda (ej: '05')
hechos_educacion = pd.read_csv("Datos/hechos_educacion.csv", dtype=str)
dim_tiempo = pd.read_csv("Datos/dim_tiempo.csv", dtype=str)
dim_municipio = pd.read_csv("Datos/dim_municipio.csv", dtype=str)
dim_departamento = pd.read_csv("Datos/dim_departamento.csv", dtype=str)

# Eliminar columna duplicada para evitar conflicto al hacer merge
if 'codigo_departamento' in dim_municipio.columns:
    dim_municipio = dim_municipio.drop(columns=['codigo_departamento'])

# Convertir año a entero (para selección y filtro)
hechos_educacion["anio"] = hechos_educacion["anio"].astype(int)
dim_tiempo["anio"] = dim_tiempo["anio"].astype(int)

# Convertir variables numéricas
for col in ["poblacion_5_16", "total_matriculados", "tasa_matriculacion_5_16", "cobertura_neta_total"]:
    hechos_educacion[col] = pd.to_numeric(hechos_educacion[col], errors='coerce')

for col in ["LATITUD", "LONGITUD"]:
    if col in dim_municipio.columns:
        dim_municipio[col] = pd.to_numeric(dim_municipio[col], errors='coerce')

# ============================
# 🔗 Unión de tablas
# ============================
df = hechos_educacion.merge(dim_tiempo, on="anio") \
                     .merge(dim_municipio, on="codigo_municipio") \
                     .merge(dim_departamento, on="codigo_departamento")

# Normalización para evitar duplicados en nombres
df['nombre_municipio'] = df['nombre_municipio'].str.strip().str.replace(',', '').str.replace('.', '').str.lower()
df['nombre_departamento'] = df['nombre_departamento'].str.strip().str.replace(',', '').str.replace('.', '').str.lower()

# Eliminar duplicados exactos de municipio con mismos datos
df = df.drop_duplicates(
    subset=['anio', 'nombre_municipio', 'tasa_matriculacion_5_16', 'cobertura_neta_total']
)

# ============================
# 🎯 Interfaz Streamlit
# ============================

st.title("📊 Dashboard Educativo - Cobertura y Matrícula")

# Selector de año
anios_disponibles = sorted(df['anio'].unique())
anio_seleccionado = st.selectbox("Selecciona un año", anios_disponibles)

# Selector de departamento
departamentos = ["Todos"] + sorted(df['nombre_departamento'].dropna().unique())
departamento_sel = st.selectbox("Filtra por departamento", departamentos)

# ============================
# 📌 Filtros aplicados
# ============================

df_filtrado = df[df['anio'] == anio_seleccionado]
if departamento_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado['nombre_departamento'] == departamento_sel]

# ============================
# 📈 Cálculo de correlación
# ============================

if len(df_filtrado) >= 2:
    correlacion = df_filtrado[['tasa_matriculacion_5_16', 'cobertura_neta_total']].corr().iloc[0,1]
    st.markdown(f"📌 **Coeficiente de correlación:** {correlacion:.2f}")
else:
    st.warning("No hay suficientes datos para calcular correlación.")

# ============================
# 📉 Gráfico de dispersión
# ============================

st.subheader("📈 Relación entre Tasa de Matrícula y Cobertura Neta")
fig = px.scatter(
    df_filtrado,
    x='tasa_matriculacion_5_16',
    y='cobertura_neta_total',
    hover_name='nombre_municipio',
    color='nombre_departamento',
    trendline="ols",
    labels={
        'tasa_matriculacion_5_16': 'Tasa de Matrícula (%)',
        'cobertura_neta_total': 'Cobertura Neta Total (%)'
    },
    title=f"Año {anio_seleccionado}: Matrícula vs. Cobertura Neta"
)
st.plotly_chart(fig, use_container_width=True)

# ============================
# 📋 Tabla detallada
# ============================

st.markdown("### 📋 Datos Detallados")
st.dataframe(df_filtrado[[ 
    'nombre_departamento', 'nombre_municipio', 
    'tasa_matriculacion_5_16', 'cobertura_neta_total' 
]].sort_values(by='cobertura_neta_total', ascending=False))

# ============================
# 🗺️ Mapa de cobertura neta
# ============================

st.subheader("🗺️ Mapa de Cobertura Neta por Municipio")

# Validar que existen columnas de latitud/longitud
if 'LATITUD' in df_filtrado.columns and 'LONGITUD' in df_filtrado.columns:
    df_map = df_filtrado[['nombre_municipio', 'cobertura_neta_total', 'LATITUD', 'LONGITUD']].dropna()
    fig_map = px.scatter_mapbox(
        df_map,
        lat="LATITUD",
        lon="LONGITUD",
        hover_name="nombre_municipio",
        hover_data={"cobertura_neta_total": True},
        size="cobertura_neta_total",
        color="cobertura_neta_total",
        color_continuous_scale="Viridis",
        zoom=5,
        height=500
    )
    fig_map.update_layout(mapbox_style="open-street-map")
    fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    st.plotly_chart(fig_map, use_container_width=True)
else:
    st.warning("No se encontraron datos geográficos para mostrar el mapa.")
