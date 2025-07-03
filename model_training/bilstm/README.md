# 🧠 BiLSTM Híbrido - Detector de Toxicidad

**F1-Score: 0.995 | Accuracy: 99%**

## 🔧 Transformaciones para Datos de YouTube

### 1. Calcular 33 Features Numéricas
```python
features = feature_extractor.extract_comprehensive_features([comment])
features_norm = feature_extractor.normalize_features(features, fit=False)
```

### 2. Tokenizar Texto
```python
sequence, _ = processor.text_to_sequence_advanced(comment)
```

### 3. Convertir a Tensores
```python
text_tensor = torch.tensor(sequence).unsqueeze(0)
features_tensor = torch.tensor(features_norm[0]).unsqueeze(0)
```

## 📝 Uso

```python
def predict_toxicity(comment):
    features = feature_extractor.extract_comprehensive_features([comment])
    features_norm = feature_extractor.normalize_features(features, fit=False)
    sequence, _ = processor.text_to_sequence_advanced(comment)
    
    text_tensor = torch.tensor(sequence).unsqueeze(0)
    features_tensor = torch.tensor(features_norm[0]).unsqueeze(0)
    
    with torch.no_grad():
        prediction = model(text_tensor, features_tensor)
        return prediction.item() > 0.5
```

## ⚠️ Requisitos

```python
# Cargar componentes entrenados
checkpoint = torch.load('bilstm_hybrid_trained_model.pth')
model.load_state_dict(checkpoint['model_state_dict'])
processor = checkpoint['processor']
feature_extractor = checkpoint['feature_extractor']
```

```bash
pip install torch spacy scikit-learn
python -m spacy download en_core_web_sm
```

## 🎯 Limitaciones

- Solo inglés
- Vocabulario fijo (2,038 palabras)
- Longitud óptima: 10-500 caracteres
