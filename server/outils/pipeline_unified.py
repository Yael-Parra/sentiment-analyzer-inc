import pandas as pd
import sys
from pathlib import Path
from typing import Dict, List, Any
sys.path.append(str(Path(__file__).parent.parent.parent))  
from etl.youtube_extraction import extract_video_id, fetch_comment_threads
from server.outils.pipeline_cleaning import clean_youtube_data
from server.database.save_comments import save_comments_batch

# Configuración del modelo
MODEL_DIR = Path("models/bilstm_advanced")
sys.path.append(str(MODEL_DIR))

class UnifiedPipeline:
    db_fields = {
        "video_id", "text",
        "toxic_probability", "hatespeech_probability", "abusive_probability",
        "provocative_probability", "racist_probability", "obscene_probability",
        "threat_probability", "religious_hate_probability", "nationalist_probability",
        "sexist_probability", "homophobic_probability", "radicalism_probability",
        "is_toxic", "is_hatespeech", "is_abusive", "is_provocative",
        "is_racist", "is_obscene", "is_threat", "is_religious_hate",
        "is_nationalist", "is_sexist", "is_homophobic", "is_radicalism",
        "sentiment_type", "sentiment_intensity"
    }

    def __init__(self):
        self.model_loader = self._load_model()
    
    def _load_model(self):
        """Carga el modelo de toxicidad"""
        try:
            from multitoxic_v1_0_20250709_003639_loader import MultitoxicLoader
            print("🔄 Inicializando modelo MULTITOXIC...")
            model_loader = MultitoxicLoader(MODEL_DIR)
            model_loader.load_model()
            print("✅ Modelo cargado exitosamente")
            return model_loader
        except Exception as e:
            print(f"❌ Error cargando modelo: {e}")
            return None
    def _get_default_toxicity_values(self) -> Dict[str, Any]:

        """Devuelve valores por defecto para todos los campos de toxicidad"""
        return {
            "toxic_probability": 0.0,
            "hatespeech_probability": 0.0,
            "abusive_probability": 0.0,
            "provocative_probability": 0.0,
            "racist_probability": 0.0,
            "obscene_probability": 0.0,
            "threat_probability": 0.0,
            "religious_hate_probability": 0.0,
            "nationalist_probability": 0.0,
            "sexist_probability": 0.0,
            "homophobic_probability": 0.0,
            "radicalism_probability": 0.0,
            "is_toxic": False,
            "is_hatespeech": False,
            "is_abusive": False,
            "is_provocative": False,
            "is_racist": False,
            "is_obscene": False,
            "is_threat": False,
            "is_religious_hate": False,
            "is_nationalist": False,
            "is_sexist": False,
            "is_homophobic": False,
            "is_radicalism": False
        }
    
    def process_comments(self, youtube_url_or_id: str, max_comments: int = 100) -> Dict[str, Any]:
        try:
            video_id = extract_video_id(youtube_url_or_id)
            raw_comments = fetch_comment_threads(video_id, max_total=max_comments)
            
            if not raw_comments:
                return self._empty_response(video_id)

            # Debug: Inspecciona comentarios crudos
            print(f"\n📦 Comentarios crudos recibidos (muestra 1):")
            print(raw_comments[0] if raw_comments else "No hay comentarios")

            df_clean = clean_youtube_data(pd.DataFrame(raw_comments))
            
            # Debug: Verifica el DataFrame limpio
            print("\n🧹 DataFrame limpio - Columnas:", df_clean.columns.tolist())
            print("Muestra primera fila:", df_clean.iloc[0].to_dict() if not df_clean.empty else "DataFrame vacío")
            
            enriched = self._enrich_comments(df_clean, video_id)
            
            if not enriched:
                raise ValueError("No se pudo enriquecer ningún comentario")
                
            return {
                "video_id": video_id,
                "total_comments": len(enriched),
                "stats": self._calculate_stats(enriched),
                "comments": enriched
            }
            
        except Exception as e:
            print(f"❌ Error en process_comments: {str(e)}")
            raise

    def _enrich_comments(self, clean_df: pd.DataFrame, video_id: str) -> List[Dict[str, Any]]:
        enriched = []
        
        # Verificación exhaustiva de columnas
        required_columns = {"text", "sentiment_type", "sentiment_intensity"}
        missing_cols = required_columns - set(clean_df.columns)
        if missing_cols:
            print(f"🚨 Columnas faltantes: {missing_cols}")
            return []

        for _, row in clean_df.iterrows():
            try:
                # Debug: Verifica estructura del comentario
                print(f"\n📝 Comentario crudo: { {k: type(v) for k, v in row.items()} }")
                
                # Asegura que los campos críticos existen
                comment_data = {
                    "video_id": video_id,
                    "text": str(row["text"]),
                    "sentiment_type": str(row.get("sentiment_type", "neutral")),
                    "sentiment_intensity": str(row.get("sentiment_intensity", "weak"))
                }
                
                # Añade toxicidad solo si el modelo está cargado
                if self.model_loader:
                    tox_data = self._predict_toxicity(str(row["text"]))
                    comment_data.update(tox_data)
                
                enriched.append(comment_data)
                
            except Exception as e:
                print(f"⚠️ Error procesando fila: {e}\nContenido: {row.to_dict()}")
                continue
                
        return enriched

    def _predict_toxicity(self, text: str) -> Dict[str, Any]:
        """Wrapper para las predicciones del modelo"""
        if not self.model_loader:
            return self._get_default_toxicity_values()

        try:
            prediction = self.model_loader.predict(text, return_probabilities=True, return_categories=True)
            probs = prediction.get("probabilities", {})
            detected = prediction.get("detected_types", [])
            
            return {
                "toxic_probability": probs.get("toxic", 0.0),
                "hatespeech_probability": probs.get("hatespeech", 0.0),
                "abusive_probability": probs.get("abusive", 0.0),
                "provocative_probability": probs.get("provocative", 0.0),
                "racist_probability": probs.get("racist", 0.0),
                "obscene_probability": probs.get("obscene", 0.0),
                "threat_probability": probs.get("threat", 0.0),
                "religious_hate_probability": probs.get("religious_hate", 0.0),
                "nationalist_probability": probs.get("nationalist", 0.0),
                "sexist_probability": probs.get("sexist", 0.0),
                "homophobic_probability": probs.get("homophobic", 0.0),
                "radicalism_probability": probs.get("radicalism", 0.0),
                "is_toxic": "toxic" in detected,
                "is_hatespeech": "hatespeech" in detected,
                "is_abusive": "abusive" in detected,
                "is_provocative": "provocative" in detected,
                "is_racist": "racist" in detected,
                "is_obscene": "obscene" in detected,
                "is_threat": "threat" in detected,
                "is_religious_hate": "religious_hate" in detected,
                "is_nationalist": "nationalist" in detected,
                "is_sexist": "sexist" in detected,
                "is_homophobic": "homophobic" in detected,
                "is_radicalism": "radicalism" in detected
            }
        except Exception as e:
            print(f"⚠️ Error en predicción de toxicidad: {e}")
            return self._get_default_toxicity_values()

    def _calculate_stats(self, comments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calcula estadísticas de toxicidad"""
        stats = {}
        toxic_fields = [
            "toxic", "hatespeech", "abusive", "provocative", "racist", 
            "obscene", "threat", "religious_hate", "nationalist", 
            "sexist", "homophobic", "radicalism"
        ]
        
        for field in toxic_fields:
            count = sum(1 for c in comments if c.get(f"is_{field}", False))
            stats[field] = {
                "count": count,
                "percentage": (count / len(comments)) * 100 if comments else 0
            }
        return stats

    def _save_to_db(self, comments: List[Dict[str, Any]]):
        """Guarda solo los campos necesarios en Supabase"""
        try:
            save_comments_batch(comments)
        except Exception as e:
            print(f"⚠️ Error guardando en BD: {e}")

    def _empty_response(self, video_id: str) -> Dict[str, Any]:
        return {
            "video_id": video_id,
            "total_comments": 0,
            "stats": {},
            "comments": []
        }

    def _default_comment(self, video_id: str, row: pd.Series) -> Dict[str, Any]:
        """Comentario con valores por defecto para manejar errores"""
        return {
            "video_id": video_id,
            "text": row["text"],
            "sentiment_type": "neutral",
            "sentiment_intensity": "weak",
            **self._get_default_toxicity_values()
        }

# # Uso con test
# if __name__ == "__main__":
#     """Zona de pruebas manuales"""
#     print("\n" + "="*50)
#     print("🔧 INICIANDO PRUEBAS MANUALES")
#     print("="*50 + "\n")
    
#     # 1. Instanciar el pipeline
#     pipeline = UnifiedPipeline()
    
#     # 2. Prueba _predict_toxicity()
#     test_text = "This is a hate speech example!"
#     print("🧪 Probando _predict_toxicity():")
#     tox_result = pipeline._predict_toxicity(test_text)
#     print(tox_result)
    
#     # 3. Prueba _calculate_stats()
#     print("\n🧪 Probando _calculate_stats():")
#     test_comments = [
#         {"is_toxic": True, "is_hatespeech": False},
#         {"is_toxic": False, "is_hatespeech": True}
#     ]
#     stats = pipeline._calculate_stats(test_comments)
#     print(stats)
    
#     # 4. Prueba integrada CORREGIDA (usar URL string, no DataFrame)
#     print("\n🧪 Prueba completa con URL simulada:")
#     test_url = "https://www.youtube.com/watch?v=fCPoKsTJfDs&list=RDfCPoKsTJfDs&start_radio=1"
#     test_comments_data = [{
#         "text": "I love this video!",
#         "sentiment_type": "positive",
#         "sentiment_intensity": "strong",
#         "author": "test_user"
#     }]
    
#     # Simula el flujo completo CORRECTAMENTE
#     video_id = extract_video_id(test_url)
#     df_clean = pd.DataFrame(test_comments_data)
#     enriched = pipeline._enrich_comments(df_clean, video_id)
#     stats = pipeline._calculate_stats(enriched)
    
#     print("Video ID:", video_id)
#     print("Comentarios enriquecidos:", enriched)
#     print("Estadísticas:", stats)