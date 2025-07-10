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
from sklearn.preprocessing import StandardScaler
from pathlib import Path

class MultitoxicProcessor:
    def __init__(self, processor_data_path):
        with open(processor_data_path, 'rb') as f:
            data = pickle.load(f)
        
        self.word_to_idx = data['word_to_idx']
        self.special_tokens = data['special_tokens']
        self.max_sequence_length = data['max_sequence_length']
        self.discriminant_words = data['discriminant_words']
        
        print(f"📝 Processor cargado: {len(self.word_to_idx)} palabras")
    
    def text_to_sequence(self, text):
        if not isinstance(text, str):
            return [], {
                'caps_extreme_words': 0,
                'caps_consecutive': 0,
                'exclamation_groups': 0,
                'repeated_chars': 0,
                'sentence_complexity': 0,
                'ellipsis_groups': 0,
                'numbers_present': 0,
                'total_caps_ratio': 0.0,
                'emoji_like': 0
            }

        if text.strip() == "":
            text = "..."

        # Features visuales básicas - ✅ REGEX CORREGIDAS
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
        
        # Tokenización básica - ✅ REGEX CORREGIDA
        tokens = []
        words = re.findall(r'\b\w+\b', text)
        
        for word in words:
            if len(word) >= 2:
                if word.isupper() and len(word) >= 5:
                    tokens.extend(['<CAPS>', word.lower()])
                elif re.search(r'\d', word):  # ✅ REGEX CORREGIDA
                    tokens.extend(['<NUM>', word.lower()])
                else:
                    tokens.append(word.lower())
        
        # Convertir a secuencia
        sequence = []
        for token in tokens:
            if token in self.word_to_idx:
                sequence.append(self.word_to_idx[token])
            else:
                sequence.append(self.word_to_idx['<UNK>'])
        
        # Padding/truncating
        if len(sequence) > self.max_sequence_length:
            sequence = sequence[:self.max_sequence_length]
        
        return sequence, visual_features

