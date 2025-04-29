import streamlit as st
import pandas as pd
import io

# =====================
# CONFIGURACIÓN DE LA PÁGINA
# =====================
st.set_page_config(
    page_title="Casita de Semillas MAU",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🌱 Casita de Semillas MAU")
st.markdown("""
Bienvenida/o al visualizador de movimientos de semillas del Movimiento de Agroecología Urbana (MAU).
Sube tu archivo de registro para comenzar a explorar los datos.
""")

# =====================
# CARGAR ARCHIVO
# =====================
uploaded_file = st.file_uploader("Sube el archivo de registro (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
        st.success("¡Archivo cargado exitosamente!")

        # =====================
        # FILTROS
        # =====================
        st.sidebar.header("🔎 Filtros")

        columnas_filtrar = st.sidebar.multiselect("Selecciona columnas para filtrar:", df.columns)

        df_filtrado = df.copy()

        for columna in columnas_filtrar:
            opciones = df_filtrado[columna].dropna().unique()
            seleccion = st.sidebar.multiselect(f"Filtrar por {columna}:", opciones)
            if seleccion:
                df_filtrado = df_filtrado[df_filtrado[columna].isin(seleccion)]

        # =====================
        # VISTA PREVIA
        # =====================
        st.subheader("📋 Vista previa de los datos")
        st.dataframe(df_filtrado)

        # =====================
        # DESCARGAR ARCHIVO FILTRADO
        # =====================
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_filtrado.to_excel(writer, index=False, sheet_name='Movimientos')

        st.download_button(
            label="💾 Descargar datos filtrados en Excel",
            data=output.getvalue(),
            file_name='Movimientos_filtrados.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")

else:
    st.info("Por favor, sube un archivo para comenzar.")
