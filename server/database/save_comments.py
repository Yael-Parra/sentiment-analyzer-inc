from server.database.connection_db import supabase
from typing import List, Dict, Any
from pydantic import ValidationError
from server.schemas import Comment


## Esta función es para guardar comentario unico para pruebas
def save_comment(comment_data: Dict[str, Any]) -> Dict[str, Any] | None:
    """
    Guarda un comentario individual en Supabase con validación de schema
    """
    try:
        # VALIDAR con schema Comment
        try:
            validated_comment = Comment(**comment_data)
        except ValidationError as ve:
            print(f"⚠️ Error de validación: {ve}")
            return None
        
        # Convertir a dict y filtrar solo campos de BD
        comment_dict = validated_comment.dict()
        db_fields = {
            "video_id", "text",
            "toxic_probability", "hatespeech_probability", "abusive_probability",
            "provocative_probability", "racist_probability", "obscene_probability",
            "threat_probability", "religious_hate_probability", "nationalist_probability",
            "sexist_probability", "homophobic_probability", "radicalism_probability",
            "is_toxic", "is_hatespeech", "is_abusive", "is_provocative",
            "is_racist", "is_obscene", "is_threat", "is_religious_hate",
            "is_nationalist", "is_sexist", "is_homophobic", "is_radicalism",
            "sentiment_type", "sentiment_score", "sentiment_intensity",
            "total_likes_comment"
        }
        
        # extraer campos de BD (sin id ni created_at)
        filtered_data = {k: v for k, v in comment_dict.items() if k in db_fields and v is not None}
        
        print(f"🔄 Guardando comentario: {filtered_data['text'][:50]}...")
        response = supabase.table("sentiment_analyzer").insert(filtered_data).execute()
        
        if response.data:
            print(f"✅ Comentario guardado con ID: {response.data[0]['id']}")
            return response.data[0]
        else:
            print(f"⚠️ Advertencia: No se recibieron datos en la respuesta")
            return None
            
    except Exception as e:
        print(f"❌ Error al guardar comentario: {e}")
        print(f"📋 Datos que causaron error: {comment_data}")
        return None


## Esta función es para guardar múltiples comentarios, valida múltiples comentarios y los guarda todos de una vez

