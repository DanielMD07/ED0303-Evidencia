# ED.03.03 - Evidencia de Desempeno

Tablero interactivo en Streamlit construido a partir de la API de la Practica 12
(TMDB - The Movie Database, endpoint `/discover/movie`). Toma el script de
consola de esa practica y lo transforma en un dashboard web con filtros,
indicadores y graficas que reaccionan a lo que elige quien lo usa.

## Que trae

- Filtros en la barra lateral: paginas a pedir, votos minimos, rango de fechas
  de estreno, orden de la peticion e idioma original.
- Indicadores: numero de peliculas, calificacion promedio, idiomas distintos,
  mediana de votos.
- 4 graficas: distribucion de calificaciones, comparacion por idioma,
  relacion votos-calificacion y evolucion por anio.
- Tabla de datos y boton para descargar el CSV filtrado.

## 1. Consigue tu API key (si no la tienes de la Practica 12)

1. Crea una cuenta gratis en https://www.themoviedb.org
2. Ve a tu perfil > Configuracion > API (https://www.themoviedb.org/settings/api)
3. Copia la "API Key (v3 auth)".

## 2. Ponla en el proyecto

Crea la carpeta `.streamlit` junto a este archivo y dentro un archivo
`secrets.toml` con una sola linea:

```toml
tmdb_token = "pega-aqui-tu-api-key"
```

**Nunca** subas ese archivo al repositorio (ya esta en `.gitignore`).

## 3. Corre el dashboard

```bash
pip install -r requirements.txt
streamlit run dashboard_tmdb.py
```

## 4. Publicarlo

Al desplegar en Streamlit Community Cloud, pega la misma linea
(`tmdb_token = "..."`) en la seccion de "Secrets" de la app.
