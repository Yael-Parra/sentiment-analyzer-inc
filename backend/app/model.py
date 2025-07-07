import joblib

# Cambia la ruta a donde hayas guardado tu modelo entrenado
model = joblib.load("models/hate_speech_model.pkl")
vectorizer = joblib.load("models/tfidf_vectorizer.pkl")
