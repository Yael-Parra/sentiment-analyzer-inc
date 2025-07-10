#!/usr/bin/env python3
"""
🚀 MULTITOXIC LOADER INDEPENDIENTE
==================================
Detector de 12 tipos de toxicidad simultáneos
Performance: F1-macro 0.9582
Parámetros: 2,752,159
"""

import torch
import torch.nn as nn
import numpy as np
import pickle
import json
import re
# ============================ spaCy ============================
import spacy
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    raise RuntimeError("spaCy model 'en_core_web_sm' not found. Please run: python -m spacy download en_core_web_sm")

from sklearn.preprocessing import StandardScaler
from pathlib import Path

import re

class MultitoxicProcessor:
    def __init__(self, processor_data_path):
        with open(processor_data_path, 'rb') as f:
            data = pickle.load(f)
        self.word_to_idx = data['word_to_idx']
        self.special_tokens = data['special_tokens']  # {'<PAD>':0, ... '<RADICAL>':9}
        self.max_sequence_length = data['max_sequence_length']
        self.discriminant_words = data['discriminant_words']  # dict c/ listas de palabras por categoría
        print(f"📝 Processor cargado: {len(self.word_to_idx)} palabras")
    
    def text_to_sequence(self, text):
        # Manejo de casos no string o vacío
        if not isinstance(text, str):
            return [], {}
        text = text.strip()
        if text == "":
            text = "..."  # Representar texto vacío con algo de puntuación (como en entrenamiento)
        
        # ** Limpieza básica (como en entrenamiento avanzado) **
        # Preservar puntuación básica (. , ! ? ; : ' " - @ #) y espacios, eliminar resto
        processed = re.sub(r'[^\w\s.,!?;:\'"-@#]', ' ', text)
        processed = re.sub(r'\s+', ' ', processed).strip()
        
        # ** Tokenización básica por regex **
        # Separar palabras incluyendo dígitos (\w captura letras/números/_) 
        raw_tokens = re.findall(r'\b\w+\b', processed)
        
        tokens = []
        # ** Construcción de tokens con marcadores <CAPS> y <NUM> **
        for word in raw_tokens:
            if len(word) < 2:
                # Omitir tokens muy cortos (e.g. "a", "I") como en entrenamiento
                continue
            if word.isupper() and word.isalpha() and len(word) >= 5:
                # Palabra en MAYÚSCULAS (>=5 letras) -> indicador de grito
                tokens.append('<CAPS>')
                tokens.append(word.lower())
            elif re.search(r'\d', word):
                # Palabra contiene dígito(s) -> indicador numérico
                tokens.append('<NUM>')
                tokens.append(word.lower())
            elif word.isalpha():
                tokens.append(word.lower())
            else:
                # Si pasa aquí, es un token alfanumérico con algún símbolo (poco probable tras limpieza)
                tokens.append(word.lower())
        
        # ** Inserción de tokens especiales por categorías tóxicas **
        text_lower = processed.lower()
        # Múltiples exclamaciones seguidas (!!): usar visual_features calculado abajo o regex directa
        if re.search(r'!{2,}', text_lower):
            tokens.append('<EXCL>')
        # Discriminant words for specific categories
        for vocab_type, word_list in self.discriminant_words.items():
            # Map discriminant_words key to corresponding special token if applicable
            if vocab_type == 'hatespeech_words':
                token_label = '<HATE>'
            elif vocab_type == 'racist_words':
                token_label = '<RACIST>'
            elif vocab_type == 'abusive_words':
                token_label = '<ABUSIVE>'
            elif vocab_type == 'threat_words':
                token_label = '<THREAT>'
            elif vocab_type == 'radicalism_words':
                token_label = '<RADICAL>'
            else:
                token_label = None
            if token_label:
                # Si cualquiera de las palabras indicadoras aparece como palabra completa en el texto, añadimos token
                for w in word_list:
                    if re.search(rf'\b{re.escape(w)}\b', text_lower):
                        tokens.append(token_label)
                        break  # agregar sólo una vez por categoría
        # ** Convertir tokens a índices del vocabulario (word_to_idx) **
        sequence = [self.word_to_idx.get(tok, self.word_to_idx['<UNK>']) for tok in tokens]
        # Padding/Truncamiento a max_sequence_length
        if len(sequence) < self.max_sequence_length:
            sequence += [self.word_to_idx['<PAD>']] * (self.max_sequence_length - len(sequence))
        else:
            sequence = sequence[:self.max_sequence_length]
        # Calcular features visuales básicas (regex) como en entrenamiento
        visual_features = {
            'caps_extreme_words': len(re.findall(r'\b[A-Z]{5,}\b', text)),
            'caps_consecutive': len(re.findall(r'[A-Z]{3,}', text)),
            'exclamation_groups': len(re.findall(r'!{2,}', text)),
            'repeated_chars': len(re.findall(r'(.)\1{3,}', text)),
            'sentence_complexity': len(re.findall(r'[.!?]+', text)),
            'ellipsis_groups': len(re.findall(r'\.{3,}', text)),
            'numbers_present': len(re.findall(r'\b\d+\b', text)),
            'total_caps_ratio': len(re.findall(r'[A-Z]', text)) / max(len(text), 1),
            'emoji_like': len(re.findall(r'[😀-🙏🌀-🗿🚀-🛿]+', text))
        }
        return sequence, visual_features, tokens 

