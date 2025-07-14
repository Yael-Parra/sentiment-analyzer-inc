import sys
from pathlib import Path
import time

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT_DIR))
import streamlit as st
import threading
import asyncio
import re
import pandas as pd
from server.monitoring.monitor_live_chat import LiveChatMonitor, API_KEY


st.set_page_config(page_title="YouTube Live Chat Monitor", layout="wide")

st.title("📡 YouTube Live Chat Monitor en Vivo")
st.markdown("Monitorea mensajes de transmisiones en vivo y detecta comentarios tóxicos con IA.")

# Verifica si el monitor ya está inicializado
if "live_monitor" not in st.session_state:
    if API_KEY:
        st.session_state.live_monitor = LiveChatMonitor(API_KEY)
    else:
        st.session_state.live_monitor = None

if "video_id" not in st.session_state:
    st.session_state.video_id = ""

def extract_video_id(url_or_id: str) -> str:
    if re.match(r"^[a-zA-Z0-9_-]{11}$", url_or_id):
        return url_or_id
    match = re.search(r"(?:v=|youtu.be/)([a-zA-Z0-9_-]{11})", url_or_id)
    if match:
        return match.group(1)
    raise ValueError("No se pudo extraer un ID de video válido.")

# estadísticas y comentarios
stats_placeholder = st.empty()
comments_placeholder = st.empty()

def update_dashboard():
    #Función para redibujar los componentes del dashboard.
    monitor = st.session_state.live_monitor
    stats = monitor.get_status().get(st.session_state.video_id, {})
    
    with stats_placeholder.container():
        st.subheader("📊 Estadísticas en Tiempo Real")
        col1, col2, col3 = st.columns(3)
        total = stats.get("total_messages", 0)
        toxic = stats.get("toxic_messages", 0)
        
        col1.metric("Total de Mensajes", total)
        col2.metric("Mensajes Tóxicos", toxic)
        
        percentage_toxic = (toxic / total * 100) if total > 0 else 0
        col3.metric("Porcentaje de Toxicidad", f"{percentage_toxic:.2f}%")

        if total > 0:
            chart_data = pd.DataFrame({
                "Tipo": ["Normales", "Tóxicos"],
                "Cantidad": [total - toxic, toxic]
            })
            st.bar_chart(chart_data.set_index("Tipo"))

    with comments_placeholder.container():
        st.subheader("📋 Últimos Comentarios")
        comments_list = stats.get("comments", [])
        if comments_list:
            df_comments = pd.DataFrame(comments_list)
            
            def highlight_toxic(row):
                color = 'background-color: #FF4B4B; color: white' if row["Es Tóxico"] else ''
                return [color] * len(row)
                
            styled_df = df_comments.style.apply(highlight_toxic, axis=1)
            st.dataframe(styled_df, use_container_width=True, height=400)
        else:
            st.info("Esperando los primeros comentarios...")

def run_monitor_in_background(monitor, video_id):
    #Esta función se ejecuta en un hilo separado y solo se encarga de correr el monitor.
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # 1. Iniciamos el monitoreo.
    loop.run_until_complete(monitor.start_monitoring(video_id))
    
    # 2. Buscamos la tarea que acabamos de crear.
    monitor_task = monitor.active_monitors.get(video_id)
    
    if monitor_task:
        try:
            # 3. LE DECIMOS AL HILO: "Espera aquí hasta que esta tarea termine".
            # Como la tarea es un bucle infinito, el hilo se quedará vivo.
            loop.run_until_complete(monitor_task)
        except asyncio.CancelledError:
            # Esto ocurre cuando el usuario presiona "Detener", lo cual es correcto.
            print(f"ℹ️ Tarea de monitoreo para {video_id} fue cancelada correctamente.")

# barra lateral
with st.sidebar:
    st.header("Controles")
    with st.form("start_form"):
        video_input = st.text_input("URL o ID del video en vivo:", value=st.session_state.video_id)
        submitted = st.form_submit_button("▶️ Iniciar Monitoreo")

    if st.button("⏹️ Detener Monitoreo"):
        if st.session_state.video_id and st.session_state.live_monitor:
            st.session_state.live_monitor.stop_monitoring(st.session_state.video_id)
            st.session_state.video_id = ""
            st.info("Monitoreo detenido.")

if submitted and video_input:
    try:
        video_id = extract_video_id(video_input)
        if st.session_state.video_id != video_id:
            st.session_state.video_id = video_id
            
            monitor_object = st.session_state.live_monitor
            thread = threading.Thread(
                target=run_monitor_in_background, 
                args=(monitor_object, video_id), 
                daemon=True
            )
            thread.start()
            st.sidebar.success(f"Monitoreando video {video_id}...")
    except Exception as e:
        st.sidebar.error(f"Error: {e}")

if st.session_state.live_monitor:
    while True:
        update_dashboard()
        time.sleep(1)
else:
    st.error("El monitor no se ha podido cargar. Revisa la API Key en tu archivo .env y los logs de la terminal.")