# ===========================
# Casita de Semillas MAU - Explorador Pro (con Imgur persistente)
# ===========================

import streamlit as st
import pandas as pd
import gspread
import requests
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import io
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# ===========================
# CONFIGURACIÓN GENERAL
# ===========================
st.set_page_config(page_title="Casita de Semillas MAU", layout="wide")

st.image("images/logo_verde.png", width=200)
st.title("🌱 Casita de Semillas - Movimiento Agroecología Urbana (MAU)")

# ===========================
# CONFIGURACIÓN DE CREDENCIALES
# ===========================

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]
creds_dict = st.secrets["gsheets"]
credentials = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)
client = gspread.authorize(credentials)
service = build('drive', 'v3', credentials=credentials)

# ===========================
# FUNCIONES DE UTILIDAD
# ===========================

IMGUR_CLIENT_ID = "24a1ff147dc7ce1"

sheet_formulario = client.open("Registro de Movimientos de Semillas (Respuestas)").worksheet("Respuestas de formulario 1")
data_formulario = sheet_formulario.get_all_records()
df_mov = pd.DataFrame(data_formulario)

# Asegurar que exista columna 'link_imgur'
if 'link_imgur' not in df_mov.columns:
    df_mov['link_imgur'] = ""
    current_cols = len(sheet_formulario.row_values(1))
    sheet_formulario.add_cols(1)
    sheet_formulario.update_cell(1, current_cols + 1, 'link_imgur')

sheet_fitodiversidad = client.open("Registro de Movimientos de Semillas (Respuestas)").worksheet("BBDD Fitodiversidad")
df_fit = pd.DataFrame(sheet_fitodiversidad.get_all_records())

# ===========================
# FUNCIONES IMAGEN
# ===========================
def download_drive_image(file_id):
    try:
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        fh.seek(0)
        return fh
    except Exception as e:
        return None

def upload_to_imgur(image_bytes):
    try:
        url = "https://api.imgur.com/3/image"
        headers = {"Authorization": f"Client-ID {IMGUR_CLIENT_ID}"}
        files = {"image": image_bytes.getvalue()}
        response = requests.post(url, headers=headers, files=files)
        if response.status_code == 200:
            return response.json()["data"]["link"]
        else:
            return None
    except:
        return None

def extraer_file_id(url):
    if pd.isna(url) or not isinstance(url, str):
        return None
    url = url.strip()
    if "open?id=" in url:
        return url.split("open?id=")[-1]
    elif "/file/d/" in url:
        return url.split("/file/d/")[-1].split("/")[0]
    return None

# ===========================
# FUSIÓN DE BASES
# ===========================
clave = "Nombre científico (opcional)"
df_mov[clave] = df_mov[clave].str.strip().str.lower()
df_fit[clave] = df_fit[clave].str.strip().str.lower()
df = pd.merge(df_mov, df_fit, on=clave, how='left')
df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('¿', '').str.replace('?', '')
df["marca_temporal"] = pd.to_datetime(df["marca_temporal"], errors='coerce')

# Nombre común + vulgar unificado
n1 = df["nombre_común_de_la_semilla"].fillna("").str.strip().str.lower()
n2 = df["nombre_vulgar"].fillna("").str.strip().str.lower()
df["nombre_semilla_unificado"] = [a.title() if a == b or not b else f"{a.title()}; {b.title()}" for a, b in zip(n1, n2)]

# ===========================
# SIDEBAR - FILTROS
# ===========================
st.sidebar.header("🔎 Filtros")
filtros = {}
filtros['casita'] = st.sidebar.multiselect("Casita", sorted(df['identificación_de_la_casita_de_semillas'].dropna().unique()))
filtros['familia'] = st.sidebar.multiselect("Familia", sorted(df['familia'].dropna().unique()))
filtros['categoria'] = st.sidebar.multiselect("Categoría", sorted(df['categoria'].dropna().unique()))
filtros['nombre_cientifico'] = st.sidebar.text_input("Nombre científico")
filtros['mes_siembra'] = st.sidebar.multiselect("Meses de siembra", ['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre'])

df_filtrado = df.copy()
if filtros['casita']:
    df_filtrado = df_filtrado[df_filtrado['identificación_de_la_casita_de_semillas'].isin(filtros['casita'])]
if filtros['familia']:
    df_filtrado = df_filtrado[df_filtrado['familia'].isin(filtros['familia'])]
if filtros['categoria']:
    df_filtrado = df_filtrado[df_filtrado['categoria'].isin(filtros['categoria'])]
