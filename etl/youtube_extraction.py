from dotenv import load_dotenv
import os
import requests
import pandas as pd


load_dotenv()
API_KEY = os.getenv("API_KEY")

def get_comments(video_id, api_key, max_results=100):
    url = "https://www.googleapis.com/youtube/v3/commentThreads"
    params = {
        "part": "snippet",
        "videoId": video_id,
        "maxResults": max_results,
        "textFormat": "plainText",
        "key": api_key
    }

    response = requests.get(url, params=params)
    
    if response.status_code != 200:
        print(f"❌ Error: {response.status_code} - {response.text}")
        return []
    
    data = response.json()
    comments_data = []

    for item in data.get("items", []):
        comment_id = item["id"]
        comment_text = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
        comments_data.append({
            "CommentId": comment_id,
            "VideoId": video_id,
            "Text": comment_text
        })

    return comments_data

if __name__ == "__main__":
    video_id = input("👉 Introduce el ID del vídeo de YouTube: ").strip()
    
    if not API_KEY:
        print("⚠️ No se encontró API_KEY. Verifica tu archivo .env.")
    else:
        comments = get_comments(video_id, API_KEY)

        if comments:
            df = pd.DataFrame(comments, columns=["CommentId", "VideoId", "Text"])
            df.to_csv("youtube_comments.csv", index=False)
            print(f"✅ {len(comments)} comentarios guardados en youtube_comments.csv")
        else:
            print("⚠️ No se obtuvieron comentarios.")

# Documentación oficial de la API de YouTube: https://developers.google.com/youtube/v3/docs/commentThreads/list?hl=es-419

# - Limpiar el texto, quitar HTML, minúsculas, signos innecesarios...  
# - Tokenizar el texto 
# - Vectorizar, convertrir tokens en números (TF-IDF, embeddings...)  
# - Pasar los vectores al modelo. 
