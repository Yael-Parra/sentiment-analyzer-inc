import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT_DIR))
import streamlit as st
import threading
import asyncio
import re
import pandas as pd
from server.monitoring.monitor_live_chat import live_monitor


st.set_page_config(page_title="YouTube Live Chat Monitor", layout="wide")

st.title("📡 YouTube Live Chat Monitor en Vivo")
st.markdown("Monitorea mensajes de transmisiones en vivo y detecta comentarios tóxicos con IA.")

# Función para extraer el ID del video desde URL o ID directo
def extract_video_id(url_or_id: str) -> str:
    # Si ya es un ID válido (11 caracteres alfanuméricos), lo devolvemos
    if re.match(r"^[a-zA-Z0-9_-]{11}$", url_or_id):
        return url_or_id
    # Si es una URL, intentamos extraer el ID
    match = re.search(r"(?:v=|youtu.be/)([a-zA-Z0-9_-]{11})", url_or_id)
    if match:
        return match.group(1)
    raise ValueError("No se pudo extraer un ID de video válido.")

# Estado global para comentarios
if "comments" not in st.session_state:
    st.session_state.comments = []

if "video_id" not in st.session_state:
    st.session_state.video_id = ""

async def run_monitor(video_id):
    await live_monitor.start_monitoring(video_id)
    while True:
        status = live_monitor.get_status().get(video_id, {})
        if status:
            st.session_state.stats = status
        await asyncio.sleep(5)

with st.form("start_form"):
    video_input = st.text_input("Introduce URL o ID del video en vivo:", value=st.session_state.video_id)
    submitted = st.form_submit_button("Iniciar monitoreo")

if submitted:
    try:
        video_id = extract_video_id(video_input)
        st.session_state.video_id = video_id

        def start_asyncio_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(run_monitor(video_id))

        t = threading.Thread(target=start_asyncio_loop)
        t.start()
        st.success(f"Monitoreando video {video_id}...")
    except Exception as e:
        st.error(f"Error: {e}")

if st.session_state.video_id:
    st.subheader("📊 Estadísticas")
    stats = live_monitor.get_status().get(st.session_state.video_id, {})
    col1, col2 = st.columns(2)
    col1.metric("Total de mensajes", stats.get("total_messages", 0))
    col2.metric("Mensajes tóxicos", stats.get("toxic_messages", 0))

    chart_data = pd.DataFrame({
        "Tipo": ["Normales", "Tóxicos"],
        "Cantidad": [
            stats.get("total_messages", 0) - stats.get("toxic_messages", 0),
            stats.get("toxic_messages", 0)
        ]
    })
    st.bar_chart(chart_data.set_index("Tipo"))

    st.subheader("📋 Últimos comentarios")
    st.warning("⚠️ Por ahora los comentarios solo se muestran en consola. Para verlos aquí, hay que modificar el monitor para guardar los mensajes en memoria.")
