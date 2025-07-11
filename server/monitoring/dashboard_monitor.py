import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import json

# Configuración de la página
st.set_page_config(
    page_title="🔍 Monitor YouTube - Tiempo Real",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Base URL
API_BASE = "http://localhost:8000"

# Título principal
st.title("🔍 Monitor YouTube - Tiempo Real")
st.markdown("---")

# Sidebar - Controles
st.sidebar.header("🎮 Controles")

# Input para nuevo video
with st.sidebar.form("start_monitor"):
    st.subheader("▶️ Iniciar Monitoreo")
    video_id = st.text_input("Video ID", placeholder="dQw4w9WgXcQ")
    interval_minutes = st.number_input("Intervalo (minutos)", min_value=1, max_value=60, value=2)
    max_comments = st.number_input("Max comentarios", min_value=5, max_value=100, value=10)
    
    if st.form_submit_button("🚀 Iniciar Monitoreo"):
        if video_id:
            try:
                response = requests.post(
                    f"{API_BASE}/monitor/start/{video_id}",
                    params={"interval_minutes": interval_minutes, "max_comments": max_comments}
                )
                if response.status_code == 200:
                    st.success(f"✅ Monitoreo iniciado para {video_id}")
                    st.rerun()
                else:
                    st.error(f"❌ Error: {response.text}")
            except Exception as e:
                st.error(f"❌ Error de conexión: {e}")

# Obtener estado actual
try:
    response = requests.get(f"{API_BASE}/monitor/status")
    if response.status_code == 200:
        status_data = response.json()
    else:
        status_data = {"active_monitors": [], "monitor_data": {}, "total_active": 0}
except:
    st.error("❌ No se puede conectar con el servidor")
    st.stop()

# Métricas principales
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("📊 Monitores Activos", status_data["total_active"])

with col2:
    total_checks = sum(data.get("total_checks", 0) for data in status_data["monitor_data"].values())
    st.metric("🔄 Checks Totales", total_checks)

with col3:
    total_new = sum(data.get("new_comments_found", 0) for data in status_data["monitor_data"].values())
    st.metric("🆕 Comentarios Nuevos", total_new)

with col4:
    total_toxic = sum(data.get("toxic_comments_found", 0) for data in status_data["monitor_data"].values())
    st.metric("⚠️ Comentarios Tóxicos", total_toxic)

st.markdown("---")

# Lista de monitores activos
if status_data["active_monitors"]:
    st.header("📋 Monitores Activos")
    
    for video_id in status_data["active_monitors"]:
        data = status_data["monitor_data"][video_id]
        
        with st.expander(f"📺 Video: {video_id}", expanded=True):
            # Información básica
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("⏱️ Intervalo", f"{data['interval_minutes']} min")
                st.metric("📊 Checks", data["total_checks"])
            
            with col2:
                st.metric("🆕 Nuevos", data["new_comments_found"])
                st.metric("⚠️ Tóxicos", data["toxic_comments_found"])
            
            with col3:
                started_at = datetime.fromisoformat(data["started_at"].replace('Z', '+00:00'))
                uptime = datetime.now() - started_at.replace(tzinfo=None)
                st.metric("⏰ Tiempo activo", f"{uptime.seconds // 3600}h {(uptime.seconds % 3600) // 60}m")
                
                if data["last_check"]:
                    last_check = datetime.fromisoformat(data["last_check"].replace('Z', '+00:00'))
                    st.metric("🔍 Último check", last_check.strftime("%H:%M:%S"))
            
            # Gráfico de actividad
            if data["total_checks"] > 0:
                # Crear datos simulados para el gráfico
                checks_data = []
                for i in range(data["total_checks"]):
                    check_time = started_at + timedelta(minutes=i * data["interval_minutes"])
                    checks_data.append({
                        "check": i + 1,
                        "time": check_time.strftime("%H:%M"),
                        "nuevos": 1 if i == 0 else 0,  # Simplificado
                        "tóxicos": 1 if i == 0 and data["toxic_comments_found"] > 0 else 0
                    })
                
                df_checks = pd.DataFrame(checks_data)
                
                fig = px.line(df_checks, x="check", y="nuevos", 
                            title=f"📈 Actividad del video {video_id}",
                            labels={"check": "Check #", "nuevos": "Comentarios nuevos"})
                st.plotly_chart(fig, use_container_width=True)
            
            # Botón para detener
            if st.button(f"🛑 Detener monitoreo de {video_id}", key=f"stop_{video_id}"):
                try:
                    response = requests.delete(f"{API_BASE}/monitor/stop/{video_id}")
                    if response.status_code == 200:
                        st.success(f"✅ Monitoreo detenido para {video_id}")
                        st.rerun()
                    else:
                        st.error(f"❌ Error: {response.text}")
                except Exception as e:
                    st.error(f"❌ Error: {e}")

else:
    st.info("📭 No hay monitores activos. Inicia uno desde el sidebar.")

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Configuración")

auto_refresh = st.sidebar.checkbox("🔄 Auto-actualizar", value=True)
if auto_refresh:
    refresh_interval = st.sidebar.slider("Intervalo de actualización (segundos)", 5, 60, 10)
    time.sleep(refresh_interval)
    st.rerun()

if st.sidebar.button("🔄 Actualizar ahora"):
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.header("📋 Logs Recientes")

st.sidebar.text_area("Logs", "🔍 Verificando cambios...\n✅ Monitor activo", height=100)


st.markdown("---")
st.markdown("🔍 **Monitor YouTube** - Detección de toxicidad en tiempo real")