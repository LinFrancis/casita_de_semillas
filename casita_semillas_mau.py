import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st
import pandas as pd

# =========================
# CONNECT TO GOOGLE SHEET
# =========================
def connect_to_gsheet(spreadsheet_name, sheet_name):
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive"
    ]

    creds_dict = st.secrets["gsheets"]
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)
    client = gspread.authorize(credentials)
    spreadsheet = client.open(spreadsheet_name)
    return spreadsheet.worksheet(sheet_name)

# Nombres
SPREADSHEET_NAME = 'Registro de Movimientos de Semillas (Respuestas)'

# Cargar hoja de Movimientos de Semillas
sheet_movimientos = connect_to_gsheet(SPREADSHEET_NAME, 'Respuestas de formulario 1')
df_movimientos = pd.DataFrame(sheet_movimientos.get_all_records())

# Cargar hoja de BBDD Fitodiversidad
sheet_fitodiversidad = connect_to_gsheet(SPREADSHEET_NAME, 'BBDD Fitodiversidad')
df_fitodiversidad = pd.DataFrame(sheet_fitodiversidad.get_all_records())

# Mostrar ambos DataFrames en Streamlit
st.title("🌱 Casita de Semillas MAU - Visualizador de Datos")

st.subheader("📋 Registro de Movimientos de Semillas")
st.dataframe(df_movimientos)

st.subheader("🌿 Base de Datos de Fitodiversidad")
st.dataframe(df_fitodiversidad)