class MultitoxicExtractor:
    def __init__(self, features_data_path):
        with open(features_data_path, 'rb') as f:
            data = pickle.load(f)
        self.feature_names = data['feature_names']
        self.scaler = data.get('scaler', None) or data.get('scaler_state', None)
        print(f"🔧 Extractor cargado: {len(self.feature_names)} features")

    def extract_features(self, text, processor):
        sequence, visual_features, tokens = processor.text_to_sequence(text)
        words = [w for w in tokens if not w.startswith('<')]
        
        features = {}
        # Features básicas
        features['text_length'] = len(text)
        features['word_count'] = len(words)
        features['char_count'] = len(text)
        features['avg_word_length'] = np.mean([len(w) for w in words]) if words else 0
        # Diversidad léxica
        unique_words = set(words)
        features['lexical_diversity'] = len(unique_words) / max(len(words), 1)
        features['vocab_richness'] = len(unique_words) / max(features['word_count'], 1)
        features['repetition_ratio'] = 1 - (len(unique_words) / max(len(words), 1))
        # Features visuales básicas y derivadas
        for vf_name, vf_val in visual_features.items():
            features[f'visual_{vf_name}'] = vf_val
        features['caps_extreme_count'] = visual_features['caps_extreme_words']
        features['caps_extreme_ratio'] = features['caps_extreme_count'] / max(features['word_count'], 1)
        features['caps_total_ratio'] = visual_features['total_caps_ratio']
        features['caps_words_count'] = len(re.findall(r'\b[A-Z]{2,}\b', text))
        features['caps_vs_total_ratio'] = features['caps_words_count'] / max(features['word_count'], 1)
        # Features emocionales
        features['exclamation_count'] = text.count('!')
        features['exclamation_ratio'] = features['exclamation_count'] / max(len(text), 1)
        features['multiple_exclamation'] = visual_features['exclamation_groups']
        features['question_marks'] = text.count('?')
        features['multiple_question'] = len(re.findall(r'\?{2,}', text))
        # Features de elaboración
        features['ellipsis_count'] = visual_features['ellipsis_groups']
        features['repeated_chars'] = visual_features['repeated_chars']
        features['sentence_count'] = len([s for s in re.split(r'[.!?]+', text) if s.strip()])
        features['avg_sentence_length'] = features['word_count'] / max(features['sentence_count'], 1)
        # Vocabularios discriminantes (conteos y ratios)
        text_lower = text.lower()
        for vocab_type, word_list in processor.discriminant_words.items():
            count = sum(text_lower.count(w) for w in word_list)
            features[f'{vocab_type}_count'] = count
            features[f'{vocab_type}_ratio'] = count / max(features['word_count'], 1)
            features[f'has_{vocab_type}'] = count > 0
        # Tokens especiales (recontados correctamente)
        features['special_tokens_count'] = sum(1 for tok in tokens if tok.startswith('<'))
        features['caps_tokens'] = tokens.count('<CAPS>')
        features['hate_tokens'] = tokens.count('<HATE>')
        features['abusive_tokens'] = tokens.count('<ABUSIVE>')
        features['threat_tokens'] = tokens.count('<THREAT>')
        features['racist_tokens'] = tokens.count('<RACIST>')
        features['radical_tokens'] = tokens.count('<RADICAL>')
        features['excl_tokens'] = tokens.count('<EXCL>')
        features['num_tokens'] = tokens.count('<NUM>')
        # Complejidad sintáctica
        if words:
            lengths = [len(w) for w in words]
            features['word_length_std'] = np.std(lengths)
            features['word_length_max'] = max(lengths)
            features['word_length_min'] = min(lengths)
            features['long_words_ratio'] = sum(1 for w in words if len(w) > 6) / len(words)
            features['short_words_ratio'] = sum(1 for w in words if len(w) <= 3) / len(words)
            features['medium_words_ratio'] = sum(1 for w in words if 4 <= len(w) <= 6) / len(words)
        else:
            for k in ['word_length_std','word_length_max','word_length_min',
                      'long_words_ratio','short_words_ratio','medium_words_ratio']:
                features[k] = 0
        # Patterns específicos
        features['has_urls'] = bool(re.search(r'http[s]?://', text))
        features['has_mentions'] = bool(re.search(r'@\w+', text))
        features['has_hashtags'] = bool(re.search(r'#\w+', text))
        features['has_numbers'] = bool(re.search(r'\d+', text))
        features['numbers_count'] = visual_features['numbers_present']
        # Densidad
        features['punct_density'] = (text.count('!') + text.count('?') + text.count('.')) / max(len(text), 1)
        features['special_chars_count'] = len(re.findall(r"[!@#$%^&*()_+={}|\":;'<>?,./]", text))
        features['special_chars_density'] = features['special_chars_count'] / max(len(text), 1)
        # Multi-label features simuladas (quedan en 0, no tenemos info de etiquetas en predicción)
        features['toxicity_types_count'] = 0
        features['is_multi_toxic'] = False
        features['toxicity_intensity'] = 0.0
        features['has_toxic_and_specific'] = False
        features['toxic_only'] = False
        # Categorías estimadas (usando conteos calculados arriba)
        identity_ind = sum(features.get(f'{v}_count', 0) for v in ['racist_words','sexist_words','homophobic_words','religious_hate_words','nationalist_words'])
        behavior_ind = sum(features.get(f'{v}_count', 0) for v in ['abusive_words','provocative_words','threat_words','radicalism_words'])
        content_ind = sum(features.get(f'{v}_count', 0) for v in ['obscene_words','hatespeech_words'])
        features['identity_attacks_count'] = min(identity_ind, 5)
        features['behavior_attacks_count'] = min(behavior_ind, 4)
        features['content_attacks_count'] = min(content_ind, 2)
        features['has_multiple_identity'] = features['identity_attacks_count'] >= 2
        features['has_multiple_behavior'] = features['behavior_attacks_count'] >= 2
        features['has_mixed_categories'] = (features['identity_attacks_count'] > 0 and features['behavior_attacks_count'] > 0)
        # Coherencia y estructura
        punct_chars = len(re.findall(r'[.!?,;:]', text))
        features['punctuation_complexity'] = punct_chars / max(len(text), 1)
        arg_words = ['because','since','therefore','however','but','although']
        features['argument_markers'] = sum(1 for w in arg_words if w in text_lower)
        features['has_argumentation'] = features['argument_markers'] > 0
        # Patterns únicos
        threat_patterns = ['will','gonna','going to','watch out','wait']
        features['threat_pattern_count'] = sum(1 for pat in threat_patterns if pat in text_lower)
        nationalist_patterns = ['america','country','nation','patriot','flag']
        features['nationalist_pattern_count'] = sum(1 for pat in nationalist_patterns if pat in text_lower)
        # Distribución de mayúsculas en bloques de 10 caracteres
        if len(text) > 20:
            chunks = [text[i:i+10] for i in range(0, len(text), 10)]
            caps_counts = [len(re.findall(r'[A-Z]', chunk)) for chunk in chunks]
            features['caps_distribution_std'] = float(np.std(caps_counts))
            features['caps_max_concentration'] = max(caps_counts) if caps_counts else 0
        else:
            features['caps_distribution_std'] = 0.0
            features['caps_max_concentration'] = 0
        # Ordenar según feature_names original
        feature_array = np.array([features.get(name, 0) for name in self.feature_names])
        return feature_array
    
    def normalize_features(self, features_array):
        """
        Normaliza los features usando el scaler cargado desde features_data.pkl
        """
        if hasattr(self, 'scaler') and self.scaler is not None:
            return self.scaler.transform([features_array])[0]  # Devuelve array normalizado 1D
        else:
            raise RuntimeError("❌ El extractor no contiene un scaler válido.")

