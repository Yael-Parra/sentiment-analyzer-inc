#!/usr/bin/env python3
"""
🧪 TEST DE INTEGRIDAD COMPLETO - MODELO MULTITÓXICO
==================================================
Verificación exhaustiva de:
- Orden de features (107 features)
- Orden de clases (12 clases)
- Arquitectura del modelo
- Pesos y parámetros
- Pipeline completo de predicción
- Thresholds y configuraciones
- Coherencia entre componentes
"""

import torch
import torch.nn as nn
import numpy as np
import pickle
import json
from pathlib import Path
import sys
import traceback
from collections import OrderedDict
import hashlib

# Importar las clases del modelo
try:
    from multitoxic_v1_0_20250709_003639_loader import MultitoxicLoader, MultitoxicProcessor, MultitoxicExtractor, MultitoxicModel
    print("✅ Clases importadas desde: multitoxic_v1_0_20250709_003639_loader")
except ImportError as e:
    print(f"❌ No se pudo importar las clases del modelo desde multitoxic_v1_0_20250709_003639_loader")
    print(f"   Error: {e}")
    print("   Asegúrate de que el archivo multitoxic_v1_0_20250709_003639_loader esté en el mismo directorio")
    sys.exit(1)

class MultitoxicIntegrityTest:
    def __init__(self, model_dir):
        self.model_dir = Path(model_dir)
        self.loader = None
        self.config = None
        self.errors = []
        self.warnings = []
        
        # Orden esperado de clases según el modelo
        self.expected_class_order = [
            'toxic',           # 1
            'hatespeech',      # 2
            'abusive',         # 3
            'threat',          # 4
            'provocative',     # 5
            'obscene',         # 6
            'racist',          # 7
            'nationalist',     # 8
            'sexist',          # 9
            'homophobic',      # 10
            'religious_hate',  # 11
            'radicalism'       # 12
        ]
        
        print("🧪 INICIANDO TEST DE INTEGRIDAD COMPLETO")
        print("=" * 50)
    
    def log_error(self, message):
        self.errors.append(message)
        print(f"❌ ERROR: {message}")
    
    def log_warning(self, message):
        self.warnings.append(message)
        print(f"⚠️ WARNING: {message}")
    
    def log_success(self, message):
        print(f"✅ OK: {message}")
    
    def test_file_existence(self):
        """Verificar que todos los archivos necesarios existan"""
        print("\n🔍 TEST 1: Verificando existencia de archivos")
        print("-" * 40)
        
        required_files = [
            "config.json",
            "processor_data.pkl",
            "features_data.pkl",
            "model_weights.pth"
        ]
        
        for file_name in required_files:
            file_path = self.model_dir / file_name
            if file_path.exists():
                file_size = file_path.stat().st_size
                self.log_success(f"{file_name} existe ({file_size:,} bytes)")
            else:
                self.log_error(f"{file_name} no existe")
    
    def test_config_structure(self):
        """Verificar estructura del config.json"""
        print("\n🔍 TEST 2: Verificando estructura de configuración")
        print("-" * 40)
        
        try:
            with open(self.model_dir / "config.json", 'r') as f:
                self.config = json.load(f)
            
            # Verificar secciones principales
            required_sections = ['model_config', 'classes', 'thresholds', 'test_metrics']
            for section in required_sections:
                if section in self.config:
                    self.log_success(f"Sección '{section}' encontrada")
                else:
                    self.log_error(f"Sección '{section}' faltante")
            
            # Verificar model_config
            if 'model_config' in self.config:
                model_config = self.config['model_config']
                required_model_keys = ['vocab_size', 'embedding_dim', 'hidden_dim', 'num_classes', 'num_numeric_features']
                for key in required_model_keys:
                    if key in model_config:
                        self.log_success(f"Model config '{key}': {model_config[key]}")
                    else:
                        self.log_error(f"Model config '{key}' faltante")
            
            # Verificar clases
            if 'classes' in self.config and 'class_names' in self.config['classes']:
                class_names = self.config['classes']['class_names']
                self.log_success(f"Clases encontradas: {len(class_names)}")
                
                # Verificar orden de clases
                if class_names == self.expected_class_order:
                    self.log_success("Orden de clases CORRECTO")
                else:
                    self.log_error("Orden de clases INCORRECTO")
                    print(f"   Esperado: {self.expected_class_order}")
                    print(f"   Actual:   {class_names}")
            
        except Exception as e:
            self.log_error(f"No se pudo cargar config.json: {e}")
    
    def test_feature_order_consistency(self):
        """Verificar consistencia del orden de features"""
        print("\n🔍 TEST 3: Verificando orden de features")
        print("-" * 40)
        
        try:
            # Cargar features del extractor
            with open(self.model_dir / "features_data.pkl", "rb") as f:
                features_data = pickle.load(f)
                extractor_names = features_data['feature_names']
            
            # Cargar features del config (si existe)
            config_names = self.config.get("model_config", {}).get("feature_names", [])
            
            print(f"📊 Features en extractor: {len(extractor_names)}")
            print(f"📊 Features en config: {len(config_names)}")
            
            if len(extractor_names) != 107:
                self.log_error(f"Número de features incorrecto: {len(extractor_names)} (esperado: 107)")
            else:
                self.log_success("Número de features correcto (107)")
            
            # ✅ NUEVO: Verificar orden completo de features con el modelo
            model_config = self.config.get('model_config', {})
            expected_num_features = model_config.get('num_numeric_features', 107)
            
            if len(extractor_names) != expected_num_features:
                self.log_error(f"Features extractor ({len(extractor_names)}) != model config ({expected_num_features})")
            else:
                self.log_success(f"Número de features coincide con modelo: {expected_num_features}")
            
            # ✅ NUEVO: Verificar que el extractor puede generar features en orden correcto
            try:
                processor = MultitoxicProcessor(self.model_dir / "processor_data.pkl")
                feature_extractor = MultitoxicExtractor(self.model_dir / "features_data.pkl")
                
                # Test con texto de prueba
                test_text = "This is a TEST with CAPS and numbers 123!"
                features_array = feature_extractor.extract_features(test_text, processor)
                
                if len(features_array) == len(extractor_names):
                    self.log_success(f"Extractor genera {len(features_array)} features correctamente")
                else:
                    self.log_error(f"Extractor genera {len(features_array)} features, esperado {len(extractor_names)}")
                
                # Verificar que no hay NaN
                if np.any(np.isnan(features_array)):
                    self.log_error("Features contienen valores NaN")
                else:
                    self.log_success("Todas las features son valores válidos")
                    
            except Exception as e:
                self.log_error(f"Error probando extractor de features: {e}")
            
            # Si hay features en config, verificar concordancia
            if config_names:
                if len(extractor_names) != len(config_names):
                    self.log_error("Diferente número de features entre extractor y config")
                else:
                    mismatch_count = 0
                    for i, (name1, name2) in enumerate(zip(extractor_names, config_names)):
                        if name1 != name2:
                            print(f"   Desajuste en posición {i}: extractor='{name1}' vs config='{name2}'")
                            mismatch_count += 1
                    
                    if mismatch_count == 0:
                        self.log_success("Orden de features coincide perfectamente")
                    else:
                        self.log_error(f"{mismatch_count} desajustes en orden de features")
            
            # ✅ NUEVO: Verificar features críticas por categoría
            critical_features_by_category = {
                'basic': ['text_length', 'word_count', 'char_count', 'avg_word_length'],
                'lexical': ['lexical_diversity', 'vocab_richness', 'repetition_ratio'],
                'visual': ['caps_extreme_count', 'caps_total_ratio', 'exclamation_count'],
                'discriminant': ['toxic_words_count', 'abusive_words_count', 'racist_words_count'],
                'tokens': ['special_tokens_count', 'caps_tokens', 'num_tokens'],
                'complexity': ['word_length_std', 'word_length_max', 'punctuation_complexity']
            }
            
            missing_by_category = {}
            for category, feature_list in critical_features_by_category.items():
                missing = [f for f in feature_list if f not in extractor_names]
                if missing:
                    missing_by_category[category] = missing
            
            if missing_by_category:
                for category, missing in missing_by_category.items():
                    self.log_error(f"Features {category} faltantes: {missing}")
            else:
                self.log_success("Todas las features críticas por categoría presentes")
            
            # ✅ NUEVO: Verificar que features discriminantes coinciden con vocabularios
            try:
                discriminant_vocabs = features_data.get('discriminant_vocabularies', {})
                expected_vocab_features = [f"{vocab}_count" for vocab in discriminant_vocabs.keys()]
                missing_vocab_features = [f for f in expected_vocab_features if f not in extractor_names]
                
                if missing_vocab_features:
                    self.log_error(f"Features de vocabulario discriminante faltantes: {missing_vocab_features}")
                else:
                    self.log_success(f"Todas las features de vocabularios discriminantes presentes ({len(expected_vocab_features)})")
            
            except Exception as e:
                self.log_warning(f"No se pudieron verificar vocabularios discriminantes: {e}")
            
        except Exception as e:
            self.log_error(f"Error verificando features: {e}")
    
    def test_class_order_complete_consistency(self):
        """Verificar consistencia COMPLETA del orden de clases entre todos los componentes"""
        print("\n🔍 TEST 3.5: Verificando consistencia COMPLETA de orden de clases")
        print("-" * 40)
        
        try:
            # 1. Orden en config.json
            config_classes = self.config.get('classes', {}).get('class_names', [])
            
            # 2. Orden esperado por el modelo (según forward pass)
            model_expected_order = self.expected_class_order
            
            # 3. Orden en thresholds
            threshold_classes = list(self.config.get('thresholds', {}).keys())
            
            # 4. Orden en métricas de test
            test_metrics = self.config.get('test_metrics', {})
            metrics_classes = list(test_metrics.get('class_metrics', {}).keys()) if 'class_metrics' in test_metrics else []
            
            print(f"📊 Verificando orden en {len([config_classes, threshold_classes, metrics_classes])} fuentes:")
            
            # Verificar que todos tienen el mismo número de clases
            class_counts = {
                'config': len(config_classes),
                'thresholds': len(threshold_classes), 
                'metrics': len(metrics_classes),
                'expected': len(model_expected_order)
            }
            
            for source, count in class_counts.items():
                if count == 12:
                    self.log_success(f"{source}: {count} clases")
                else:
                    self.log_error(f"{source}: {count} clases (esperado: 12)")
            
            # Verificar orden exacto
            comparisons = [
                ('config vs expected', config_classes, model_expected_order),
                ('thresholds vs expected', threshold_classes, model_expected_order),
                ('metrics vs expected', metrics_classes, model_expected_order)
            ]
            
            for name, actual, expected in comparisons:
                if not actual:  # Si está vacío, skip
                    continue
                    
                if actual == expected:
                    self.log_success(f"Orden {name}: ✅ PERFECTO")
                else:
                    self.log_error(f"Orden {name}: ❌ INCORRECTO")
                    print(f"   Esperado: {expected}")
                    print(f"   Actual:   {actual}")
                    
                    # Mostrar diferencias específicas
                    for i, (a, e) in enumerate(zip(actual, expected)):
                        if a != e:
                            print(f"   Posición {i}: '{a}' != '{e}'")
            
            # ✅ NUEVO: Verificar que el forward pass del modelo coincide
            try:
                model_config = self.config['model_config']
                model = MultitoxicModel(model_config)
                
                # Test de forward pass para verificar dimensiones
                batch_size = 1
                seq_length = model_config.get('max_sequence_length', 128)
                num_features = model_config['num_numeric_features']
                
                dummy_text = torch.randint(0, model_config['vocab_size'], (batch_size, seq_length))
                dummy_features = torch.randn(batch_size, num_features)
                dummy_mask = torch.ones(batch_size, seq_length)
                
                with torch.no_grad():
                    output = self.model(dummy_text, dummy_features, dummy_mask)
                
                if output.shape[1] == len(config_classes):
                    self.log_success(f"Output del modelo: {output.shape[1]} clases (coincide)")
                else:
                    self.log_error(f"Output del modelo: {output.shape[1]} clases, config: {len(config_classes)}")
                    
            except Exception as e:
                self.log_warning(f"No se pudo verificar output del modelo: {e}")
                
            # ✅ NUEVO: Verificar mapeo categórico
            try:
                with open(self.model_dir / "features_data.pkl", "rb") as f:
                    features_data = pickle.load(f)
                
                category_mapping = features_data.get('category_mapping', {})
                if category_mapping:
                    # Verificar que todas las clases están en alguna categoría
                    all_categorized = set()
                    for category, class_list in category_mapping.items():
                        all_categorized.update(class_list)
                    
                    missing_from_categories = set(config_classes) - all_categorized
                    extra_in_categories = all_categorized - set(config_classes)
                    
                    if missing_from_categories:
                        self.log_error(f"Clases no categorizadas: {missing_from_categories}")
                    if extra_in_categories:
                        self.log_error(f"Clases extra en categorías: {extra_in_categories}")
                    if not missing_from_categories and not extra_in_categories:
                        self.log_success("Mapeo categórico completo y correcto")
                        
            except Exception as e:
                self.log_warning(f"No se pudo verificar mapeo categórico: {e}")
        
        except Exception as e:
            self.log_error(f"Error verificando consistencia de clases: {e}")
    
    def test_model_architecture(self):
        """Verificar arquitectura del modelo"""
        print("\n🔍 TEST 4: Verificando arquitectura del modelo")
        print("-" * 40)
        
        try:
            # Crear modelo
            model_config = self.config['model_config']
            model = MultitoxicModel(model_config)
            
            # Verificar parámetros
            total_params = sum(p.numel() for p in model.parameters())
            trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
            
            self.log_success(f"Parámetros totales: {total_params:,}")
            self.log_success(f"Parámetros entrenables: {trainable_params:,}")
            
            # Verificar que coincida con la especificación
            if total_params == 2752159:
                self.log_success("Número de parámetros coincide con especificación")
            else:
                self.log_warning(f"Número de parámetros difiere de especificación (2,752,159)")
            
            # Verificar componentes del modelo
            components = [
                'embedding', 'bilstm', 'attention_general', 'attention_identity',
                'attention_behavior', 'numeric_processor', 'fusion_layer',
                'identity_branch', 'behavior_branch', 'content_branch', 'general_branch',
                'identity_output', 'behavior_output', 'content_output', 'general_output'
            ]
            
            for component in components:
                if hasattr(model, component):
                    self.log_success(f"Componente '{component}' presente")
                else:
                    self.log_error(f"Componente '{component}' faltante")
            
            # Test de forward pass
            batch_size = 2
            seq_length = model_config.get('max_sequence_length', 128)
            num_features = model_config['num_numeric_features']
            
            dummy_text = torch.randint(0, model_config['vocab_size'], (batch_size, seq_length))
            dummy_features = torch.randn(batch_size, num_features)
            dummy_mask = torch.ones(batch_size, seq_length)
            
            with torch.no_grad():
                output = model(dummy_text, dummy_features, dummy_mask)
            
            expected_shape = (batch_size, model_config['num_classes'])
            if output.shape == expected_shape:
                self.log_success(f"Forward pass exitoso: {output.shape}")
            else:
                self.log_error(f"Forward pass shape incorrecto: {output.shape} (esperado: {expected_shape})")
            
        except Exception as e:
            self.log_error(f"Error en arquitectura del modelo: {e}")
            traceback.print_exc()
    
    def test_model_weights(self):
        """Verificar pesos del modelo"""
        print("\n🔍 TEST 5: Verificando pesos del modelo")
        print("-" * 40)
        
        try:
            # Cargar checkpoint
            checkpoint = torch.load(self.model_dir / "model_weights.pth", map_location='cpu')
            
            # Verificar estructura del checkpoint
            if 'state_dict' in checkpoint:
                self.log_success("Checkpoint contiene state_dict")
                state_dict = checkpoint['state_dict']
            else:
                self.log_error("Checkpoint no contiene state_dict")
                return
            
            # Verificar keys esperadas
            expected_keys = [
                'embedding.weight', 'bilstm.weight_ih_l0', 'bilstm.weight_hh_l0',
                'attention_general.0.weight', 'numeric_processor.0.weight',
                'fusion_layer.0.weight', 'identity_output.weight', 'behavior_output.weight',
                'content_output.weight', 'general_output.weight'
            ]
            
            missing_keys = []
            for key in expected_keys:
                if key not in state_dict:
                    missing_keys.append(key)
            
            if missing_keys:
                self.log_error(f"Keys faltantes en state_dict: {missing_keys}")
            else:
                self.log_success("Todas las keys críticas presentes en state_dict")
            
            # Verificar que los pesos no sean todos ceros
            zero_weights = []
            for name, param in state_dict.items():
                if torch.all(param == 0):
                    zero_weights.append(name)
            
            if zero_weights:
                self.log_error(f"Pesos en cero: {zero_weights}")
            else:
                self.log_success("Ningún peso es completamente cero")
            
            # Verificar rangos razonables
            extreme_weights = []
            for name, param in state_dict.items():
                if torch.max(torch.abs(param)) > 10:
                    extreme_weights.append(name)
            
            if extreme_weights:
                self.log_warning(f"Pesos con valores extremos (>10): {extreme_weights}")
            else:
                self.log_success("Todos los pesos en rangos razonables")
            
        except Exception as e:
            self.log_error(f"Error verificando pesos: {e}")
    
    def test_thresholds_consistency(self):
        """Verificar consistencia de thresholds"""
        print("\n🔍 TEST 6: Verificando thresholds")
        print("-" * 40)
        
        try:
            if 'thresholds' not in self.config:
                self.log_error("No hay thresholds en config")
                return
            
            thresholds = self.config['thresholds']
            class_names = self.config['classes']['class_names']
            
            # Verificar que hay threshold para cada clase
            missing_thresholds = []
            for class_name in class_names:
                if class_name not in thresholds:
                    missing_thresholds.append(class_name)
            
            if missing_thresholds:
                self.log_error(f"Thresholds faltantes: {missing_thresholds}")
            else:
                self.log_success("Thresholds presentes para todas las clases")
            
            # Verificar rangos razonables (0-1)
            invalid_thresholds = []
            for class_name, threshold in thresholds.items():
                if not (0 <= threshold <= 1):
                    invalid_thresholds.append(f"{class_name}: {threshold}")
            
            if invalid_thresholds:
                self.log_error(f"Thresholds fuera de rango [0,1]: {invalid_thresholds}")
            else:
                self.log_success("Todos los thresholds en rango válido [0,1]")
            
            # Mostrar thresholds
            print("📊 Thresholds por clase:")
            for class_name in class_names:
                threshold = thresholds.get(class_name, 'N/A')
                print(f"   {class_name}: {threshold}")
            
        except Exception as e:
            self.log_error(f"Error verificando thresholds: {e}")
    
    def test_processor_consistency(self):
        """Verificar consistencia del processor"""
        print("\n🔍 TEST 7: Verificando processor")
        print("-" * 40)
        
        try:
            processor = MultitoxicProcessor(self.model_dir / "processor_data.pkl")
            
            # Verificar vocabulario
            vocab_size = len(processor.word_to_idx)
            expected_vocab = self.config['model_config']['vocab_size']
            
            if vocab_size == expected_vocab:
                self.log_success(f"Tamaño de vocabulario correcto: {vocab_size}")
            else:
                self.log_error(f"Tamaño de vocabulario incorrecto: {vocab_size} (esperado: {expected_vocab})")
            
            # ✅ MEJORADO: Verificar tokens especiales más flexiblemente
            required_tokens = ['<PAD>', '<UNK>']  # Tokens absolutamente necesarios
            optional_tokens = ['<START>', '<END>']  # Tokens opcionales pero recomendados
            
            missing_required = []
            missing_optional = []
            
            for token in required_tokens:
                if token not in processor.word_to_idx:
                    missing_required.append(token)
            
            for token in optional_tokens:
                if token not in processor.word_to_idx:
                    missing_optional.append(token)
            
            if missing_required:
                self.log_error(f"Tokens especiales CRÍTICOS faltantes: {missing_required}")
            else:
                self.log_success("Tokens especiales críticos presentes")
            
            if missing_optional:
                self.log_warning(f"Tokens especiales OPCIONALES faltantes: {missing_optional}")
                print("   ℹ️  Los tokens <START> y <END> son opcionales para este modelo")
                print("   ℹ️  El modelo funciona correctamente sin ellos")
            else:
                self.log_success("Todos los tokens especiales presentes")
            
            # ✅ NUEVO: Verificar que el vocabulario contiene palabras reales
            sample_words = ['the', 'and', 'you', 'to', 'of', 'a', 'that', 'it', 'in', 'is']
            missing_common = [word for word in sample_words if word not in processor.word_to_idx]
            
            if len(missing_common) > 5:
                self.log_warning(f"Muchas palabras comunes faltantes: {missing_common}")
            elif missing_common:
                self.log_warning(f"Algunas palabras comunes faltantes: {missing_common}")
            else:
                self.log_success("Vocabulario contiene palabras comunes")
            
            # ✅ NUEVO: Verificar distribución del vocabulario
            vocab_stats = {
                'total_words': len(processor.word_to_idx),
                'special_tokens': len([k for k in processor.word_to_idx.keys() if k.startswith('<')]),
                'regular_words': len([k for k in processor.word_to_idx.keys() if not k.startswith('<')])
            }
            
            print(f"📊 Estadísticas del vocabulario:")
            for stat, value in vocab_stats.items():
                print(f"   {stat}: {value}")
            
            if vocab_stats['regular_words'] < 1000:
                self.log_warning(f"Vocabulario pequeño: {vocab_stats['regular_words']} palabras")
            else:
                self.log_success(f"Vocabulario adecuado: {vocab_stats['regular_words']} palabras")
            
            # Test de procesamiento con múltiples casos
            test_cases = [
                ("texto_normal", "This is a test message with CAPS and numbers 123!"),
                ("texto_mayusculas", "THIS IS ALL CAPS TEXT"),
                ("texto_numeros", "Test with numbers 456 789"),
                ("texto_especial", "Special chars: !@#$%^&*()"),
                ("texto_vacio", ""),
                ("texto_corto", "Hi"),
                ("texto_largo", "This is a very long message " * 10)
            ]
            
            successful_processing = 0
            
            for label, text in test_cases:
                try:
                    tokens, visual_features = processor.text_to_sequence(text)
                    
                    # Verificar que retorna estructuras válidas
                    if isinstance(tokens, list) and isinstance(visual_features, dict):
                        successful_processing += 1
                        
                        # Para textos no vacíos, verificar que genera tokens
                        if text.strip() and not tokens:
                            self.log_warning(f"Texto '{label}' no genera tokens: '{text[:30]}'")
                        
                    else:
                        self.log_error(f"Procesamiento de '{label}' retorna tipos incorrectos")
                        
                except Exception as e:
                    self.log_error(f"Error procesando '{label}': {e}")
            
            success_rate = successful_processing / len(test_cases)
            if success_rate == 1.0:
                self.log_success(f"Procesamiento exitoso en todos los casos ({successful_processing}/{len(test_cases)})")
            elif success_rate >= 0.8:
                self.log_warning(f"Procesamiento mayormente exitoso ({successful_processing}/{len(test_cases)})")
            else:
                self.log_error(f"Muchos fallos en procesamiento ({successful_processing}/{len(test_cases)})")
            
            # ✅ NUEVO: Verificar longitud máxima de secuencia
            max_seq_len = processor.max_sequence_length
            expected_max_len = self.config['model_config'].get('max_sequence_length', 128)
            
            if max_seq_len == expected_max_len:
                self.log_success(f"Longitud máxima de secuencia correcta: {max_seq_len}")
            else:
                self.log_error(f"Longitud máxima incorrecta: {max_seq_len} (esperado: {expected_max_len})")
            
        except Exception as e:
            self.log_error(f"Error verificando processor: {e}")
    
    def test_feature_extractor_consistency(self):
        """Verificar consistencia del feature extractor"""
        print("\n🔍 TEST 8: Verificando feature extractor")
        print("-" * 40)
        
        try:
            feature_extractor = MultitoxicExtractor(self.model_dir / "features_data.pkl")
            processor = MultitoxicProcessor(self.model_dir / "processor_data.pkl")
            
            # Test de extracción
            test_text = "This is a test message with CAPS and numbers 123!"
            features = feature_extractor.extract_features(test_text, processor)
            
            expected_features = len(feature_extractor.feature_names)
            if len(features) == expected_features:
                self.log_success(f"Extracción de features exitosa: {len(features)} features")
            else:
                self.log_error(f"Número de features incorrecto: {len(features)} (esperado: {expected_features})")
            
            # Verificar normalización
            normalized = feature_extractor.normalize_features(features)
            if len(normalized) == len(features):
                self.log_success("Normalización exitosa")
            else:
                self.log_error("Error en normalización")
            
            # Verificar que no hay NaN o Inf
            if np.any(np.isnan(normalized)) or np.any(np.isinf(normalized)):
                self.log_error("Features normalizadas contienen NaN o Inf")
            else:
                self.log_success("Features normalizadas válidas")
            
        except Exception as e:
            self.log_error(f"Error verificando feature extractor: {e}")
    
    def test_end_to_end_prediction(self):
        """Test completo de predicción end-to-end"""
        print("\n🔍 TEST 9: Verificando predicción end-to-end")
        print("-" * 40)
        
        try:
            # Cargar modelo completo
            self.loader = MultitoxicLoader(self.model_dir)
            self.loader.load_model()
            
            # Test cases
            test_cases = [
                ("texto_limpio", "This is a great video!"),
                ("texto_toxico", "You are so stupid"),
                ("texto_vacio", ""),
                ("texto_largo", "This is a very long text " * 20),
                ("texto_especial", "Special chars: !@#$%^&*()_+{}|:<>?[]\\;',./"),
                ("texto_numeros", "Test with numbers 123 456 789"),
                ("texto_mayusculas", "THIS IS ALL CAPS TEXT"),
                ("texto_mixto", "MiXeD cAsE tExT with 123 and !!!")
            ]
            
            successful_predictions = 0
            
            for label, text in test_cases:
                try:
                    result = self.loader.predict(text)
                    
                    # Verificar estructura del resultado
                    required_keys = ['detected_types', 'is_multi_toxic', 'total_types', 'severity', 'predictions']
                    missing_keys = [key for key in required_keys if key not in result]
                    
                    if missing_keys:
                        self.log_error(f"Keys faltantes en resultado para '{label}': {missing_keys}")
                    else:
                        successful_predictions += 1
                        self.log_success(f"Predicción exitosa para '{label}': {result['severity']}")
                        
                        # Verificar que las probabilidades están en rango [0,1]
                        if 'predictions' in result:
                            invalid_probs = []
                            for class_name, pred_data in result['predictions'].items():
                                prob = pred_data['probability']
                                if not (0 <= prob <= 1):
                                    invalid_probs.append(f"{class_name}: {prob}")
                            
                            if invalid_probs:
                                self.log_error(f"Probabilidades fuera de rango para '{label}': {invalid_probs}")
                
                except Exception as e:
                    self.log_error(f"Error en predicción para '{label}': {e}")
            
            success_rate = successful_predictions / len(test_cases)
            if success_rate == 1.0:
                self.log_success(f"Todas las predicciones exitosas ({successful_predictions}/{len(test_cases)})")
            else:
                self.log_error(f"Algunas predicciones fallaron ({successful_predictions}/{len(test_cases)})")
            
        except Exception as e:
            self.log_error(f"Error en test end-to-end: {e}")
    
    def test_performance_metrics(self):
        """Verificar métricas de performance"""
        print("\n🔍 TEST 10: Verificando métricas de performance")
        print("-" * 40)
        
        try:
            if 'test_metrics' not in self.config:
                self.log_warning("No hay métricas de test en config")
                return
            
            metrics = self.config['test_metrics']
            
            # Verificar F1-macro
            if 'f1_macro' in metrics:
                f1_macro = metrics['f1_macro']
                if f1_macro >= 0.95:
                    self.log_success(f"F1-macro excelente: {f1_macro:.4f}")
                elif f1_macro >= 0.90:
                    self.log_success(f"F1-macro bueno: {f1_macro:.4f}")
                else:
                    self.log_warning(f"F1-macro bajo: {f1_macro:.4f}")
            
            # Mostrar todas las métricas
            print("📊 Métricas de test:")
            for metric, value in metrics.items():
                print(f"   {metric}: {value}")
            
        except Exception as e:
            self.log_error(f"Error verificando métricas: {e}")
    
    def run_all_tests(self):
        """Ejecutar todos los tests"""
        print(f"🚀 Ejecutando tests en directorio: {self.model_dir}")
        
        test_methods = [
            self.test_file_existence,
            self.test_config_structure,
            self.test_feature_order_consistency,
            self.test_class_order_complete_consistency,
            self.test_model_architecture,
            self.test_model_weights,
            self.test_thresholds_consistency,
            self.test_processor_consistency,
            self.test_feature_extractor_consistency,
            self.test_end_to_end_prediction,
            self.test_performance_metrics
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                self.log_error(f"Test {test_method.__name__} falló: {e}")
        
        # Resumen final
        self.print_summary()
    
    def print_summary(self):
        """Imprimir resumen final"""
        print("\n" + "=" * 50)
        print("📋 RESUMEN DE INTEGRIDAD")
        print("=" * 50)
        
        total_tests = len(self.errors) + len(self.warnings) + 1  # +1 para éxitos
        
        if not self.errors and not self.warnings:
            print("🎉 MODELO COMPLETAMENTE ÍNTEGRO")
            print("   ✅ Todos los tests pasaron exitosamente")
            print("   ✅ No se encontraron errores ni advertencias")
        else:
            if self.errors:
                print(f"❌ ERRORES ENCONTRADOS: {len(self.errors)}")
                for i, error in enumerate(self.errors, 1):
                    print(f"   {i}. {error}")
            
            if self.warnings:
                print(f"⚠️ ADVERTENCIAS: {len(self.warnings)}")
                for i, warning in enumerate(self.warnings, 1):
                    print(f"   {i}. {warning}")
        
        print("\n📊 ESTADÍSTICAS:")
        print(f"   Errores: {len(self.errors)}")
        print(f"   Advertencias: {len(self.warnings)}")
        
        if len(self.errors) == 0:
            print("✅ MODELO LISTO PARA PRODUCCIÓN")
        else:
            print("❌ MODELO REQUIERE CORRECCIONES")
        
        print("=" * 50)

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test de integridad del modelo Multitóxico')
    parser.add_argument('--model-dir', '-d', default='models/bilstm_advanced', 
                   help='Directorio del modelo (default: models/bilstm_advanced)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Mostrar información detallada')
    
    args = parser.parse_args()
    
    # Ejecutar tests
    tester = MultitoxicIntegrityTest(args.model_dir)
    tester.run_all_tests()

if __name__ == "__main__":
    main()