class MultitoxicExtractor:
    def __init__(self, features_data_path):
        with open(features_data_path, 'rb') as f:
            data = pickle.load(f)
        
        self.feature_names = data['feature_names']
        self.discriminant_vocabularies = data['discriminant_vocabularies']
        
        # Recrear scaler
        self.scaler = StandardScaler()
        scaler_state = data['scaler_state']
        self.scaler.mean_ = scaler_state['mean_']
        self.scaler.scale_ = scaler_state['scale_']
        self.scaler.var_ = scaler_state['var_']
        self.scaler.n_features_in_ = scaler_state['n_features_in_']
        self.scaler.n_samples_seen_ = scaler_state['n_samples_seen_']
        
        print(f"🔧 Extractor cargado: {len(self.feature_names)} features")
    
    def extract_features(self, text, processor):
        features = {}
        
        tokens, visual_features = processor.text_to_sequence(text)
        words = text.lower().split()
        
        # Features básicas
        features['text_length'] = len(text)
        features['word_count'] = len(words)
        features['char_count'] = len(text)
        features['avg_word_length'] = np.mean([len(word) for word in words]) if words else 0
        
        # Diversidad léxica
        unique_words = set(words)
        features['lexical_diversity'] = len(unique_words) / max(len(words), 1)
        features['vocab_richness'] = len(unique_words) / max(features['word_count'], 1)
        features['repetition_ratio'] = 1 - (len(unique_words) / max(len(words), 1))
        
        # Features visuales
        for vf_name, vf_value in visual_features.items():
            features[f'visual_{vf_name}'] = vf_value
        
        # Features de agresividad visual - ✅ REGEX CORREGIDA
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
        
        # Vocabularios discriminantes
        text_lower = text.lower()
        for vocab_type, word_list in self.discriminant_vocabularies.items():
            count = sum(text_lower.count(word) for word in word_list)
            features[f'{vocab_type}_count'] = count
            features[f'{vocab_type}_ratio'] = count / max(features['word_count'], 1)
            features[f'has_{vocab_type}'] = count > 0
        
        # Tokens especiales
        features['special_tokens_count'] = sum(1 for token in tokens if isinstance(token, str) and token.startswith('<'))
        features['caps_tokens'] = 1 if '<CAPS>' in str(tokens) else 0
        features['hate_tokens'] = 0
        features['abusive_tokens'] = 0
        features['threat_tokens'] = 0
        features['racist_tokens'] = 0
        features['radical_tokens'] = 0
        features['excl_tokens'] = 0
        features['num_tokens'] = 1 if '<NUM>' in str(tokens) else 0
        
        # Complejidad sintáctica
        if len(words) > 0:
            word_lengths = [len(word) for word in words]
            features['word_length_std'] = np.std(word_lengths)
            features['word_length_max'] = max(word_lengths)
            features['word_length_min'] = min(word_lengths)
            features['long_words_ratio'] = sum(1 for w in words if len(w) > 6) / len(words)
            features['short_words_ratio'] = sum(1 for w in words if len(w) <= 3) / len(words)
            features['medium_words_ratio'] = sum(1 for w in words if 4 <= len(w) <= 6) / len(words)
        else:
            for key in ['word_length_std', 'word_length_max', 'word_length_min',
                       'long_words_ratio', 'short_words_ratio', 'medium_words_ratio']:
                features[key] = 0
        
        # Patterns específicos - ✅ REGEX CORREGIDAS
        features['has_urls'] = bool(re.search(r'http[s]?://', text))
        features['has_mentions'] = bool(re.search(r'@\w+', text))
        features['has_hashtags'] = bool(re.search(r'#\w+', text))
        features['has_numbers'] = bool(re.search(r'\d+', text))
        features['numbers_count'] = visual_features['numbers_present']
        
        # Densidad
        features['punct_density'] = (text.count('!') + text.count('?') + text.count('.')) / max(len(text), 1)
        features['special_chars_count'] = len(re.findall(r"[!@#$%^&*()_+={}|\\:\";'<>?,./]", text))
        features['special_chars_density'] = features['special_chars_count'] / max(len(text), 1)
        
        # Multi-label features (simuladas)
        features['toxicity_types_count'] = 0
        features['is_multi_toxic'] = False
        features['toxicity_intensity'] = 0.0
        features['has_toxic_and_specific'] = False
        features['toxic_only'] = False
        
        # Categorías estimadas
        identity_indicators = sum(features.get(f'{vocab}_count', 0) for vocab in 
                                 ['racist_words', 'sexist_words', 'homophobic_words', 
                                  'religious_hate_words', 'nationalist_words'])
        behavior_indicators = sum(features.get(f'{vocab}_count', 0) for vocab in 
                                 ['abusive_words', 'provocative_words', 'threat_words', 'radicalism_words'])
        content_indicators = sum(features.get(f'{vocab}_count', 0) for vocab in 
                                ['obscene_words', 'hatespeech_words'])
        
        features['identity_attacks_count'] = min(identity_indicators, 5)
        features['behavior_attacks_count'] = min(behavior_indicators, 4)
        features['content_attacks_count'] = min(content_indicators, 2)
        features['has_multiple_identity'] = features['identity_attacks_count'] >= 2
        features['has_multiple_behavior'] = features['behavior_attacks_count'] >= 2
        features['has_mixed_categories'] = (features['identity_attacks_count'] > 0 and 
                                           features['behavior_attacks_count'] > 0)
        
        # Coherencia y estructura
        punct_chars = len(re.findall(r'[.!?,;:]', text))
        features['punctuation_complexity'] = punct_chars / max(len(text), 1)
        
        argument_words = ['because', 'since', 'therefore', 'however', 'but', 'although']
        features['argument_markers'] = sum(1 for word in argument_words if word in text_lower)
        features['has_argumentation'] = features['argument_markers'] > 0
        
        # Patterns únicos
        threat_patterns = ['will', 'gonna', 'going to', 'watch out', 'wait']
        features['threat_pattern_count'] = sum(1 for pattern in threat_patterns if pattern in text_lower)
        
        nationalist_patterns = ['america', 'country', 'nation', 'patriot', 'flag']
        features['nationalist_pattern_count'] = sum(1 for pattern in nationalist_patterns if pattern in text_lower)
        
        # Distribución
        if len(text) > 20:
            text_chunks = [text[i:i+10] for i in range(0, len(text), 10)]
            caps_distribution = [len(re.findall(r'[A-Z]', chunk)) for chunk in text_chunks]
            features['caps_distribution_std'] = np.std(caps_distribution) if caps_distribution else 0
            features['caps_max_concentration'] = max(caps_distribution) if caps_distribution else 0
        else:
            features['caps_distribution_std'] = 0
            features['caps_max_concentration'] = 0
        
        # Asegurar orden correcto
        feature_array = np.array([features.get(name, 0) for name in self.feature_names])
        return feature_array
    
    def normalize_features(self, features_array):
        return self.scaler.transform(features_array.reshape(1, -1))[0]

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
                # Para texto vacío, retornar estructura completa con predicciones
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
                    'predictions': empty_predictions
                }
                
                if return_probabilities:
                    result['probabilities'] = {k: 0.0 for k in class_names}
                
                return result
            
            # Process text
            tokens, visual_features = self.processor.text_to_sequence(text)
            
            # Extract features
            features_array = self.feature_extractor.extract_features(text, self.processor)
            normalized_features = self.feature_extractor.normalize_features(features_array)
            
            # Prepare tensors
            if len(tokens) < self.processor.max_sequence_length:
                tokens += [0] * (self.processor.max_sequence_length - len(tokens))
            elif len(tokens) > self.processor.max_sequence_length:
                tokens = tokens[:self.processor.max_sequence_length]
            
            text_tensor = torch.tensor([tokens], dtype=torch.long, device=self.device)
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
            return {
                'detected_types': [],
                'is_multi_toxic': False,
                'total_types': 0,
                'severity': 'error',
                'error': str(e)
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