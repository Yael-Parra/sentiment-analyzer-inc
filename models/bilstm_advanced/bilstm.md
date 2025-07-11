## 🚀 **Modelo MULTITOXIC - Guía de Implementación (Actualizada)**

### **Información del Modelo**

- **Performance:** F1-macro 95.16%
- **Tipos detectados:** 12 tipos de toxicidad simultáneos
- **Input:** Comentarios de YouTube en inglés
- **Output:** 24 valores (12 probabilidades + 12 booleanos)

---

### **Tipos de Toxicidad**

1. `toxic` - Toxicidad general
2. `hatespeech` - Discurso de odio
3. `abusive` - Lenguaje abusivo
4. `provocative` - Contenido provocativo
5. `racist` - Contenido racista
6. `obscene` - Lenguaje obsceno
7. `threat` - Amenazas
8. `religious_hate` - Odio religioso
9. `nationalist` - Nacionalismo extremo
10. `sexist` - Ataques de género
11. `homophobic` - Homofobia
12. `radicalism` - Extremismo

---

### **Archivos del Modelo**

#### **Archivos Obligatorios (4)**

#### 1. `multitoxic_v1.0_XXXXXX_config.json`
- **Uso:** Configuración inicial del pipeline
- **Contiene:** Arquitectura, thresholds, nombres de clases
- **Cuándo:** Al inicializar el servicio (una vez)

#### 2. `multitoxic_v1.0_XXXXXX_processor.pkl`
- **Uso:** Procesar texto → tokens numéricos
- **Contiene:** Vocabulario (2,785 palabras), tokenizador
- **Cuándo:** Para cada comentario (paso 1)

#### 3. `multitoxic_v1.0_XXXXXX_features.pkl`
- **Uso:** Extraer 84 características numéricas
- **Contiene:** Extractor + StandardScaler entrenado
- **Cuándo:** Para cada comentario (paso 2)

#### 4. `multitoxic_v1.0_XXXXXX_model.pth`
- **Uso:** Hacer predicción final
- **Contiene:** Red neuronal entrenada (3.13M parámetros)
- **Cuándo:** Para cada comentario (paso 3)

#### **Archivo Opcional**

#### 5. `multitoxic_v1.0_XXXXXX_loader.py`
- **Uso:** Clase que integra todo automáticamente
- **Alternativa:** Implementar manualmente los 4 pasos

---

### **Requisitos del Sistema**

```bash
# Dependencias obligatorias
pip install torch numpy pandas scikit-learn dill tqdm

# Hardware mínimo
# RAM: 4GB, Almacenamiento: 100MB, CPU/GPU: ambos soportados
```

---

### Usar Loader Automático (Recomendado)**

#### **Inicialización (una vez al arrancar)**

```python
from models.bilstm_advanced.multitoxic_v1.0_XXXXXX_loader import MultitoxicLoader

# Cargar modelo completo automáticamente
loader = MultitoxicLoader("./models/bilstm_advanced")
loader.load_model()  # Busca automáticamente la versión más reciente
```

#### **Predicción (por cada comentario)**

```python
def predecir_toxicidad(texto_youtube):
    # Todo automático en una línea
    resultado = loader.predict(
        texto_youtube, 
        return_probabilities=True,
        return_categories=True,
        return_details=False
    )
    
    # Extraer datos para base de datos
    db_data = {}
    
    # 12 probabilidades
    for tipo, prob in resultado['probabilities'].items():
        db_data[f'{tipo}_probability'] = prob
    
    # 12 booleanos
    for tipo in resultado['probabilities'].keys():
        db_data[f'is_{tipo}'] = tipo in resultado['detected_types']
    
    resultado['database_ready'] = db_data
    return resultado
```
--

## Pipeline YouTube → Base de Datos

### Flujo Completo

```python
# 1. Extraer comentarios de YouTube
comentarios = youtube_extractor.get_comments(video_id)

# 2. Procesar cada comentario
resultados = []
for comentario in comentarios:
    # NO limpiar el texto (preservar emojis, @mentions, #hashtags)
    texto_original = comentario['text']
    
    # Predecir toxicidad
    prediccion = predecir_toxicidad(texto_original)
    
    # Preparar para BD
    datos_bd = {
        'comment_id': comentario['id'],
        'original_text': texto_original,
        **prediccion  # Las 24 columnas del modelo
    }
    
    resultados.append(datos_bd)

# 3. Guardar en base de datos
for datos in resultados:
    db.insert('toxicity_predictions', datos)
```

### Preprocesamiento del Texto

**✅ El modelo hace esto AUTOMÁTICAMENTE:**
- Analiza emojis (los cuenta como feature)
- Detecta @menciones y #hashtags (los cuenta)
- Preserva mayúsculas (importantes para agresividad)
- Analiza puntuación (¡¡¡ ??? son críticos)
- Extrae 84 características numéricas
- Normaliza con StandardScaler

**❌ NO hagas esto al texto:**
- NO eliminar emojis, @menciones, #hashtags
- NO convertir todo a minúsculas
- NO quitar signos de puntuación
- NO filtrar palabras "malas"