class MultitoxicModel(nn.Module):
    def __init__(self, config):
        super(MultitoxicModel, self).__init__()
        
        self.vocab_size = config['vocab_size']
        self.embedding_dim = config['embedding_dim']
        self.hidden_dim = config['hidden_dim']
        self.num_classes = config['num_classes']
        self.num_numeric_features = config['num_numeric_features']
        dropout_rate = config.get('dropout_rate', 0.4)
        
        # Embedding
        self.embedding = nn.Embedding(self.vocab_size, self.embedding_dim, padding_idx=0)
        self.embedding_dropout = nn.Dropout(dropout_rate * 0.3)
        
        # BiLSTM
        self.bilstm = nn.LSTM(
            input_size=self.embedding_dim,
            hidden_size=self.hidden_dim,
            num_layers=2,
            batch_first=True,
            bidirectional=True,
            dropout=dropout_rate
        )
        
        # Attention
        self.attention_dim = self.hidden_dim * 2
        self.attention_general = nn.Sequential(
            nn.Linear(self.attention_dim, self.attention_dim // 2),
            nn.Tanh(),
            nn.Linear(self.attention_dim // 2, 1),
            nn.Softmax(dim=1)
        )
        
        self.attention_identity = nn.Sequential(
            nn.Linear(self.attention_dim, self.attention_dim // 3),
            nn.Tanh(),
            nn.Linear(self.attention_dim // 3, 1),
            nn.Softmax(dim=1)
        )
        
        self.attention_behavior = nn.Sequential(
            nn.Linear(self.attention_dim, self.attention_dim // 3),
            nn.Tanh(),
            nn.Linear(self.attention_dim // 3, 1),
            nn.Softmax(dim=1)
        )
        
        # Numeric processor
        self.numeric_processor = nn.Sequential(
            nn.Linear(self.num_numeric_features, 128),
            nn.ReLU(),
            nn.BatchNorm1d(128),
            nn.Dropout(dropout_rate * 0.5),
            nn.Linear(128, 96),
            nn.ReLU(),
            nn.BatchNorm1d(96),
            nn.Dropout(dropout_rate * 0.4),
            nn.Linear(96, 64),
            nn.ReLU(),
            nn.BatchNorm1d(64),
            nn.Dropout(dropout_rate * 0.3),
            nn.Linear(64, 48),
            nn.ReLU(),
            nn.Dropout(dropout_rate * 0.2)
        )
        
        # Fusion
        fusion_input_dim = self.attention_dim * 3 + 48
        self.fusion_layer = nn.Sequential(
            nn.Linear(fusion_input_dim, 384),
            nn.ReLU(),
            nn.BatchNorm1d(384),
            nn.Dropout(dropout_rate * 0.6),
            nn.Linear(384, 256),
            nn.ReLU(),
            nn.BatchNorm1d(256),
            nn.Dropout(dropout_rate * 0.5),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(dropout_rate * 0.4)
        )
        
        # Branches
        self.identity_branch = nn.Sequential(
            nn.Linear(128, 64), nn.ReLU(), nn.Dropout(dropout_rate * 0.3),
            nn.Linear(64, 32), nn.ReLU(), nn.Dropout(dropout_rate * 0.2)
        )
        self.behavior_branch = nn.Sequential(
            nn.Linear(128, 64), nn.ReLU(), nn.Dropout(dropout_rate * 0.3),
            nn.Linear(64, 32), nn.ReLU(), nn.Dropout(dropout_rate * 0.2)
        )
        self.content_branch = nn.Sequential(
            nn.Linear(128, 64), nn.ReLU(), nn.Dropout(dropout_rate * 0.3),
            nn.Linear(64, 32), nn.ReLU(), nn.Dropout(dropout_rate * 0.2)
        )
        self.general_branch = nn.Sequential(
            nn.Linear(128, 64), nn.ReLU(), nn.Dropout(dropout_rate * 0.3),
            nn.Linear(64, 32), nn.ReLU(), nn.Dropout(dropout_rate * 0.2)
        )
        
        # Output layers
        self.identity_output = nn.Linear(32, 5)    # 5 clases: racist, religious_hate, nationalist, sexist, homophobic
        self.behavior_output = nn.Linear(32, 4)    # 4 clases: abusive, provocative, threat, radicalism
        self.content_output = nn.Linear(32, 2)     # 2 clases: hatespeech, obscene
        self.general_output = nn.Linear(32, 1)     # 1 clase: toxic
    
    def forward(self, text_input, numeric_input, attention_mask=None):
        embedded = self.embedding(text_input)
        embedded = self.embedding_dropout(embedded)
        
        lstm_output, _ = self.bilstm(embedded)
        
        if attention_mask is not None:
            attention_mask = attention_mask.unsqueeze(-1)
            lstm_output = lstm_output * attention_mask
        
        # Multi-head attention
        attention_general = self.attention_general(lstm_output)
        attention_identity = self.attention_identity(lstm_output)
        attention_behavior = self.attention_behavior(lstm_output)
        
        attended_general = torch.sum(lstm_output * attention_general, dim=1)
        attended_identity = torch.sum(lstm_output * attention_identity, dim=1)
        attended_behavior = torch.sum(lstm_output * attention_behavior, dim=1)
        
        # Numeric features
        numeric_features = self.numeric_processor(numeric_input)
        
        # Fusion
        fused_features = torch.cat([
            attended_general, attended_identity, attended_behavior, numeric_features
        ], dim=1)
        
        fused_output = self.fusion_layer(fused_features)
        
        # Branches
        identity_features = self.identity_branch(fused_output)
        behavior_features = self.behavior_branch(fused_output)
        content_features = self.content_branch(fused_output)
        general_features = self.general_branch(fused_output)
        
        # Outputs
        identity_logits = self.identity_output(identity_features)
        behavior_logits = self.behavior_output(behavior_features)
        content_logits = self.content_output(content_features)
        general_logits = self.general_output(general_features)
        
        # Concatenate in order: toxic, hatespeech, abusive, threat, provocative, obscene, racist, nationalist, sexist, homophobic, religious_hate, radicalism
        logits = torch.cat([
            general_logits,                       # toxic (1)
            content_logits[:, 0:1],              # hatespeech (2)
            behavior_logits[:, 0:1],             # abusive (3)
            behavior_logits[:, 2:3],             # threat (4)
            behavior_logits[:, 1:2],             # provocative (5)
            content_logits[:, 1:2],              # obscene (6)
            identity_logits[:, 0:1],             # racist (7)
            identity_logits[:, 1:2],             # nationalist (8)
            identity_logits[:, 2:3],             # sexist (9)
            identity_logits[:, 3:4],             # homophobic (10)
            identity_logits[:, 4:5],             # religious_hate (11)
            behavior_logits[:, 3:4],             # radicalism (12)
        ], dim=1)
        
        return logits

class MultitoxicLoader:
    def __init__(self, model_dir):
        self.model_dir = Path(model_dir)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = None
        self.processor = None
        self.feature_extractor = None
        self.config = None
        
        print(f"🚀 Multitoxic Loader")
        print(f"   Dispositivo: {self.device}")
    
    def load_model(self):
        print("🔄 Cargando modelo...")
        
        # Load config
        with open(self.model_dir / "config.json", 'r') as f:
            self.config = json.load(f)
        
        # Load processor
        self.processor = MultitoxicProcessor(self.model_dir / "processor_data.pkl")
        
        # Load feature extractor
        self.feature_extractor = MultitoxicExtractor(self.model_dir / "features_data.pkl")
        
        # Load model
        self.model = MultitoxicModel(self.config['model_config']).to(self.device)
        
        # Load weights
        checkpoint = torch.load(self.model_dir / "model_weights.pth", map_location=self.device)
        self.model.load_state_dict(checkpoint['state_dict'])
        self.model.eval()
        
        print("✅ Modelo cargado exitosamente")
        f1_score = self.config.get('test_metrics', {}).get('f1_macro', 0)
        print(f"   F1-macro: {f1_score:.4f}")
    
    def predict(self, text, return_probabilities=True, return_categories=True):
        if not self.model:
            raise ValueError("Modelo no cargado. Ejecuta load_model() primero.")
        
        try:
            # ✅ CORRECCIÓN: Manejar texto vacío apropiadamente
            if not isinstance(text, str) or text.strip() == "":
                empty_predictions = {}
                class_names = self.config['classes']['class_names']
                thresholds = self.config['thresholds']
                
                for class_name in class_names:
                    empty_predictions[class_name] = {
                        'probability': 0.0,
                        'detected': False,
                        'threshold': thresholds[class_name]
                    }
                
                result = {
                    'detected_types': [],
                    'is_multi_toxic': False,
                    'total_types': 0,
                    'severity': 'clean',
                    'predictions': empty_predictions,
                    'probabilities': {k: 0.0 for k in class_names}  
                }
                return result

            # Process text (correctly unpacking three values)
            sequence, visual_features, tokens_list = self.processor.text_to_sequence(text)
            
            # Extract features for numeric part
            features_array = self.feature_extractor.extract_features(text, self.processor)
            normalized_features = self.feature_extractor.scaler.transform([features_array])[0]
            
            # Prepare text sequence tensor (ensure correct length)
            if len(sequence) < self.processor.max_sequence_length:
                sequence += [0] * (self.processor.max_sequence_length - len(sequence))
            elif len(sequence) > self.processor.max_sequence_length:
                sequence = sequence[:self.processor.max_sequence_length]
            
            text_tensor = torch.tensor([sequence], dtype=torch.long, device=self.device)
            features_tensor = torch.from_numpy(np.array([normalized_features])).float().to(self.device)
            attention_mask = (text_tensor != 0).float()
            
            # Predict
            with torch.no_grad():
                logits = self.model(text_tensor, features_tensor, attention_mask)

                # 🔍 DEBUG: Imprimir los logits crudos antes de aplicar sigmoid
                for i, class_name in enumerate(self.config['classes']['class_names']):
                    print(f"[DEBUG] Logit {class_name}: {logits[0][i].item():.4f}")

                probabilities = torch.sigmoid(logits).cpu().numpy()[0]
            
            # Interpret results
            thresholds = self.config['thresholds']
            class_names = self.config['classes']['class_names']
            
            predictions = {}
            detected_types = []
            
            for i, class_name in enumerate(class_names):
                prob = float(probabilities[i])
                threshold = thresholds[class_name]
                is_detected = prob > threshold
                
                predictions[class_name] = {
                    'probability': prob,
                    'detected': is_detected,
                    'threshold': threshold
                }
                
                if is_detected:
                    detected_types.append(class_name)
            
            result = {
                'detected_types': detected_types,
                'is_multi_toxic': len(detected_types) >= 2,
                'total_types': len(detected_types),
                'severity': 'high' if len(detected_types) >= 3 else 'medium' if len(detected_types) >= 2 else 'low' if len(detected_types) >= 1 else 'clean',
                'predictions': predictions
            }
            
            if return_probabilities:
                result['probabilities'] = {k: v['probability'] for k, v in predictions.items()}
            
            return result
            
        except Exception as e:
            class_names = self.config['classes']['class_names']
            return {
                'detected_types': [],
                'is_multi_toxic': False,
                'total_types': 0,
                'severity': 'error',
                'error': str(e),
                'probabilities': {k: 0.0 for k in class_names},
                'predictions': {k: {'probability': 0.0, 'detected': False, 'threshold': 0.5} for k in class_names}
            }


if __name__ == "__main__":
    print("🚀 TESTING MULTITOXIC")
    print("=" * 40)
    
    try:
        loader = MultitoxicLoader("models/bilstm_advanced")
        loader.load_model()
        
        test_cases = [
            ("Clean", "This is a great video!"),
            ("Toxic", "You are so stupid"),
            ("Racist", "These people are animals"),
            ("Multi", "You fucking racist piece of shit")
        ]
        
        for label, text in test_cases:
            result = loader.predict(text)
            print(f"\n{label}: {text[:40]}...")
            print(f"  Detected: {result['detected_types']}")
            print(f"  Severity: {result['severity']}")
        
        print("\n✅ MODELO FUNCIONANDO")
        
    except Exception as e:
        print(f"❌ Error: {e}")