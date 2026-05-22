import streamlit as st
import pandas as pd
import os
import plotly.graph_objects as go
from groq import Groq  # Importamos el motor del Agente IA

# ==============================================================================
# 1️⃣ CONFIGURACIÓN DE LA PÁGINA Y SEGURIDAD
# ==============================================================================
st.set_page_config(
    page_title="MINSUR S.A. — Agente AI & Dashboard",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"  # Obliga a mostrar el chat del agente
)

CLAVE_DE_ACCESO = "david2531"
RUTA_EXCEL = "empresa_MINSUR.xlsx"

# 🔑 CONEXIÓN SEGURA A LA API KEY DESDE LOS SECRETS DE STREAMLIT
if "GROQ_API_KEY" in st.secrets:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
else:
    # Opción de respaldo por si no se configura en la nube
    GROQ_API_KEY = "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"

# Inicializar estados de sesión
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
if "historial_chat" not in st.session_state:
    st.session_state["historial_chat"] = []

# Pantalla de Bloqueo
if not st.session_state["autenticado"]:
    st.markdown("<h2 style='text-align: center; color: #0f172a;'>🔒 SISTEMA PRIVADO - MINSUR S.A.</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748b;'>Este canal de auditoría financiera contiene un Agente IA con acceso restringido.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        clave_ingresada = st.text_input("🔑 Ingrese el Código de Acceso Oficial:", type="password")
        if st.button("Desbloquear Sistema", use_container_width=True):
            if clave_ingresada == CLAVE_DE_ACCESO:
                st.session_state["autenticado"] = True
                st.rerun()
            else:
                st.error("❌ Código incorrecto. Acceso denegado.")
    st.stop()

# ==============================================================================
# 2️⃣ PROCESAMIENTO DE DATOS FINANCIEROS
# ==============================================================================
def limpiar_hoja_excel(df):
    df = df.dropna(how='all', axis=1)
    fila_cabecera = None
    for i in range(min(5, len(df))):
        valores_fila = [str(val).strip().lower() for val in df.iloc[i].values]
        if 'año' in valores_fila:
            fila_cabecera = i
            break
    if fila_cabecera is not None:
        df.columns = [str(c).strip() for c in df.iloc[fila_cabecera].values]
        df = df.iloc[fila_cabecera + 1:].copy()
    else:
        df.columns = [str(c).strip() for c in df.columns]
    df = df.loc[:, ~df.columns.str.contains('^Unnamed|^nan$', case=False, na=True)]
    for col in df.columns:
        if col.lower() == 'año':
            df.rename(columns={col: 'Año'}, inplace=True)
            break
    return df

@st.cache_data
def cargar_y_procesar_datos():
    if not os.path.exists(RUTA_EXCEL):
        return None
    try:
        df_balance = limpiar_hoja_excel(pd.read_excel(RUTA_EXCEL, sheet_name='Balance', engine='openpyxl'))
        df_resultados = limpiar_hoja_excel(pd.read_excel(RUTA_EXCEL, sheet_name='Resultados', engine='openpyxl'))
        
        df_balance['Año'] = pd.to_numeric(df_balance['Año'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip(), errors='coerce')
        df_resultados['Año'] = pd.to_numeric(df_resultados['Año'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip(), errors='coerce')
        
        df_balance = df_balance.dropna(subset=['Año']).copy()
        df_resultados = df_resultados.dropna(subset=['Año']).copy()
        df_balance['Año'] = df_balance['Año'].astype(int)
        df_resultados['Año'] = df_resultados['Año'].astype(int)
        
        df_merged = pd.merge(df_balance, df_resultados, on='Año')
        
        columnas_financieras = ['Activo Corriente', 'Pasivo Corriente', 'Activo Total', 'Pasivo Total', 'Patrimonio', 'Utilidad Neta']
        for col in columnas_financieras:
            if col in df_merged.columns:
                df_merged[col] = pd.to_numeric(df_merged[col].astype(str).str.replace(',', '', regex=False).str.strip(), errors='coerce')
        
        df_merged.dropna(subset=columnas_financieras, inplace=True)
        df_merged['Liquidez'] = (df_merged['Activo Corriente'] / df_merged['Pasivo Corriente']).round(2)
        df_merged['Endeudamiento'] = ((df_merged['Pasivo Total'] / df_merged['Activo Total']) * 100).round(2)
        df_merged['ROA'] = ((df_merged['Utilidad Neta'] / df_merged['Activo Total']) * 100).round(2)
        df_merged['ROE'] = ((df_merged['Utilidad Neta'] / df_merged['Patrimonio']) * 100).round(2)
        
        return df_merged.sort_values(by='Año').reset_index(drop=True)
    except Exception as e:
        return None

df = cargar_y_procesar_datos()

if df is None or df.empty:
    st.warning("⚠️ No se encontró el archivo 'empresa_MINSUR.xlsx' en el repositorio.")
    st.stop()

# ==============================================================================
# 3️⃣ BARRA LATERAL: INTERFAZ DEL AGENTE IA DE AUDITORÍA
# ==============================================================================
st.sidebar.markdown("## 🤖 Agente IA Financiero Minsur")
st.sidebar.markdown("Hazle preguntas libres al analista virtual sobre los balances e historial de la empresa:")

# Mostrar historial de chat en la barra lateral
for mensaje in st.session_state["historial_chat"]:
    with st.sidebar.chat_message(mensaje["role"]):
        st.write(mensaje["content"])

# Entrada de texto del usuario en el chat lateral
if pregunta_usuario := st.sidebar.chat_input("Escribe tu consulta contable aquí..."):
    with st.sidebar.chat_message("user"):
        st.write(pregunta_usuario)
    st.session_state["historial_chat"].append({"role": "user", "content": pregunta_usuario})
    
    # Preparar los datos tabulares para que la IA los pueda "leer" perfectamente
    datos_contexto = df[['Año', 'Liquidez', 'Endeudamiento', 'ROA', 'ROE']].to_string(index=False)
    
    # Prompt del sistema para darle personalidad experta al Agente
    instrucciones_agente = (
        "Eres un Agente Consultor Financiero Senior y Auditor de Inteligencia Artificial para la minera MINSUR S.A. "
        "Tienes acceso exclusivo a la siguiente tabla de ratios financieros clave calculados directamente "
        "desde los libros oficiales de Balance y Resultados:\n\n"
        f"{datos_contexto}\n\n"
        "Tu misión es responder las preguntas del usuario de forma analítica, precisa, usando terminología contable correcta "
        "y basándote estrictamente en los datos provistos. Si te piden opiniones o proyecciones, fundamenta tus respuestas "
        "en las tendencias de las métricas (Liquidez, Endeudamiento, ROA, ROE). Sé conciso pero sumamente profesional."
    )
    
    try:
        # Llamada al cerebro de Groq usando la llave segura
        client = Groq(api_key=GROQ_API_KEY)
        respuesta_ia = client.chat.completions.create(
            model="llama-3.1-8b-instant",  # El nuevo motor ultra rápido
            messages=[
                {"role": "system", "content": instrucciones_agente},
                *st.session_state["historial_chat"]
            ],
            temperature=0.3
        )
        
        respuesta_texto = respuesta_ia.choices[0].message.content
        
        with st.sidebar.chat_message("assistant"):
            st.write(respuesta_texto)
        st.session_state["historial_chat"].append({"role": "assistant", "content": respuesta_texto})
        st.rerun()
        
    except Exception as e:
        st.sidebar.error("Error del Agente IA: Verifica la conexión.")

# ==============================================================================
# 4️⃣ CUERPO PRINCIPAL: INTERFAZ GRÁFICA VISUAL (DASHBOARD)
# ==============================================================================
ultimo_registro = df.iloc[-1]
anios_disponibles = sorted(df['Año'].unique().tolist(), reverse=True)

st.markdown(f"""
    <div style='background-color: #0f172a; padding: 16px; border-radius: 12px; margin-bottom: 24px; display: flex; justify-content: space-between; align-items: center;'>
        <h1 style='color: white; margin: 0; font-size: 24px;'>MINSUR S.A. — Cuadro de Mando con Agente IA</h1>
        <span style='background: #38bdf8; color: #0f172a; padding: 6px 12px; border-radius: 20px; font-weight: bold; font-size: 13px;'>Estatus del Sistema: En Línea</span>
    </div>
""", unsafe_allow_html=True)

col_sel1, col_sel2 = st.columns([1, 3])
with col_sel1:
    anio_seleccionado = st.selectbox("📅 Historial Fiscal Año:", anios_disponibles)

datos_anio = df[df['Año'] == anio_seleccionado].iloc[0]

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Liquidez Corriente", f"{datos_anio['Liquidez']} x")
kpi2.metric("Endeudamiento Global", f"{datos_anio['Endeudamiento']} %")
kpi3.metric("Rentabilidad ROA", f"{datos_anio['ROA']} %")
kpi4.metric("Rentabilidad ROE", f"{datos_anio['ROE']} %")

st.markdown("---")

g1, g2 = st.columns(2)

def crear_grafico_linea(x, y, titulo, color):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y, mode='lines+markers', name=titulo, line=dict(color=color, width=3)))
    fig.update_layout(title=titulo, margin=dict(l=20, r=20, t=40, b=20), height=250, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    return fig

with g1:
    st.plotly_chart(crear_grafico_linea(df['Año'], df['Liquidez'], "Evolución de Liquidez Corriente (Veces)", "#2563eb"), use_container_width=True)
    st.plotly_chart(crear_grafico_linea(df['Año'], df['ROA'], "Retorno sobre Activos - ROA (%)", "#16a34a"), use_container_width=True)

with g2:
    st.plotly_chart(crear_grafico_linea(df['Año'], df['Endeudamiento'], "Ratio de Endeudamiento Global (%)", "#dc2626"), use_container_width=True)
    st.plotly_chart(crear_grafico_linea(df['Año'], df['ROE'], "Retorno sobre Patrimonio - ROE (%)", "#ea580c"), use_container_width=True)

st.markdown("---")
st.markdown("### 📋 Historial de Datos Consolidados")
st.dataframe(df[['Año', 'Liquidez', 'Endeudamiento', 'ROA', 'ROE']], use_container_width=True)