**✅ Limpieza opcional permitida:**
- Recortar espacios extras
- Truncar si > 10,000 caracteres

---

## Output para Base de Datos

### 24 Columnas Requeridas

**12 Probabilidades (DECIMAL(5,4)):**
```sql
toxic_probability       DECIMAL(5,4)    -- ej: 0.8547
hatespeech_probability  DECIMAL(5,4)    -- ej: 0.1234
abusive_probability     DECIMAL(5,4)    -- ej: 0.6789
provocative_probability DECIMAL(5,4)    -- ej: 0.0567
racist_probability      DECIMAL(5,4)    -- ej: 0.0123
obscene_probability     DECIMAL(5,4)    -- ej: 0.4321
threat_probability      DECIMAL(5,4)    -- ej: 0.0089
religious_hate_probability DECIMAL(5,4) -- ej: 0.0156
nationalist_probability DECIMAL(5,4)    -- ej: 0.0234
sexist_probability      DECIMAL(5,4)    -- ej: 0.0345
homophobic_probability  DECIMAL(5,4)    -- ej: 0.0198
radicalism_probability  DECIMAL(5,4)    -- ej: 0.0076
```

**12 Booleanos (BOOLEAN):**
```sql
is_toxic            BOOLEAN    -- ej: true (si prob > 0.5)
is_hatespeech       BOOLEAN    -- ej: false (si prob > 0.4)
is_abusive          BOOLEAN    -- ej: true (si prob > 0.4)
is_provocative      BOOLEAN    -- ej: false (si prob > 0.6)
is_racist           BOOLEAN    -- ej: false (si prob > 0.3)
is_obscene          BOOLEAN    -- ej: false (si prob > 0.5)
is_threat           BOOLEAN    -- ej: false (si prob > 0.2)
is_religious_hate   BOOLEAN    -- ej: false (si prob > 0.3)
is_nationalist      BOOLEAN    -- ej: false (si prob > 0.4)
is_sexist           BOOLEAN    -- ej: false (si prob > 0.3)
is_homophobic       BOOLEAN    -- ej: false (si prob > 0.3)
is_radicalism       BOOLEAN    -- ej: false (si prob > 0.2)
```

### Thresholds Optimizados

```python
thresholds = {
    'threat': 0.2,           # Muy estricto
    'radicalism': 0.2,       # Muy estricto
    'racist': 0.3,           # Estricto
    'sexist': 0.3,           # Estricto
    'homophobic': 0.3,       # Estricto
    'religious_hate': 0.3,   # Estricto
    'hatespeech': 0.4,       # Moderado
    'abusive': 0.4,          # Moderado
    'nationalist': 0.4,      # Moderado
    'obscene': 0.5,          # Moderado
    'toxic': 0.5,            # Moderado
    'provocative': 0.6       # Permisivo
}
```

---

## Ejemplo Completo

### Input: Comentario de YouTube
```python
comentario = {
    'id': 'abc123',
    'text': 'This video is stupid and you are an idiot 🤡 @creator'
}
```

### Output: Datos para BD
```python
{
    'comment_id': 'abc123',
    'original_text': 'This video is stupid and you are an idiot 🤡 @creator',
    
    # 12 probabilidades
    'toxic_probability': 0.8547,
    'hatespeech_probability': 0.1234,
    'abusive_probability': 0.6789,
    'provocative_probability': 0.0567,
    'racist_probability': 0.0123,
    'obscene_probability': 0.4321,
    'threat_probability': 0.0089,
    'religious_hate_probability': 0.0156,
    'nationalist_probability': 0.0234,
    'sexist_probability': 0.0345,
    'homophobic_probability': 0.0198,
    'radicalism_probability': 0.0076,
    
    # 12 booleanos
    'is_toxic': True,              # 0.8547 > 0.5
    'is_hatespeech': False,        # 0.1234 < 0.4
    'is_abusive': True,            # 0.6789 > 0.4
    'is_provocative': False,       # 0.0567 < 0.6
    'is_racist': False,            # 0.0123 < 0.3
    'is_obscene': False,           # 0.4321 < 0.5
    'is_threat': False,            # 0.0089 < 0.2
    'is_religious_hate': False,    # 0.0156 < 0.3
    'is_nationalist': False,       # 0.0234 < 0.4
    'is_sexist': False,            # 0.0345 < 0.3
    'is_homophobic': False,        # 0.0198 < 0.3
    'is_radicalism': False         # 0.0076 < 0.2
}
```

---

## Performance y Limitaciones

### Limitaciones
- Solo funciona en **inglés**
- Optimizado para **comentarios de YouTube**
- Puede fallar con **sarcasmo** muy sutil
- No considera **contexto** entre comentarios

### Casos Especiales
- **Texto vacío:** Devuelve todas las probabilidades en 0.0
- **Texto muy largo:** Se trunca a 10,000 caracteres
- **Solo emojis:** Se procesa normalmente

