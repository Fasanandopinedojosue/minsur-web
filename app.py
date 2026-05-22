import streamlit as st
import pandas as pd
import os
import plotly.graph_objects as go

# ==============================================================================
# 1️⃣ CONFIGURACIÓN DE LA PÁGINA Y SEGURIDAD
# ==============================================================================
st.set_page_config(
    page_title="MINSUR S.A. — Cuadro de Mando Integral",
    page_icon="💼",
    layout="wide"
)

CLAVE_DE_ACCESO = "david2531"
RUTA_EXCEL = "empresa_MINSUR.xlsx"  # En la web estará en la misma carpeta

# Inicializar el estado de autenticación en la sesión del navegador
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

# Pantalla de Bloqueo si no se ha puesto la clave
if not st.session_state["autenticado"]:
    st.markdown("<h2 style='text-align: center; color: #0f172a;'>🔒 SISTEMA PRIVADO - MINSUR S.A.</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748b;'>Este canal de auditoría financiera contiene información corporativa restringida.</p>", unsafe_allow_html=True)
    
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
# 2️⃣ PROCESAMIENTO DE DATOS FINANCIEROS (REUTILIZADO)
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
        df_balance = limpiar_hoja_excel(pd.read_excel(RUTA_EXCEL, sheet_name='Balance'))
        df_resultados = limpiar_hoja_excel(pd.read_excel(RUTA_EXCEL, sheet_name='Resultados'))
        
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
        st.error(f"Error al procesar el archivo Excel: {e}")
        return None

df = cargar_y_procesar_datos()

if df is None or df.empty:
    st.warning("⚠️ No se encontró el archivo 'empresa_MINSUR.xlsx' o está vacío en el directorio.")
    st.stop()

# ==============================================================================
# 3️⃣ ENTORNO GRÁFICO Y MOTORES DE DIAGNÓSTICO
# ==============================================================================
ultimo_registro = df.iloc[-1]
anios_disponibles = sorted(df['Año'].unique().tolist(), reverse=True)

# Barra lateral superior
st.markdown(f"""
    <div style='background-color: #0f172a; padding: 16px; border-radius: 12px; margin-bottom: 24px; display: flex; justify-content: space-between; align-items: center;'>
        <h1 style='color: white; margin: 0; font-size: 24px;'>MINSUR S.A. — Panel Gerencial Web</h1>
        <span style='background: #38bdf8; color: #0f172a; padding: 6px 12px; border-radius: 20px; font-weight: bold; font-size: 13px;'>Última Actualización Fiscal: {int(ultimo_registro['Año'])}</span>
    </div>
""", unsafe_allow_html=True)

# Selectores superiores
col_sel1, col_sel2 = st.columns([1, 3])
with col_sel1:
    anio_seleccionado = st.selectbox("📅 Seleccionar Año de Análisis:", anios_disponibles)

datos_anio = df[df['Año'] == anio_seleccionado].iloc[0]

# KPIs Principales en Pantalla
st.markdown("### 📊 Indicadores Clave de Rendimiento (KPIs)")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Liquidez Corriente", f"{datos_anio['Liquidez']} x", help="Activo Corriente / Pasivo Corriente")
kpi2.metric("Endeudamiento Global", f"{datos_anio['Endeudamiento']} %", help="Pasivo Total / Activo Total")
kpi3.metric("Rentabilidad ROA", f"{datos_anio['ROA']} %", help="Utilidad Neta / Activo Total")
kpi4.metric("Rentabilidad ROE", f"{datos_anio['ROE']} %", help="Utilidad Neta / Patrimonio")

st.markdown("---")

# Gráficos Interactivos
st.markdown("### 📈 Tendencias Históricas Consolidadas")
g1, g2 = st.columns(2)

def crear_grafico_linea(x, y, titulo, color):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y, mode='lines+markers', name=titulo, line=dict(color=color, width=3), marker=dict(size=8)))
    fig.update_layout(title=titulo, margin=dict(l=20, r=20, t=40, b=20), height=300, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    fig.update_xaxes(gridcolor='#e2e8f0')
    fig.update_yaxes(gridcolor='#e2e8f0')
    return fig

with g1:
    st.plotly_chart(crear_grafico_linea(df['Año'], df['Liquidez'], "Evolución de Liquidez Corriente (Veces)", "#2563eb"), use_container_width=True)
    st.plotly_chart(crear_grafico_linea(df['Año'], df['ROA'], "Retorno sobre Activos - ROA (%)", "#16a34a"), use_container_width=True)

with g2:
    st.plotly_chart(crear_grafico_linea(df['Año'], df['Endeudamiento'], "Ratio de Endeudamiento Global (%)", "#dc2626"), use_container_width=True)
    st.plotly_chart(crear_grafico_linea(df['Año'], df['ROE'], "Retorno sobre Patrimonio - ROE (%)", "#ea580c"), use_container_width=True)

st.markdown("---")

# Auditoría Automática Detallada
st.markdown(f"### 📑 Auditoría e Interpretación Automatizada — Año {anio_seleccionado}")

# Lógica de Diagnósticos integrada
def mostrar_diagnostico(titulo, valor, tipo):
    if tipo == "liq":
        if valor >= 2.5: status, msg = "🟢 EXCESO", f"Minsur presenta un ratio de {valor}x, denotando holgura financiera excepcional. Activos líquidos significativos rindiendo por debajo de su costo."
        elif valor >= 1.2: status, msg = "🟢 ÓPTIMO", f"El indicador de {valor}x refleja una gestión de capital de trabajo saludable y alineada con la minería a gran escala."
        else: status, msg = "🔴 TENSIÓN", f"Con un nivel de {valor}x, el margen de maniobra se encuentra en zona de vulnerabilidad estructural."
    elif tipo == "sol":
        if valor <= 40: status, msg = "🟢 CONSERVADOR", f"El ratio de endeudamiento global se sitúa en un sólido {valor}%. Otorga una altísima calificación crediticia corporativa."
        elif valor <= 55: status, msg = "🟡 EQUILIBRADO", f"La estructura de capital muestra un nivel de apalancamiento del {valor}%, reflejando un equilibrio corporativo estándar."
        else: status, msg = "🔴 ALTO RIESGO", f"Los acreedores externos controlan el {valor}% de la estructura de activos. Eleva drásticamente la carga financiera fija."
    else:
        if valor < 0: status, msg = "🔴 CRÍTICO", f"El ejercicio arroja destrucción de valor con pérdidas netas operativas en este periodo."
        elif valor >= 20: status, msg = "🟢 EXCEPCIONAL", f"Demuestra una eficiencia sobresaliente para multiplicar el capital, superando con holgura el costo de capital (WACC)."
        else: status, msg = "🟡 ESTABLE", f"Capacidad sostenida de generación de beneficios dentro del promedio industrial minero."
    
    st.info(f"**{titulo} [{status}]:** {msg}")

mostrar_diagnostico("Gestión de Liquidez Comercial", datos_anio['Liquidez'], "liq")
mostrar_diagnostico("Estructura de Capital Corporativo", datos_anio['Endeudamiento'], "sol")
mostrar_diagnostico("Rendimiento y Creación de Valor (ROE)", datos_anio['ROE'], "rent")

st.markdown("---")
# Tabla de datos completa al final
st.markdown("### 📋 Historial de Datos Consolidados")
st.dataframe(df[['Año', 'Liquidez', 'Endeudamiento', 'ROA', 'ROE']], use_container_width=True)