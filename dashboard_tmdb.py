# Tablero de peliculas populares - TMDB (The Movie Database)
# Herramientas de Visualizacion - ED.03.03 Evidencia de Desempeno
#
#     pip install -r requirements.txt
#     streamlit run dashboard_tmdb.py
#
# EL TOKEN NO VA EN ESTE ARCHIVO.
# En tu equipo: crea la carpeta .streamlit y dentro un archivo secrets.toml
# con una sola linea:
#     tmdb_token = "pega-aqui-tu-api-key-v3"
# Al publicar: pega esa misma linea en la seccion de secretos de la app.
# El archivo secrets.toml nunca se sube al repositorio.

import os
from datetime import date, datetime

import matplotlib.pyplot as plt
import pandas as pd
import requests
import streamlit as st

# --- Paleta del curso ------------------------------------------------------
GRIS = "#B9C3D1"
AZUL = "#1C4C9A"
ROJO = "#B2182B"
CUALI = ["#E69F00", "#56B4E9", "#009E73", "#0072B2"]

BASE_URL = "https://api.themoviedb.org/3/discover/movie"

IDIOMAS = {
    "en": "Ingles", "es": "Espanol", "ja": "Japones", "fr": "Frances",
    "ko": "Coreano", "zh": "Chino", "hi": "Hindi", "de": "Aleman",
    "it": "Italiano", "pt": "Portugues", "ru": "Ruso",
}

st.set_page_config(page_title="Tablero TMDB", layout="wide")


# --- El token ----------------------------------------------------------
def leer_token():
    try:
        if "tmdb_token" in st.secrets:
            return str(st.secrets["tmdb_token"]).strip()
    except Exception:
        pass  # todavia no existe el archivo de secretos
    if os.environ.get("TMDB_TOKEN"):
        return os.environ["TMDB_TOKEN"].strip()
    return None


TOKEN = leer_token()

if TOKEN and len(TOKEN) < 20:
    st.error(f"El token tiene {len(TOKEN)} caracteres y parece incompleto. "
             "Revisa que este completo y sin comillas.")
    st.stop()

if not TOKEN:
    st.error("Falta la API key de TMDB.")
    st.markdown(
        "1. Consiguela gratis en "
        "https://www.themoviedb.org/settings/api (API Key v3 auth)\n"
        "2. Crea la carpeta `.streamlit` junto a este archivo.\n"
        "3. Dentro, un archivo `secrets.toml` con la linea:\n"
        '   `tmdb_token = "tu-api-key"`\n'
        "4. Vuelve a cargar esta pagina."
    )
    st.stop()


# --- La consulta ------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def consultar(token, paginas, votos_minimos, inicio, fin, idiomas_api, orden):
    resultados = []
    total_reportado = None

    for pagina in range(1, paginas + 1):
        parametros = {
            "api_key": token,
            "language": "es-MX",
            "sort_by": orden,
            "vote_count.gte": votos_minimos,
            "primary_release_date.gte": str(inicio),
            "primary_release_date.lte": str(fin),
            "include_adult": "false",
            "include_video": "false",
            "page": pagina,
        }
        if idiomas_api:
            parametros["with_original_language"] = "|".join(idiomas_api)

        respuesta = requests.get(BASE_URL, params=parametros, timeout=15)

        if respuesta.status_code == 401:
            raise PermissionError("El token no fue aceptado (401). Revisa la API key.")
        if respuesta.status_code == 429:
            raise PermissionError("Demasiadas peticiones a TMDB (429). Espera un momento.")
        respuesta.raise_for_status()

        tipo = respuesta.headers.get("Content-Type") or ""
        if "json" not in tipo:
            raise ValueError(f"TMDB no devolvio JSON sino {tipo}.")

        datos_pagina = respuesta.json()
        total_reportado = datos_pagina.get("total_results")
        resultados.extend(datos_pagina.get("results", []))

        if pagina >= datos_pagina.get("total_pages", 1):
            break  # no pedir paginas que TMDB no tiene

    if not resultados:
        raise ValueError("Esa combinacion de filtros no devolvio peliculas.")

    filas = []
    for peli in resultados:
        filas.append({
            "id": peli.get("id"),
            "titulo": peli.get("title"),
            "fecha_estreno": peli.get("release_date"),
            "calificacion": peli.get("vote_average"),
            "num_votos": peli.get("vote_count"),
            "popularidad": peli.get("popularity"),
            "idioma_original": peli.get("original_language"),
        })
    df = pd.DataFrame(filas)

    for columna in ("calificacion", "num_votos", "popularidad"):
        df[columna] = pd.to_numeric(df[columna], errors="coerce")

    df["fecha_estreno"] = df["fecha_estreno"].replace("", None)
    df["fecha_estreno"] = pd.to_datetime(df["fecha_estreno"], errors="coerce")
    df = df.dropna(subset=["fecha_estreno", "calificacion"]).copy()

    df["idioma_original"] = df["idioma_original"].map(IDIOMAS).fillna(
        df["idioma_original"].str.upper())
    df["anio"] = df["fecha_estreno"].dt.year

    df = df.drop_duplicates(subset="id")
    return df, total_reportado