def save_comments_batch(comments_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Guarda múltiples comentarios con validación de schema
    """
    try:
        if not comments_list:
            print("⚠️ Lista de comentarios vacía")
            return []
        
        # valida cada comentario con schema
        validated_comments = []
        for i, comment in enumerate(comments_list):
            try:
                validated_comment = Comment(**comment)
                validated_comments.append(validated_comment.dict())
            except ValidationError as ve:
                print(f"⚠️ Comentario {i} inválido, saltando: {ve}")
                continue
        
        if not validated_comments:
            print("❌ No hay comentarios válidos para guardar")
            return []
        
        # Filtra campos para BD
        db_fields = {
            "video_id", "text",
            "toxic_probability", "hatespeech_probability", "abusive_probability",
            "provocative_probability", "racist_probability", "obscene_probability", 
            "threat_probability", "religious_hate_probability", "nationalist_probability",
            "sexist_probability", "homophobic_probability", "radicalism_probability",
            "is_toxic", "is_hatespeech", "is_abusive", "is_provocative",
            "is_racist", "is_obscene", "is_threat", "is_religious_hate",
            "is_nationalist", "is_sexist", "is_homophobic", "is_radicalism",
            "sentiment_type", "sentiment_score", "sentiment_intensity",
            "total_likes_comment"
        }
        
        # Prepara datos para inserción en lote
        batch_data = []
        for comment in validated_comments:
            filtered_comment = {k: v for k, v in comment.items() if k in db_fields and v is not None}
            batch_data.append(filtered_comment)
        
        print(f"🔄 Guardando {len(batch_data)} comentarios en lote...")
        response = supabase.table("sentiment_analyzer").insert(batch_data).execute()
        
        if response.data:
            print(f"✅ {len(response.data)} comentarios guardados correctamente")
            return response.data
        else:
            print("⚠️ Advertencia: No se recibieron datos en la respuesta")
            return []
            
    except Exception as e:
        print(f"❌ Error al guardar comentarios en lote: {e}")
        return []


## Esta función es para recuperar comentarios de un video específico
def get_comments_by_video(video_id: str) -> List[Dict[str, Any]]:
    """
    Recupera comentarios de un video específico
    """
    try:
        print(f"🔍 Buscando comentarios para video: {video_id}")
        response = supabase.table("sentiment_analyzer").select("*").eq("video_id", video_id).execute()
        
        if response.data:
            print(f"✅ Encontrados {len(response.data)} comentarios para el video")
            return response.data
        else:
            print("📭 No se encontraron comentarios para este video")
            return []
            
    except Exception as e:
        print(f"❌ Error al recuperar comentarios: {e}")
        return []


## Esta función es para eliminar todos los comentarios de un video específico
def delete_comments_by_video(video_id: str) -> bool:
    """
    Elimina todos los comentarios de un video
    """
    try:
        print(f"🗑️ Eliminando comentarios del video: {video_id}")
        response = supabase.table("sentiment_analyzer").delete().eq("video_id", video_id).execute()
        print(f"✅ Comentarios eliminados correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error al eliminar comentarios: {e}")
        return False


## Esta función es solo un test para probar que funcione el guardado
def test_save_function():
    """Función de prueba para verificar que el guardado funciona"""
    test_comment = {
        "video_id": "test_12345",
        "text": "Este es un comentario de prueba",
        "toxic_probability": 0.1,
        "is_toxic": False,
        "hatespeech_probability": 0.05,
        "is_hatespeech": False,
        "abusive_probability": 0.0,
        "is_abusive": False,
        "provocative_probability": 0.15,
        "is_provocative": False,
        "racist_probability": 0.0,
        "is_racist": False,
        "obscene_probability": 0.0,
        "is_obscene": False,
        "threat_probability": 0.0,
        "is_threat": False,
        "religious_hate_probability": 0.0,
        "is_religious_hate": False,
        "nationalist_probability": 0.0,
        "is_nationalist": False,
        "sexist_probability": 0.0,
        "is_sexist": False,
        "homophobic_probability": 0.0,
        "is_homophobic": False,
        "radicalism_probability": 0.0,
        "is_radicalism": False,
        # Los temporales se filtran automáticamente
        "sentiment_type": "positive",
        "sentiment_score": 0.8,
        "sentiment_intensity": "strong",
        "total_likes_comment": 1
    }
    
    result = save_comment(test_comment)
    if result:
        print("🎉 Test de guardado exitoso!")
        print(f"🆔 ID generado automáticamente: {result['id']}")
        print(f"📅 Created_at automático: {result['created_at']}")
        # Limpiar después del test
        delete_comments_by_video("test_12345")
        return True
    else:
        print("❌ Test de guardado falló")
        return False

if __name__ == "__main__":      # solo para testear manualmente
    test_save_function()


#  GUARDAR ESTADÍSTICAS DEL VIDEO
def save_video_statistics(video_id: str, complete_stats: Dict[str, Any]) -> Dict[str, Any] | None:
    """
    Guarda/actualiza estadísticas (UNA por video_id)
    Resumen de TODOS los comentarios del video
    """
    try:
        import json
        print(f"📊 Guardando estadísticas para video: {video_id}")

        stats_record = {
            "video_id": video_id,
            "total_comments": complete_stats.get("total_comments", 0),
            "percentage_toxicity": complete_stats.get("percentage_toxicity", 0.0),
            "mean_likes": complete_stats.get("mean_likes", 0.0),
            "max_likes": complete_stats.get("max_likes", 0),
            "total_likes": complete_stats.get("total_likes", 0),
            "self_promotional": complete_stats.get("self_promotional", 0),
            "mean_sentiment_score": complete_stats.get("mean_sentiment_score", 0.0),
            "sentiment_distribution": json.dumps(complete_stats.get("sentiment_distribution", {})),
            "toxicity_stats": json.dumps(complete_stats.get("toxicity_stats", {})),
        }
        
        # UPSERT: insertar o actualizar si ya existe
        response = supabase.table("video_statistics")\
            .upsert(stats_record, on_conflict="video_id")\
            .execute()
        
        if response.data:
            print(f"✅ Estadísticas guardadas/actualizadas para video: {video_id}")
            return response.data[0]
        else:
            print(f"⚠️ No se recibieron datos al guardar estadísticas")
            return None
            
    except Exception as e:
        print(f"❌ Error al guardar estadísticas: {e}")
        return None

def get_video_statistics(video_id: str) -> Dict[str, Any] | None:
    """
    Recupera estadísticas de UN video específico
    """
    try:
        import json
        print(f"📊 Buscando estadísticas para video: {video_id}")
        response = supabase.table("video_statistics")\
            .select("*")\
            .eq("video_id", video_id)\
            .single()\
            .execute()
        
        if response.data:
            # Parsear campos JSON de vuelta a dict
            stats = response.data.copy()
            if stats.get("sentiment_distribution"):
                stats["sentiment_distribution"] = json.loads(stats["sentiment_distribution"])
            if stats.get("toxicity_stats"):
                stats["toxicity_stats"] = json.loads(stats["toxicity_stats"])
            
            print(f"✅ Estadísticas encontradas para video: {video_id}")
            return stats
        else:
            print(f"📭 No hay estadísticas guardadas para video: {video_id}")
            return None
            
    except Exception as e:
        print(f"❌ Error al recuperar estadísticas: {e}")
        return None