if filtros['nombre_cientifico'].strip():
    df_filtrado = df_filtrado[df_filtrado['nombre_científico_(opcional)'].str.contains(filtros['nombre_cientifico'], case=False, na=False)]
if filtros['mes_siembra']:
    df_filtrado = df_filtrado[df_filtrado[filtros['mes_siembra']].sum(axis=1) > 0]

# ===========================
# MÉTRICAS Y GRÁFICO
# ===========================

st.markdown("## 📊 Totales")
col1, col2, col3 = st.columns(3)
with col1: st.metric("Total registros", len(df_filtrado))
with col2: st.metric("Familias únicas", df_filtrado['familia'].nunique())
with col3: st.metric("Especies únicas", df_filtrado['nombre_científico_(opcional)'].nunique())

st.markdown("### 📊 Familias más comunes")
st.bar_chart(df_filtrado['familia'].value_counts().head(15))

# ===========================
# FICHA DETALLADA
# ===========================

st.sidebar.header("🌿 Ver semilla")
seleccion = st.sidebar.selectbox("Nombre común:", sorted(df_filtrado['nombre_semilla_unificado'].dropna().unique()))
if seleccion:
    semilla = df_filtrado[df_filtrado['nombre_semilla_unificado'] == seleccion].iloc[0]
    st.markdown(f"## 🌱 {semilla['nombre_semilla_unificado']} ({semilla['nombre_científico_(opcional)']})")

    st.write(f"**Casita:** {semilla['identificación_de_la_casita_de_semillas']}")
    st.write(f"**Responsable:** {semilla['nombre_de_la_persona_que_entrega_o_recibe_las_semillas']}")
    st.write(f"**Fecha:** {semilla['marca_temporal'].date() if pd.notnull(semilla['marca_temporal']) else '-'}")

    st.markdown("### 📸 Imagen")
    if 'link_imgur' in semilla and semilla['link_imgur'].startswith("http"):
        st.image(semilla['link_imgur'], width=300)
    else:
        file_id = extraer_file_id(semilla.get("suba_una_fotografía_de_la_semilla", ""))
        if file_id:
            imagen_bytes = download_drive_image(file_id)
            if imagen_bytes:
                link_imgur = upload_to_imgur(imagen_bytes)
                if link_imgur:
                    st.image(link_imgur, width=300)
                    # Guardar nuevo link en hoja
                    actualizaciones = []
try:
    fila = next(i for i, row in enumerate(data_formulario) if str(row['Marca temporal']).strip() == semilla['marca_temporal'].strftime('%Y-%m-%d %H:%M:%S')) + 2
    col = len(sheet_formulario.row_values(1))
    actualizaciones.append({
        'range': f"Respuestas de formulario 1!{chr(64+col)}{fila}",
        'values': [[link_imgur]]
    })
except Exception as e:
    st.error(f"Error preparando actualización Imgur: {e}")

if 'link_imgur' in semilla and semilla['link_imgur'].startswith("http"):
    st.image(semilla['link_imgur'], width=300)
else:
    file_id = extraer_file_id(semilla.get("suba_una_fotografía_de_la_semilla", ""))
    if file_id:
        imagen_bytes = download_drive_image(file_id)
        if imagen_bytes:
            link_imgur = upload_to_imgur(imagen_bytes)
            if link_imgur:
                st.image(link_imgur, width=300)

                # Guardar el link nuevo
                try:
                    fila = next(i for i, row in enumerate(data_formulario) if str(row['Marca temporal']).strip() == semilla['marca_temporal'].strftime('%Y-%m-%d %H:%M:%S')) + 2
                    col = len(sheet_formulario.row_values(1))
                    sheet_formulario.batch_update({
                        "valueInputOption": "RAW",
                        "data": [{
                            'range': f"Respuestas de formulario 1!{chr(64+col)}{fila}",
                            'values': [[link_imgur]]
                        }]
                    })
                except Exception as e:
                    st.error(f"Error preparando actualización Imgur: {e}")

            else:
                st.image("images/logo_verde.png", width=300)
        else:
            st.image("images/logo_verde.png", width=300)
    else:
        st.image("images/logo_verde.png", width=300)
# ===========================
# TABLA Y DESCARGA
# ===========================

st.markdown("### 📋 Resultados")
st.dataframe(df_filtrado)
csv = df_filtrado.to_csv(index=False).encode("utf-8")
st.download_button("📥 Descargar CSV", csv, "semillas_filtradas.csv", "text/csv")
