from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv(override=True)
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def test_connection():
    try:
        response = supabase.table("sentiment_analyzer").select("*").execute()
        return response.data is not None
    
    except Exception as e:
        print(f"❌Error al conectar la base de datos😭: {e}")
        return False
    
    
if __name__ == "__main__":
    if test_connection():
        print("💕Conexión exitosa con la base de datos 💕")
    else:
        print("❌Error al conectar la base de datos😭")