# --- Controles -----------------------------------------------------------
with st.sidebar:
    st.header("Que consultar")
    paginas = st.slider("Paginas a pedir (20 peliculas c/u)", 1, 20, 10)
    votos_minimos = st.slider("Votos minimos por pelicula", 0, 1000, 100, step=50)
    inicio = st.date_input("Estreno desde", date(2000, 1, 1))
    fin = st.date_input("Estreno hasta", date(2025, 12, 31))
    orden = st.selectbox(
        "Ordenar peticion por",
        ["popularity.desc", "vote_average.desc", "revenue.desc", "primary_release_date.desc"],
        help="Asi decide TMDB que paginas traer; no afecta las graficas, solo que peliculas llegan.")
    nombres_idioma = st.multiselect(
        "Idioma original (vacio = todos)",
        options=list(IDIOMAS.values()),
        help="Filtra directo en la API con with_original_language.")
    st.caption("Fuente: The Movie Database (TMDB) - /discover/movie")

codigos_idioma = [c for c, n in IDIOMAS.items() if n in nombres_idioma]

if inicio >= fin:
    st.error("La fecha de inicio debe ser anterior a la de fin.")
    st.stop()

with st.spinner("Consultando TMDB..."):
    try:
        df, total_reportado = consultar(
            TOKEN, paginas, votos_minimos, inicio, fin, tuple(codigos_idioma), orden)
    except PermissionError as e:
        st.error(str(e))
        st.stop()
    except ValueError as e:
        st.warning(str(e))
        st.stop()
    except requests.exceptions.RequestException as e:
        st.error(f"No se pudo consultar TMDB: {e}")
        st.stop()

# Idiomas con pocas peliculas distorsionan el promedio: se agrupan en "Otro"
conteo_idioma = df["idioma_original"].value_counts()
frecuentes = set(conteo_idioma[conteo_idioma >= 5].index)
df["idioma_grafica"] = df["idioma_original"].where(
    df["idioma_original"].isin(frecuentes), "Otro")


# --- Encabezado e indicadores ----------------------------------------
st.title("Tablero de peliculas populares (TMDB)")
st.caption(f"{len(df)} peliculas tras limpiar, de {total_reportado or '?'} que reporta TMDB para "
           f"el filtro · del {inicio} al {fin} · "
           f"consultado el {datetime.now():%d/%m/%Y %H:%M}")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Peliculas", len(df))
c2.metric("Calificacion promedio", f"{df['calificacion'].mean():.2f} / 10")
c3.metric("Idiomas distintos", df["idioma_original"].nunique())
c4.metric("Votos (mediana)", f"{int(df['num_votos'].median()):,}")

