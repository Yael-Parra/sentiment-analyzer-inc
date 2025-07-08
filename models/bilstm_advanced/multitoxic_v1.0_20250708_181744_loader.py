#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
SCRIPT DE CARGA MODELO MULTITOXIC BiLSTM HÍBRIDO
Versión: multitoxic_v1.0_20250708_181744
Creado: 20250708_181744
F1-macro: 95.49% (validado con CV 5-fold)
'''

import torch
import pickle
import json
import numpy as np
from pathlib import Path

class MultitoxicModelLoader:
    def __init__(self, model_dir="."):
        self.model_dir = Path(model_dir)
        self.model = None
        self.processor = None
        self.feature_extractor = None
        self.config = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
    def load_model(self, version="multitoxic_v1.0_20250708_181744"):
        '''Carga el modelo completo MULTITOXIC'''
        print(f"🔄 Cargando modelo MULTITOXIC {version}...")
        
        # Cargar configuración
        config_path = self.model_dir / f"{version}_config.json"
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Cargar procesador
        processor_path = self.model_dir / f"{version}_processor.pkl"
        with open(processor_path, 'rb') as f:
            processor_data = pickle.load(f)
            self.processor = processor_data['processor']
        
        # Cargar extractor de features
        features_path = self.model_dir / f"{version}_features.pkl"
        with open(features_path, 'rb') as f:
            features_data = pickle.load(f)
            self.feature_extractor = features_data['feature_extractor']
        
        # Recrear arquitectura del modelo
        from model_architecture import HybridMultitoxicBiLSTM  # Importar tu clase
        
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
        
        # Cargar pesos del modelo
        model_path = self.model_dir / f"{version}_model.pth"
        checkpoint = torch.load(model_path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.eval()
        
        print(f"✅ Modelo MULTITOXIC cargado exitosamente")
        print(f"   F1-macro: {self.config['performance']['test_metrics']['f1_macro']:.4f}")
        print(f"   Clases: {self.config['classes']['num_classes']}")
        print(f"   Parámetros: {self.config['metadata']['total_parameters']:,}")
        
    def predict(self, text, return_probabilities=True, return_categories=True):
        '''Predice toxicidad para un texto'''
        if not self.model:
            raise ValueError("Modelo no cargado. Ejecuta load_model() primero.")
        
        # Procesar texto
        tokens, visual_features = self.processor.text_to_sequence_multitoxic(text)
        
        # Extraer features numéricas
        features_dict = self.feature_extractor.extract_single_text_features(text)
        normalized_features = self.feature_extractor.normalize_features(features_dict)
        
        # Preparar tensores
        text_tensor = torch.tensor([tokens], dtype=torch.long, device=self.device)
        features_tensor = torch.tensor([normalized_features], dtype=torch.float32, device=self.device)
        
        # Predicción
        with torch.no_grad():
            logits = self.model(text_tensor, features_tensor)
            probabilities = torch.sigmoid(logits).cpu().numpy()[0]
        
        # Aplicar thresholds
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
            'total_types': len(detected_types)
        }
        
        if return_probabilities:
            result['probabilities'] = {k: v['probability'] for k, v in predictions.items()}
        
        if return_categories:
            categories = self.config['classes']['category_mapping']
            category_scores = {}
            for category, class_list in categories.items():
                scores = [predictions[cls]['probability'] for cls in class_list if cls in predictions]
                category_scores[category] = np.mean(scores) if scores else 0.0
            result['categories'] = category_scores
        
        result['predictions'] = predictions
        
        return result

# Ejemplo de uso
if __name__ == "__main__":
    # Cargar modelo
    loader = MultitoxicModelLoader(".")
    loader.load_model()
    
    # Ejemplo de predicción
    text = "You're so stupid and racist!"
    result = loader.predict(text)
    
    print("🎯 Resultado:")
    print(f"   Tipos detectados: {result['detected_types']}")
    print(f"   Multi-tóxico: {result['is_multi_toxic']}")
    print(f"   Probabilidades: {result['probabilities']}")
