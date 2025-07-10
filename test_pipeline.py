import sys
from pathlib import Path
import pandas as pd

# Configuración de paths
sys.path.append(str(Path(__file__).parent.parent))  # Ajusta según tu estructura
from server.outils.pipeline_unified import UnifiedPipeline

def test_pipeline():
    print("🚀 Iniciando pruebas del UnifiedPipeline...\n")
    
    # 1. Instanciar el pipeline
    pipeline = UnifiedPipeline()
    
    # 2. Datos de prueba (simulando la salida de youtube_extraction)
    test_comments = [
        {
            "thread_id": "test1",
            "comment_id": "test1",
            "video_id": "test_video",
            "author": "@test_user",
            "authorChannel_id": "UCtest123",
            "is_reply": False,
            "parent_comment_id": None,
            "published_at_comment": "2024-07-15T14:30:00Z",
            "text": "This is a normal comment",
            "like_count_comment": 10,
            "reply_count": 2
        },
        {
            "thread_id": "test2",
            "comment_id": "test2",
            "video_id": "test_video",
            "author": "@toxic_user",
            "author_Channel_id": "UCtoxic123",
            "is_reply": False,
            "parent_comment_id": None,
            "published_at_comment": "2024-07-15T20:45:00Z",
            "text": "This is an offensive comment!",
            "like_count_comment": 5,
            "reply_count": 8
        }
    ]
    
    # 3. Procesamiento completo
    print("🔍 Probando process_comments()...")
    try:
        # Convertir a DataFrame (como lo haría clean_youtube_data)
        df = pd.DataFrame(test_comments)
        
        # Probar enriquecimiento
        print("\n🧪 Probando _enrich_comments()")
        enriched = pipeline._enrich_comments(df, "test_video")
        print(f"✅ Comentarios enriquecidos: {len(enriched)}")
        print("Muestra del primer comentario:", enriched[0])
        
        # Probar cálculo de stats
        print("\n🧪 Probando _calculate_stats()")
        stats = pipeline._calculate_stats(enriched)
        print("📊 Estadísticas generadas:")
        for k, v in stats.items():
            print(f"- {k}: {v}")
        
        # Probar pipeline completo
        print("\n🧪 Probando process_comments() con URL simulada")
        result = pipeline.process_comments("https://youtu.be/test_video", max_comments=2)
        print("\n🎉 Resultado final del pipeline:")
        print(f"- Video ID: {result['video_id']}")
        print(f"- Total comentarios: {result['total_comments']}")
        print(f"- Stats keys: {list(result['stats'].keys())}")
        print(f"- Primer comentario procesado: {result['comments'][0]['text'][:50]}...")
        
        return True
    except Exception as e:
        print(f"\n❌ Error en las pruebas: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    success = test_pipeline()
    print("\n🔥 Resultado final:", "✅ Éxito" if success else "❌ Fallo")