# etl/youtube_extraction.py

from dotenv import load_dotenv
import os, requests, time, pandas as pd, re

load_dotenv()
API_KEY = os.getenv("YouTube_Data_API_v3")

def extract_video_id(url_or_id):
    """
    Accepts a full YouTube URL or a plain video ID.
    Extracts the ID if it's a URL, otherwise returns the ID as-is.
    """
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url_or_id)
    if match:
        return match.group(1)
    elif len(url_or_id) == 11:
        return url_or_id
    else:
        raise ValueError("❌ No se pudo extraer un ID válido del vídeo.")

def fetch_comment_threads(video_id, max_total=5000, delay=1):
    url = "https://www.googleapis.com/youtube/v3/commentThreads"
    comments = []
    token = None
    total = 0
    round_count = 0

    while total < max_total:
        print(f"\n🔁 Petición {round_count + 1}: descargando comentarios...")

        params = {
            "part": "id,snippet,replies",
            "videoId": video_id,
            "maxResults": min(100, max_total - total),
            "textFormat": "plainText",
            "key": API_KEY
        }

        if token:
            params["pageToken"] = token
            print(f"➡️ Siguiente token: {token}")

        try:
            response = requests.get(url, params=params)
        except Exception as e:
            print(f"❌ Error en la solicitud: {e}")
            break

        print(f"📦 Estado HTTP: {response.status_code}")
        if response.status_code != 200:
            print(f"❌ Error: {response.text}")
            break

        data = response.json()
        items = data.get("items", [])
        print(f"📥 Comentarios recibidos en esta tanda: {len(items)}")

        for item in items:
            s = item["snippet"]
            top = s["topLevelComment"]["snippet"]
            comments.append({
                "threadId": item["id"],
                "videoId": video_id,
                "commentId": item["id"],
                "author": top["authorDisplayName"],
                "publishedAt": top["publishedAt"],
                "updatedAt": top.get("updatedAt"),
                "text": top["textDisplay"],
                "likeCount": top["likeCount"],
                "replyCount": s["totalReplyCount"],
                "canReply": s["canReply"],
                "isPublic": s["isPublic"],
                "parentId": None
            })
            total += 1

            for rep in item.get("replies", {}).get("comments", []):
                rps = rep["snippet"]
                comments.append({
                    "threadId": item["id"],
                    "videoId": video_id,
                    "commentId": rep["id"],
                    "author": rps["authorDisplayName"],
                    "publishedAt": rps["publishedAt"],
                    "updatedAt": rps.get("updatedAt"),
                    "text": rps["textDisplay"],
                    "likeCount": rps["likeCount"],
                    "replyCount": None,
                    "canReply": None,
                    "isPublic": None,
                    "parentId": rps["parentId"]
                })
                total += 1

        print(f"✅ Total acumulado: {total}")
        token = data.get("nextPageToken")
        if not token:
            print("🚫 No hay más páginas disponibles.")
            break

        round_count += 1
        print(f"⏳ Esperando {delay} segundos antes de la siguiente petición...")
        time.sleep(delay)

    print(f"\n🎯 Total final de comentarios obtenidos: {total}")
    return comments


def save_comments(video_id, comments, base_dir="etl"):
    df = pd.DataFrame(comments)
    outdir = os.path.join(base_dir, "data")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, f"youtube_comments_{video_id}.csv.gz")
    df.to_csv(path, index=False, compression="gzip", encoding="utf-8")
    print(f"\n✅ Datos guardados en: {path}")
    return df


if __name__ == "__main__":
    try:
        raw_input_id = input("📺 Introduce la URL o ID del vídeo de YouTube: ").strip()
        if not API_KEY:
            print("❌ No se encontró API_KEY. Verifica tu archivo .env.")
        else:
            vid = extract_video_id(raw_input_id)
            print(f"🔎 Video ID extraído: {vid}")
            print("🚀 Iniciando extracción de comentarios...")
            com = fetch_comment_threads(vid, max_total=7000)
            df = save_comments(vid, com)
            print(df.info())
    except KeyboardInterrupt:
        print("\n🛑 Proceso interrumpido por la usuaria.")
    except ValueError as ve:
        print(str(ve))
