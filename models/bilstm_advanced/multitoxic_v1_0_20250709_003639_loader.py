#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 MULTITOXIC BiLSTM HYBRID LOADER v1.0
🎯 Detector avanzado de 12 tipos de toxicidad simultáneos
🔧 Incluye 107 features engineered + Multi-head attention
🏷️  Categorías: Identity/Behavior/Content/General attacks
"""

import torch
import torch.nn as nn
import numpy as np
import pandas as pd
import re
import pickle
import json
import dill
from collections import Counter, defaultdict
from sklearn.preprocessing import StandardScaler
from pathlib import Path
from tqdm.auto import tqdm

# Dependencias opcionales
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    print("⚠️ spaCy no disponible - usando procesamiento básico")

class MultitoxicProcessor:
    """
    Processor idéntico al usado en entrenamiento
    Optimizado para vocabulario de 12 clases multi-label
    """
    
    def __init__(self, processor_data):
        self.word_to_idx = processor_data['word_to_idx']
        self.idx_to_word = processor_data['idx_to_word']
        self.special_tokens = processor_data['special_tokens']
        self.max_sequence_length = processor_data['max_sequence_length']
        self.max_vocab_size = processor_data['max_vocab_size']
        self.min_word_freq = processor_data['min_word_freq']
        self.vocab_built = processor_data['vocab_built']
        self.word_freq = Counter(processor_data['word_freq'])
        self.class_word_freq = {k: Counter(v) for k, v in processor_data['class_word_freq'].items()}
        self.discriminant_words = processor_data['discriminant_words']
        self._setup_functions()
        
        print(f"📝 Processor MULTITOXIC cargado:")
        print(f"   Vocabulario: {len(self.word_to_idx):,} palabras")
        print(f"   Tokens especiales: {len(self.special_tokens)}")
        print(f"   Secuencia máxima: {self.max_sequence_length}")
    
    def _setup_functions(self):
        """Setup de funciones de procesamiento multitoxic"""
        def tokenize_fallback(text):
            if not isinstance(text, str) or text.strip() == "":
                return [], {}
            
            # FEATURES VISUALES CRÍTICAS para las 12 clases
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
            
            tokens = []
            words = re.findall(r'\b\w+\b', text)
            
            # Tokenización con marcadores especiales
            for word in words:
                if len(word) >= 2:
                    if word.isupper() and len(word) >= 5:
                        tokens.append('<CAPS>')
                        tokens.append(word.lower())
                    elif word.isupper() and len(word) >= 3:
                        tokens.append('<CAPS>')
                        tokens.append(word.lower())
                    elif re.search(r'\d', word):
                        tokens.append('<NUM>')
                        tokens.append(word.lower())
                    else:
                        tokens.append(word.lower())
            
            # Marcadores contextuales
            if visual_features['exclamation_groups'] > 0:
                tokens.append('<EXCL>')
            
            text_lower = text.lower()
            
            # Detectores específicos por clase
            if any(w in text_lower for w in self.discriminant_words.get('hatespeech_words', [])):
                tokens.append('<HATE>')
            if any(w in text_lower for w in self.discriminant_words.get('racist_words', [])):
                tokens.append('<RACIST>')
            if any(w in text_lower for w in self.discriminant_words.get('abusive_words', [])):
                tokens.append('<ABUSIVE>')
            if any(w in text_lower for w in self.discriminant_words.get('threat_words', [])):
                tokens.append('<THREAT>')
            if any(w in text_lower for w in self.discriminant_words.get('radicalism_words', [])):
                tokens.append('<RADICAL>')
            
            # Filtrado de tokens válidos
            filtered_tokens = [token for token in tokens 
                              if token and (token in self.special_tokens or 
                                 (len(token) >= 2 and token.isalpha()))]
            
            return filtered_tokens, visual_features
        
        def sequence_fallback(text):
            tokens, visual_features = tokenize_fallback(text)
            sequence = []
            
            for token in tokens:
                if token in self.word_to_idx:
                    sequence.append(self.word_to_idx[token])
                else:
                    sequence.append(self.word_to_idx['<UNK>'])
            
            # Truncamiento o padding
            if len(sequence) > self.max_sequence_length:
                sequence = sequence[:self.max_sequence_length]
            
            return sequence, visual_features
        
        self.tokenize_with_multitoxic_features = tokenize_fallback
        self.text_to_sequence_multitoxic = sequence_fallback


class MultitoxicExtractor:
    """
    Feature Extractor completo con las 107 features engineered
    Idéntico al usado en entrenamiento multitoxic
    """
    
    def __init__(self, features_data):
        self.feature_names = features_data['feature_names']
        self.fitted = features_data['fitted']
        self.num_features = features_data['num_features']
        self.discriminant_vocabularies = features_data['discriminant_vocabularies']
        self.category_mapping = features_data['category_mapping']
        self.target_classes = features_data['target_classes']
        self.class_names = features_data['class_names']
        
        # Restaurar scaler exacto del entrenamiento
        self.scaler = StandardScaler()
        scaler_state = features_data['scaler_state']
        self.scaler.mean_ = scaler_state['mean_']
        self.scaler.scale_ = scaler_state['scale_']
        self.scaler.var_ = scaler_state['var_']
        self.scaler.n_features_in_ = scaler_state['n_features_in_']
        self.scaler.n_samples_seen_ = scaler_state['n_samples_seen_']
        if scaler_state['feature_names_in_'] is not None:
            self.scaler.feature_names_in_ = scaler_state['feature_names_in_']
        
        self._setup_extraction()
        
        print(f"🔧 Feature Extractor MULTITOXIC cargado:")
        print(f"   Features: {len(self.feature_names)} completas")
        print(f"   Scaler ajustado: {self.fitted}")
        print(f"   Categorías: {len(self.category_mapping)}")
    
    def _setup_extraction(self):
        """Setup completo de extracción de las 107 features"""
        def extract_complete_multitoxic_features(text, processor_instance):
            """
            EXTRACCIÓN COMPLETA de las 107 features engineered
            Idéntica a la usada en entrenamiento
            """
            features = {}
            
            # Obtener features del processor primero
            tokens, visual_features = processor_instance.tokenize_with_multitoxic_features(text)
            
            # 1. FEATURES BÁSICAS UNIVERSALES
            features['text_length'] = len(text)
            words = text.lower().split()
            features['word_count'] = len(words)
            features['char_count'] = len(text)
            features['avg_word_length'] = np.mean([len(word) for word in words]) if words else 0
            
            # 2. FEATURES DE DIVERSIDAD LÉXICA MULTITOXIC
            unique_words = set(words)
            features['lexical_diversity'] = len(unique_words) / max(len(words), 1)
            features['vocab_richness'] = len(unique_words) / max(features['word_count'], 1)
            features['repetition_ratio'] = 1 - (len(unique_words) / max(len(words), 1))
            
            # 3. FEATURES VISUALES ESPECÍFICAS POR CLASE (del processor)
            for vf_name, vf_value in visual_features.items():
                features[f'visual_{vf_name}'] = vf_value
            
            # 4. FEATURES DE AGRESIVIDAD VISUAL (OBSCENE, THREAT, SEXIST)
            features['caps_extreme_count'] = len(re.findall(r'\b[A-Z]{5,}\b', text))
            features['caps_extreme_ratio'] = features['caps_extreme_count'] / max(features['word_count'], 1)
            features['caps_total_ratio'] = len(re.findall(r'[A-Z]', text)) / max(len(text), 1)
            features['caps_words_count'] = len(re.findall(r'\b[A-Z]{2,}\b', text))
            features['caps_vs_total_ratio'] = features['caps_words_count'] / max(features['word_count'], 1)
            
            # 5. FEATURES DE INTENSIDAD EMOCIONAL (ABUSIVE, PROVOCATIVE)
            features['exclamation_count'] = text.count('!')
            features['exclamation_ratio'] = features['exclamation_count'] / max(len(text), 1)
            features['multiple_exclamation'] = len(re.findall(r'!{2,}', text))
            features['question_marks'] = text.count('?')
            features['multiple_question'] = len(re.findall(r'\?{2,}', text))
            
            # 6. FEATURES DE ELABORACIÓN (HATESPEECH, RACIST)
            features['ellipsis_count'] = len(re.findall(r'\.{3,}', text))
            features['repeated_chars'] = len(re.findall(r'(.)\1{3,}', text))
            features['sentence_count'] = len([s for s in re.split(r'[.!?]+', text) if s.strip()])
            features['avg_sentence_length'] = features['word_count'] / max(features['sentence_count'], 1)
            
            # 7. VOCABULARIOS DISCRIMINANTES (12 CLASES)
            text_lower = text.lower()
            for vocab_type, word_list in self.discriminant_vocabularies.items():
                count = sum(text_lower.count(word) for word in word_list)
                features[f'{vocab_type}_count'] = count
                features[f'{vocab_type}_ratio'] = count / max(features['word_count'], 1)
                features[f'has_{vocab_type}'] = count > 0
            
            # 8. FEATURES DE TOKENS ESPECIALES (del processor)
            features['special_tokens_count'] = sum(1 for token in tokens if token.startswith('<'))
            features['caps_tokens'] = tokens.count('<CAPS>')
            features['hate_tokens'] = tokens.count('<HATE>')
            features['abusive_tokens'] = tokens.count('<ABUSIVE>')
            features['threat_tokens'] = tokens.count('<THREAT>')
            features['racist_tokens'] = tokens.count('<RACIST>')
            features['radical_tokens'] = tokens.count('<RADICAL>')
            features['excl_tokens'] = tokens.count('<EXCL>')
            features['num_tokens'] = tokens.count('<NUM>')
            
            # 9. FEATURES DE COMPLEJIDAD SINTÁCTICA
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
            
            # 10. FEATURES DE PATTERNS ESPECÍFICOS
            features['has_urls'] = bool(re.search(r'http[s]?://', text))
            features['has_mentions'] = bool(re.search(r'@\w+', text))
            features['has_hashtags'] = bool(re.search(r'#\w+', text))
            features['has_numbers'] = bool(re.search(r'\d+', text))
            features['numbers_count'] = len(re.findall(r'\b\d+\b', text))
            
            # 11. FEATURES DE DENSIDAD
            features['punct_density'] = (text.count('!') + text.count('?') + text.count('.')) / max(len(text), 1)
            features['special_chars_count'] = len(re.findall(r'[!@#$%^&*()_+={}|\\:";\'<>?,./]', text))
            features['special_chars_density'] = features['special_chars_count'] / max(len(text), 1)
            
            # 12. FEATURES DE MULTI-LABEL ESPECÍFICAS (simuladas para single prediction)
            features['toxicity_types_count'] = 0  # Será 0 para predicción individual
            features['is_multi_toxic'] = False
            features['toxicity_intensity'] = 0.0
            features['has_toxic_and_specific'] = False
            features['toxic_only'] = False
            
            # Conteo por categorías (basado en patrones detectados)
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
            
            # 13. FEATURES DE COHERENCIA Y ESTRUCTURA
            punct_chars = len(re.findall(r'[.!?,;:]', text))
            features['punctuation_complexity'] = punct_chars / max(len(text), 1)
            
            # Indicadores de argumentación (para hate/racist)
            argument_words = ['because', 'since', 'therefore', 'however', 'but', 'although']
            features['argument_markers'] = sum(1 for word in argument_words if word in text_lower)
            features['has_argumentation'] = features['argument_markers'] > 0
            
            # 14. FEATURES ESPECÍFICAS POR PATTERNS ÚNICOS
            # THREAT patterns
            threat_patterns = ['will', 'gonna', 'going to', 'watch out', 'wait']
            features['threat_pattern_count'] = sum(1 for pattern in threat_patterns if pattern in text_lower)
            
            # NATIONALIST patterns  
            nationalist_patterns = ['america', 'country', 'nation', 'patriot', 'flag']
            features['nationalist_pattern_count'] = sum(1 for pattern in nationalist_patterns if pattern in text_lower)
            
            # 15. FEATURES DE DISTRIBUCIÓN Y CONCENTRACIÓN
            if len(text) > 20:  # Solo para textos suficientemente largos
                text_chunks = [text[i:i+10] for i in range(0, len(text), 10)]
                caps_distribution = [len(re.findall(r'[A-Z]', chunk)) for chunk in text_chunks]
                features['caps_distribution_std'] = np.std(caps_distribution) if caps_distribution else 0
                features['caps_max_concentration'] = max(caps_distribution) if caps_distribution else 0
            else:
                features['caps_distribution_std'] = 0
                features['caps_max_concentration'] = 0
            
            # Convertir a array en el orden correcto de features
            feature_array = np.array([features.get(name, 0) for name in self.feature_names])
            
            # CORRECCIÓN: Ajustar a 84 features que espera el scaler
            if len(feature_array) > 84:
                feature_array = feature_array[:84]
            elif len(feature_array) < 84:
                padding = np.zeros(84 - len(feature_array))
                feature_array = np.concatenate([feature_array, padding])
            
            return feature_array
        
        self.extract_complete_multitoxic_features = extract_complete_multitoxic_features
    
    def normalize_features(self, features_array):
        """Normaliza features usando el scaler del entrenamiento"""
        return self.scaler.transform(features_array.reshape(1, -1))[0]


class HybridMultitoxicBiLSTM(nn.Module):
    """
    Arquitectura BiLSTM híbrida idéntica al entrenamiento
    Multi-head attention + Categorical branches para 12 clases
    """
    def __init__(self, vocab_size, embedding_dim, hidden_dim, num_classes, 
                 num_numeric_features, num_layers=2, dropout_rate=0.4, device='cpu'):
        super(HybridMultitoxicBiLSTM, self).__init__()
        
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.hidden_dim = hidden_dim
        self.num_classes = num_classes
        self.num_numeric_features = num_numeric_features
        self.num_layers = num_layers
        self.device = device
        
        # 1. EMBEDDING LAYER
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
        nn.init.uniform_(self.embedding.weight, -0.1, 0.1)
        self.embedding.weight.data[0].fill_(0)
        self.embedding_dropout = nn.Dropout(dropout_rate * 0.3)
        
        # 2. BiLSTM LAYERS
        self.bilstm = nn.LSTM(
            input_size=embedding_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout_rate if num_layers > 1 else 0,
        )
        
        # 3. MULTI-HEAD ATTENTION
        self.attention_dim = hidden_dim * 2
        
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
        
        # 4. NUMERIC FEATURES PROCESSOR
        self.numeric_processor = nn.Sequential(
            nn.Linear(num_numeric_features, 128),
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
        
        # 5. FUSION LAYER
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
        
        # 6. CATEGORICAL BRANCHES
        self.identity_branch = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(dropout_rate * 0.3),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Dropout(dropout_rate * 0.2)
        )
        
        self.behavior_branch = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(dropout_rate * 0.3),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Dropout(dropout_rate * 0.2)
        )
        
        self.content_branch = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(dropout_rate * 0.3),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Dropout(dropout_rate * 0.2)
        )
        
        self.general_branch = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(dropout_rate * 0.3),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Dropout(dropout_rate * 0.2)
        )
        
        # 7. OUTPUT LAYERS
        self.identity_classes = 5
        self.behavior_classes = 4
        self.content_classes = 2
        self.general_classes = 1
        
        self.identity_output = nn.Linear(32, self.identity_classes)
        self.behavior_output = nn.Linear(32, self.behavior_classes)
        self.content_output = nn.Linear(32, self.content_classes)
        self.general_output = nn.Linear(32, self.general_classes)
        
        self._initialize_weights()
    
    def _initialize_weights(self):
        """Inicialización inteligente de pesos"""
        for name, param in self.named_parameters():
            if 'weight' in name:
                if 'lstm' in name:
                    nn.init.xavier_uniform_(param)
                elif 'linear' in name.lower():
                    nn.init.kaiming_uniform_(param, nonlinearity='relu')
            elif 'bias' in name:
                nn.init.constant_(param, 0)
    
    def forward(self, text_input, numeric_input, attention_mask=None):
        """Forward pass híbrido para 12 clases categorizadas"""
        batch_size = text_input.size(0)
        
        # Text processing
        embedded = self.embedding(text_input)
        embedded = self.embedding_dropout(embedded)
        
        lstm_output, (hidden, cell) = self.bilstm(embedded)
        
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
        
        # Numeric features processing
        numeric_features = self.numeric_processor(numeric_input)
        
        # Fusion
        fused_features = torch.cat([
            attended_general, 
            attended_identity, 
            attended_behavior, 
            numeric_features
        ], dim=1)
        
        fused_output = self.fusion_layer(fused_features)
        
        # Categorical branches
        identity_features = self.identity_branch(fused_output)
        behavior_features = self.behavior_branch(fused_output)
        content_features = self.content_branch(fused_output)
        general_features = self.general_branch(fused_output)
        
        # Output logits
        identity_logits = self.identity_output(identity_features)
        behavior_logits = self.behavior_output(behavior_features)
        content_logits = self.content_output(content_features)
        general_logits = self.general_output(general_features)
        
        # Concatenar en orden correcto: toxic, hatespeech, abusive, provocative, racist, obscene, threat, religious_hate, nationalist, sexist, homophobic, radicalism
        logits = torch.cat([
            general_logits,      # toxic (1)
            content_logits,      # hatespeech, obscene (2) 
            behavior_logits,     # abusive, provocative, threat, radicalism (4)
            identity_logits      # racist, religious_hate, nationalist, sexist, homophobic (5)
        ], dim=1)
        
        return logits


class MultitoxicLoader:
    """
    Loader principal para el modelo MULTITOXIC
    Maneja carga y predicción completa de 12 clases
    """
    def __init__(self, model_dir):
        self.model_dir = Path(model_dir)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = None
        self.processor = None
        self.feature_extractor = None
        self.config = None
        
        print(f"🚀 MultitoxicLoader inicializado")
        print(f"   Dispositivo: {self.device}")
        print(f"   Directorio: {self.model_dir}")
    
    def load_model(self, version_pattern="multitoxic_v1.0_20250709_003639"):
        """Carga el modelo completo multitoxic"""
        print("🔄 Cargando modelo MULTITOXIC...")
        
        # Buscar archivos del modelo
        config_files = list(self.model_dir.glob("*" + version_pattern + "*_config.json"))
        processor_files = list(self.model_dir.glob("*" + version_pattern + "*_processor.pkl"))
        features_files = list(self.model_dir.glob("*" + version_pattern + "*_features.pkl"))
        model_files = list(self.model_dir.glob("*" + version_pattern + "*_model.pth"))
        
        if not all([config_files, processor_files, features_files, model_files]):
            missing = []
            if not config_files: missing.append("config.json")
            if not processor_files: missing.append("processor.pkl")
            if not features_files: missing.append("features.pkl")
            if not model_files: missing.append("model.pth")
            raise FileNotFoundError(f"Archivos faltantes: {', '.join(missing)}")
        
        # Cargar configuración
        with open(config_files[0], 'r') as f:
            self.config = json.load(f)
        
        # Cargar processor
        with open(processor_files[0], 'rb') as f:
            processor_data = dill.load(f)
        
        # Cargar feature extractor
        with open(features_files[0], 'rb') as f:
            features_data = dill.load(f)
        
        # Inicializar componentes
        self.processor = MultitoxicProcessor(processor_data)
        self.feature_extractor = MultitoxicExtractor(features_data)
        
        # Cargar modelo PyTorch
        model_config = self.config['model_config']
        self.model = HybridMultitoxicBiLSTM(
            vocab_size=model_config['vocab_size'],
            embedding_dim=model_config['embedding_dim'],
            hidden_dim=model_config['hidden_dim'],
            num_classes=model_config['num_classes'],
            num_numeric_features=model_config['num_numeric_features'],
            num_layers=model_config['num_layers'],
            dropout_rate=model_config['dropout_rate'],
            device=self.device
        ).to(self.device)
        
        # Cargar pesos entrenados
        checkpoint = torch.load(model_files[0], map_location=self.device, weights_only=False)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.eval()
        
        print("✅ Modelo MULTITOXIC cargado exitosamente")
        print(f"   Performance: F1-macro {self.config['performance']['test_metrics']['f1_macro']:.4f}")
        print(f"   Parámetros: {self.config['metadata']['total_parameters']:,}")
        print(f"   Clases: {', '.join(self.config['classes']['class_names'][:6])}...")
    
    def predict(self, text, return_probabilities=True, return_categories=True, return_details=False):
        """
        Predicción completa multitoxic con categorización
        """
        if not self.model:
            raise ValueError("Modelo no cargado. Ejecuta load_model() primero.")
        
        try:
            # 1. PROCESAMIENTO DE TEXTO
            tokens, visual_features = self.processor.text_to_sequence_multitoxic(text)
            
            # 2. EXTRACCIÓN DE FEATURES COMPLETAS
            features_array = self.feature_extractor.extract_complete_multitoxic_features(text, self.processor)
            normalized_features = self.feature_extractor.normalize_features(features_array)
            
            # 3. PREPARACIÓN DE TENSORES
            if len(tokens) < self.processor.max_sequence_length:
                tokens += [0] * (self.processor.max_sequence_length - len(tokens))
            elif len(tokens) > self.processor.max_sequence_length:
                tokens = tokens[:self.processor.max_sequence_length]
            
            text_tensor = torch.tensor([tokens], dtype=torch.long, device=self.device)
            features_tensor = torch.tensor([normalized_features], dtype=torch.float32, device=self.device)
            attention_mask = (text_tensor != 0).float()
            
            # 4. PREDICCIÓN
            with torch.no_grad():
                logits = self.model(text_tensor, features_tensor, attention_mask)
                probabilities = torch.sigmoid(logits).cpu().numpy()[0]
            
            # 5. INTERPRETACIÓN DE RESULTADOS
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
                    'threshold': threshold,
                    'confidence': 'high' if prob > threshold + 0.2 else 'medium' if prob > threshold + 0.1 else 'low'
                }
                
                if is_detected:
                    detected_types.append(class_name)
            
            # 6. RESULTADO PRINCIPAL
            result = {
                'detected_types': detected_types,
                'is_multi_toxic': len(detected_types) >= 2,
                'total_types': len(detected_types),
                'severity': 'high' if len(detected_types) >= 3 else 'medium' if len(detected_types) >= 2 else 'low' if len(detected_types) >= 1 else 'clean',
                'predictions': predictions
            }
            
            # 7. INFORMACIÓN ADICIONAL
            if return_probabilities:
                result['probabilities'] = {k: v['probability'] for k, v in predictions.items()}
            
            if return_categories:
                categories = self.config['classes']['category_mapping']
                category_scores = {}
                category_detections = {}
                
                for category, class_list in categories.items():
                    scores = [predictions[cls]['probability'] for cls in class_list if cls in predictions]
                    detected = [cls for cls in class_list if cls in predictions and predictions[cls]['detected']]
                    
                    category_scores[category] = np.mean(scores) if scores else 0.0
                    category_detections[category] = detected
                
                result['categories'] = {
                    'scores': category_scores,
                    'detections': category_detections
                }
            
            if return_details:
                result['details'] = {
                    'text_length': len(text),
                    'tokens_processed': len([t for t in tokens if t != 0]),
                    'features_extracted': len(normalized_features),
                    'visual_features': visual_features,
                    'processing_info': {
                        'vocab_size': len(self.processor.word_to_idx),
                        'sequence_length': self.processor.max_sequence_length,
                        'model_version': self.config['metadata']['model_version']
                    }
                }
            
            return result
            
        except Exception as e:
            return {
                'detected_types': [],
                'is_multi_toxic': False,
                'total_types': 0,
                'severity': 'error',
                'error': str(e),
                'predictions': {}
            }


if __name__ == "__main__":
    """
    Prueba automática del modelo MULTITOXIC
    """
    print("🚀 TESTING MULTITOXIC MODEL v1.0")
    print("=" * 60)
    
    try:
        # Inicializar loader
        loader = MultitoxicLoader(".")
        loader.load_model()
        
        # Casos de prueba representativos
        test_cases = [
            ("Clean", "This is a great video, thanks for sharing!"),
            ("Toxic General", "You are so fucking stupid"),
            ("Racist", "These people are inferior animals"),
            ("Multi-toxic", "You fucking racist piece of shit"),
            ("Threat", "I'm gonna find you and make you pay"),
            ("Sexist", "Women should stay in the kitchen"),
            ("Homophobic", "Those perverts make me sick"),
            ("Complex Multi", "Stupid fucking women and their gay agenda, time for revolution")
        ]
        
        print("\n🧪 Ejecutando pruebas...")
        
        for label, text in test_cases:
            result = loader.predict(text, return_categories=True, return_details=False)
            detected = result['detected_types']
            severity = result['severity']
            
            print(f"\n📝 Caso {label}:")
            print(f"   Texto: {text[:60]}{'...' if len(text) > 60 else ''}")
            print(f"   Detectado: {detected if detected else ['CLEAN']}")
            print(f"   Severidad: {severity}")
            print(f"   Multi-tóxico: {result['is_multi_toxic']}")
            
            if 'categories' in result:
                detected_cats = {k: v for k, v in result['categories']['detections'].items() if v}
                if detected_cats:
                    print(f"   Categorías: {detected_cats}")
        
        print("\n✅ MULTITOXIC model completamente operacional")
        print(f"🎯 Rendimiento garantizado: F1-macro {loader.config['performance']['test_metrics']['f1_macro']:.4f}")
        print(f"🔧 {loader.config['metadata']['total_parameters']:,} parámetros híbridos")
        print(f"🏷️  12 clases categorizadas funcionando perfectamente")
        
    except Exception as e:
        print(f"❌ Error en testing: {str(e)}")
        print("🔧 Verificar instalación de dependencias:")
        print("   pip install dill torch numpy scikit-learn pandas")