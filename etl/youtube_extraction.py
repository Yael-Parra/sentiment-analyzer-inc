from dotenv import load_dotenv
import os, requests, time, pandas as pd
import re

load_dotenv()
API_KEY = os.getenv("YouTube_Data_API_v3")

def extract_video_id(url_or_id):
    print(f"🔍 Extrayendo ID del vídeo de: {url_or_id}")
    pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(pattern, url_or_id)
    if match:
        video_id = match.group(1)
        print(f"✅ ID extraído: {video_id}")
        return video_id
    else:
        print(f"⚠️ No se pudo extraer ID, asumiendo input es ID directo: {url_or_id}")
        return url_or_id

def fetch_video_metadata(video_id, api_key):
    print(f"▶️ Iniciando extracción de metadatos para video {video_id}")
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "snippet,statistics",
        "id": video_id,
        "key": api_key
    }
    r = requests.get(url, params=params)
    print(f"📦 Estado HTTP metadata: {r.status_code}")
    r.raise_for_status()
    items = r.json().get("items", [])
    if not items:
        raise ValueError("Video no encontrado")
    print(f"✅ Metadatos obtenidos para video {video_id}")
    return items[0]

def fetch_comment_threads(video_id, max_total=100000, delay=1):
    print(f"▶️ Iniciando extracción de comentarios para video {video_id}")
    url = "https://www.googleapis.com/youtube/v3/commentThreads"
    comments = []
    token = None
    total = 0
    round_count = 0

    while total < max_total:
        round_count += 1
        print(f"\n🔁 Petición {round_count}: descargando comentarios...")
        params = {
            "part": "snippet,replies",
            "videoId": video_id,
            "maxResults": min(100, max_total - total),
            "textFormat": "plainText",
            "key": API_KEY
        }
        if token:
            params["pageToken"] = token
            print(f"➡️ Usando pageToken: {token}")

        response = requests.get(url, params=params)
        print(f"📦 Estado HTTP comentarios: {response.status_code}")
        response.raise_for_status()
        data = response.json()
        items = data.get("items", [])
        print(f"📥 Comentarios recibidos en esta tanda: {len(items)}")

        for item in items:
            s = item["snippet"]
            top = s["topLevelComment"]["snippet"]

            comments.append({
                "threadId": item["id"],
                "commentId": item["id"],
                "videoId": video_id,
                "author": top.get("authorDisplayName"),
                "authorChannelId": top.get("authorChannelId", {}).get("value"),
                "isReply": False,
                "parentCommentId": None,
                "publishedAtComment": top.get("publishedAt"),
                "text": top.get("textDisplay"),
                "likeCountComment": top.get("likeCount"),
                "replyCount": s.get("totalReplyCount")
            })
            total += 1

            for rep in item.get("replies", {}).get("comments", []):
                rps = rep["snippet"]
                comments.append({
                    "threadId": item["id"],
                    "commentId": rep["id"],
                    "videoId": video_id,
                    "author": rps.get("authorDisplayName"),
                    "authorChannelId": rps.get("authorChannelId", {}).get("value"),
                    "isReply": True,
                    "parentCommentId": rps.get("parentId"),
                    "publishedAtComment": rps.get("publishedAt"),
                    "text": rps.get("textDisplay"),
                    "likeCountComment": rps.get("likeCount"),
                    "replyCount": None
                })
                total += 1
                if total >= max_total:
                    break
            if total >= max_total:
                break

        print(f"✅ Total comentarios acumulados: {total}")
        token = data.get("nextPageToken")
        if not token:
            print("🚫 No hay más páginas disponibles.")
            break

        print(f"⏳ Esperando {delay} segundos antes de la siguiente petición...")
        time.sleep(delay)

    print(f"\n🎯 Total final de comentarios extraídos: {total}")
    return comments

def save_results(df, video_metadata, outdir="etl/data"):
    print("▶️ Guardando resultados...")
    os.makedirs(outdir, exist_ok=True)
    vid = video_metadata["id"]
    path_comments = os.path.join(outdir, f"youtube_comments_{vid}.csv.gz")
    df.to_csv(path_comments, index=False, compression="gzip", encoding="utf-8")
    
    video_info = {
        "videoId": vid,
        "videoPublishedAt": video_metadata["snippet"]["publishedAt"],
        "videoLikeCount": int(video_metadata["statistics"].get("likeCount", 0)),
        "videoCommentCount": int(video_metadata["statistics"].get("commentCount", 0))
    }
    meta_df = pd.DataFrame([video_info])
    path_meta = os.path.join(outdir, f"youtube_metadata_{vid}.csv")
    meta_df.to_csv(path_meta, index=False)
    print(f"✅ Comentarios guardados en: {path_comments}")
    print(f"✅ Metadatos guardados en: {path_meta}")

if __name__ == "__main__":
    url_or_id = input("Introduce URL o ID de vídeo YouTube: ").strip()
    video_id = extract_video_id(url_or_id)
    if not API_KEY:
        print("❌ No API_KEY en .env")
        exit(1)

    print(f"Extrayendo metadatos del vídeo {video_id}...")
    metadata = fetch_video_metadata(video_id, API_KEY)
    print("Extrayendo comentarios y respuestas...")
    comments = fetch_comment_threads(video_id, max_total=100000)
    print(f"{len(comments)} comentarios y respuestas extraídos.")

    df = pd.DataFrame(comments)
    print("Primeros comentarios extraídos:")
    print(df.head())

    save_results(df, metadata)