st.divider()


# --- Graficas --------------------------------------------------------
izquierda, derecha = st.columns(2)

with izquierda:
    st.subheader("Como se reparten las calificaciones")
    media = df["calificacion"].mean()

    fig, ax = plt.subplots(figsize=(6, 3.6))
    ax.hist(df["calificacion"], bins=20, color=GRIS, edgecolor="white")
    ax.axvline(media, color=AZUL, linewidth=2, label=f"Media: {media:.1f}")
    ax.set_xlabel("Calificacion de usuarios (0 a 10)")
    ax.set_ylabel("Numero de peliculas")
    ax.legend(frameon=False)
    st.pyplot(fig)
    st.caption("La mayoria de las peliculas populares se agrupan cerca de la media; "
               "colas largas a la izquierda suelen ser peliculas con pocos votos todavia.")

with derecha:
    st.subheader("Calificacion promedio por idioma original")
    conteo = df.groupby("idioma_grafica").size()
    promedio = (df.groupby("idioma_grafica")["calificacion"].mean()
                  .loc[conteo.index].sort_values())

    colores = [GRIS] * len(promedio)
    colores[-1] = AZUL
    etiquetas = [f"{idioma} (n={conteo[idioma]})" for idioma in promedio.index]

    fig, ax = plt.subplots(figsize=(6, 3.6))
    ax.barh(etiquetas, promedio.values, color=colores)
    ax.set_xlabel("Calificacion promedio (0 a 10)")
    st.pyplot(fig)
    st.caption(f"'{promedio.index[-1]}' tiene la mejor calificacion promedio "
               "dentro de este filtro.")

abajo_izq, abajo_der = st.columns(2)

with abajo_izq:
    st.subheader("Votos vs. calificacion")
    correlacion = df["num_votos"].corr(df["calificacion"])
    fuerza = "fuerte" if abs(correlacion) >= 0.5 else "moderada" if abs(correlacion) >= 0.3 else "debil"
    direccion = "positiva" if correlacion >= 0 else "negativa"

    fig, ax = plt.subplots(figsize=(6, 3.6))
    ax.scatter(df["num_votos"], df["calificacion"], color=GRIS, alpha=0.6,
               edgecolor=AZUL, linewidth=0.3)
    ax.set_xscale("log")
    ax.set_xlabel("Numero de votos (escala logaritmica)")
    ax.set_ylabel("Calificacion de usuarios (0 a 10)")
    st.pyplot(fig)
    st.caption(f"Relacion {fuerza} y {direccion} entre votos y calificacion (r = {correlacion:.2f}).")

with abajo_der:
    st.subheader("Calificacion promedio por anio de estreno")
    conteo_anio = df.groupby("anio").size()
    anios_confiables = conteo_anio[conteo_anio >= 3].index
    promedio_anio = (df[df["anio"].isin(anios_confiables)]
                        .groupby("anio")["calificacion"].mean().sort_index())

    fig, ax = plt.subplots(figsize=(6, 3.6))
    ax.plot(promedio_anio.index, promedio_anio.values, color=AZUL, linewidth=2,
            marker="o", markersize=3)
    ax.set_xlabel("Anio de estreno")
    ax.set_ylabel("Calificacion promedio (0 a 10)")
    st.pyplot(fig)
    if len(promedio_anio) > 0:
        anio_max = promedio_anio.idxmax()
        st.caption(f"{anio_max} es el anio con mejor calificacion promedio en este filtro "
                   "(solo anios con 3+ peliculas).")


# --- Datos -------------------------------------------------------------
with st.expander("Ver y descargar los datos"):
    st.dataframe(df.drop(columns=["idioma_grafica"]))
    st.download_button(
        "Descargar CSV",
        df.to_csv(index=False).encode("utf-8"),
        file_name=f"tmdb_{inicio}_{fin}.csv",
        mime="text/csv",
    )
