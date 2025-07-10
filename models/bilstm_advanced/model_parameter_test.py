#!/usr/bin/env python3
"""
🔍 TEST DE DEBUG DE PREDICCIONES - ANÁLISIS EXHAUSTIVO
======================================================
Analiza predicciones paso a paso para detectar fallos y sus causas
- Pipeline completo de procesamiento
- Análisis de features extraídas
- Verificación de logits y probabilidades
- Comparación con thresholds
- Detección de inconsistencias
"""

import torch
import numpy as np
import pandas as pd
import json
from pathlib import Path
import traceback
from collections import OrderedDict
import matplotlib.pyplot as plt
import seaborn as sns

# Importar las clases del modelo
try:
    from multitoxic_v1_0_20250709_003639_loader import MultitoxicLoader, MultitoxicProcessor, MultitoxicExtractor, MultitoxicModel
    print("✅ Clases importadas desde: multitoxic_v1_0_20250709_003639_loaderpy")
except ImportError as e:
    print(f"❌ No se pudo importar las clases del modelo: {e}")
    exit(1)

class PredictionDebugger:
    def __init__(self, model_dir="/models/bilstm_advanced"):
        self.model_dir = Path(model_dir)
        self.loader = None
        self.config = None
        self.issues = []
        self.warnings = []
        self.detailed_results = []
        
        print("🔍 INICIANDO DEBUG DE PREDICCIONES")
        print("=" * 50)
        
        # Cargar modelo
        try:
            self.loader = MultitoxicLoader(self.model_dir)
            self.loader.load_model()
            self.config = self.loader.config
            print("✅ Modelo cargado exitosamente")
        except Exception as e:
            print(f"❌ Error cargando modelo: {e}")
            exit(1)
    
    def log_issue(self, issue):
        self.issues.append(issue)
        print(f"❌ ISSUE: {issue}")
    
    def log_warning(self, warning):
        self.warnings.append(warning)
        print(f"⚠️ WARNING: {warning}")
    
    def log_info(self, info):
        print(f"ℹ️ INFO: {info}")
    
    def analyze_text_processing_pipeline(self, text):
        """Analiza paso a paso el pipeline de procesamiento de texto"""
        print(f"\n🔍 ANALIZANDO PIPELINE: '{text[:50]}{'...' if len(text) > 50 else ''}'")
        print("-" * 60)
        
        analysis = {
            'original_text': text,
            'text_length': len(text),
            'pipeline_steps': {},
            'issues': []
        }
        
        try:
            # Paso 1: Procesamiento de texto
            print("📝 PASO 1: Procesamiento de texto")
            tokens, visual_features = self.loader.processor.text_to_sequence(text)
            
            analysis['pipeline_steps']['text_processing'] = {
                'tokens_generated': len(tokens),
                'visual_features_count': len(visual_features),
                'tokens_sample': tokens[:10] if tokens else [],
                'visual_features': visual_features
            }
            
            print(f"   Tokens generados: {len(tokens)}")
            print(f"   Features visuales: {len(visual_features)}")
            
            if not tokens and text.strip():
                analysis['issues'].append("Texto no vacío pero no genera tokens")
                self.log_issue(f"Texto '{text[:30]}' no genera tokens")
            
            # Paso 2: Extracción de features
            print("🔧 PASO 2: Extracción de features")
            features_array = self.loader.feature_extractor.extract_features(text, self.loader.processor)
            normalized_features = self.loader.feature_extractor.normalize_features(features_array)
            
            analysis['pipeline_steps']['feature_extraction'] = {
                'features_extracted': len(features_array),
                'features_min': float(np.min(features_array)),
                'features_max': float(np.max(features_array)),
                'features_mean': float(np.mean(features_array)),
                'normalized_min': float(np.min(normalized_features)),
                'normalized_max': float(np.max(normalized_features)),
                'normalized_mean': float(np.mean(normalized_features)),
                'has_nan': bool(np.any(np.isnan(normalized_features))),
                'has_inf': bool(np.any(np.isinf(normalized_features)))
            }
            
            print(f"   Features extraídas: {len(features_array)}")
            print(f"   Rango original: [{np.min(features_array):.3f}, {np.max(features_array):.3f}]")
            print(f"   Rango normalizado: [{np.min(normalized_features):.3f}, {np.max(normalized_features):.3f}]")
            
            if np.any(np.isnan(normalized_features)):
                analysis['issues'].append("Features normalizadas contienen NaN")
                self.log_issue("Features normalizadas contienen valores NaN")
            
            if np.any(np.isinf(normalized_features)):
                analysis['issues'].append("Features normalizadas contienen Inf")
                self.log_issue("Features normalizadas contienen valores infinitos")
            
            # Paso 3: Preparación de tensores
            print("⚡ PASO 3: Preparación de tensores")
            
            # Padding de tokens
            max_seq_len = self.loader.processor.max_sequence_length
            if len(tokens) < max_seq_len:
                padded_tokens = tokens + [0] * (max_seq_len - len(tokens))
            else:
                padded_tokens = tokens[:max_seq_len]
            
            text_tensor = torch.tensor([padded_tokens], dtype=torch.long, device=self.loader.device)
            features_tensor = torch.from_numpy(np.array([normalized_features])).float().to(self.loader.device)
            attention_mask = (text_tensor != 0).float()
            
            analysis['pipeline_steps']['tensor_preparation'] = {
                'original_tokens_length': len(tokens),
                'padded_tokens_length': len(padded_tokens),
                'max_sequence_length': max_seq_len,
                'text_tensor_shape': list(text_tensor.shape),
                'features_tensor_shape': list(features_tensor.shape),
                'attention_mask_shape': list(attention_mask.shape),
                'non_zero_tokens': int(torch.sum(attention_mask).item())
            }
            
            print(f"   Tokens originales: {len(tokens)}")
            print(f"   Tokens con padding: {len(padded_tokens)}")
            print(f"   Tokens no-cero: {int(torch.sum(attention_mask).item())}")
            
            # Paso 4: Predicción del modelo
            print("🧠 PASO 4: Predicción del modelo")
            
            with torch.no_grad():
                logits = self.loader.model(text_tensor, features_tensor, attention_mask)
                probabilities = torch.sigmoid(logits).cpu().numpy()[0]
            
            analysis['pipeline_steps']['model_prediction'] = {
                'logits_shape': list(logits.shape),
                'logits_min': float(logits.min().item()),
                'logits_max': float(logits.max().item()),
                'logits_mean': float(logits.mean().item()),
                'probabilities_min': float(np.min(probabilities)),
                'probabilities_max': float(np.max(probabilities)),
                'probabilities_mean': float(np.mean(probabilities)),
                'logits_raw': logits.cpu().numpy()[0].tolist(),
                'probabilities_raw': probabilities.tolist()
            }
            
            print(f"   Logits shape: {logits.shape}")
            print(f"   Logits rango: [{logits.min().item():.3f}, {logits.max().item():.3f}]")
            print(f"   Probabilidades rango: [{np.min(probabilities):.3f}, {np.max(probabilities):.3f}]")
            
            # Verificar dimensiones
            expected_classes = len(self.config['classes']['class_names'])
            if logits.shape[1] != expected_classes:
                analysis['issues'].append(f"Logits shape incorrecta: {logits.shape[1]} != {expected_classes}")
                self.log_issue(f"Logits shape incorrecta: {logits.shape[1]} (esperado: {expected_classes})")
            
            # Paso 5: Interpretación de resultados
            print("📊 PASO 5: Interpretación de resultados")
            
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
                    'threshold': threshold,
                    'detected': is_detected,
                    'margin': prob - threshold
                }
                
                if is_detected:
                    detected_types.append(class_name)
            
            analysis['pipeline_steps']['interpretation'] = {
                'total_classes': len(class_names),
                'detected_classes': len(detected_types),
                'detected_types': detected_types,
                'predictions': predictions
            }
            
            print(f"   Clases detectadas: {len(detected_types)}")
            print(f"   Tipos detectados: {detected_types}")
            
            # Verificar consistencia de thresholds
            for class_name in class_names:
                if class_name not in thresholds:
                    analysis['issues'].append(f"Threshold faltante para {class_name}")
                    self.log_issue(f"Threshold faltante para clase {class_name}")
            
            analysis['success'] = True
            
        except Exception as e:
            analysis['success'] = False
            analysis['error'] = str(e)
            analysis['traceback'] = traceback.format_exc()
            self.log_issue(f"Error en pipeline: {e}")
        
        return analysis
    
    def test_diverse_text_cases(self):
        """Testa casos de texto diversos para encontrar edge cases"""
        print(f"\n🧪 TESTING CASOS DIVERSOS")
        print("=" * 50)
        
        test_cases = [
            # Casos básicos
            ("texto_limpio", "This is a great video, thanks for sharing!"),
            ("texto_neutral", "The weather is nice today."),
            
            # Casos tóxicos por categoría
            ("toxic_general", "You are so fucking stupid"),
            ("racist", "These people are inferior animals"),
            ("sexist", "Women should stay in the kitchen"),
            ("homophobic", "Those perverts make me sick"),
            ("threat", "I'm gonna find you and make you pay"),
            ("abusive", "You worthless piece of shit"),
            ("obscene", "Fuck this shit seriously"),
            ("hatespeech", "We need to purge these people"),
            ("nationalist", "Our race is superior to all others"),
            ("provocative", "You should kill yourself pathetic loser"),
            ("religious_hate", "Those perverts are spreading mental illness"),
            ("radicalism", "The revolution is coming, we must act"),
            
            # Multi-tóxicos
            ("multi_toxic_1", "You fucking racist piece of shit"),
            ("multi_toxic_2", "Those perverted animals should be eliminated"),
            
            # Edge cases problemáticos
            ("texto_vacio", ""),
            ("solo_espacios", "   "),
            ("solo_puntuacion", "!@#$%^&*()"),
            ("solo_numeros", "123 456 789"),
            ("solo_mayusculas", "THIS IS ALL CAPS"),
            ("texto_muy_corto", "Hi"),
            ("texto_muy_largo", "This is a very long message that repeats itself. " * 20),
            ("caracteres_especiales", "Héllo wörld with ñ and ç"),
            ("emojis", "This is great! 😀🎉👍"),
            ("mixto_complejo", "THIS fucking RACIST shit 123 !!! makes me SICK"),
            
            # Casos límite con thresholds
            ("threshold_test", "This is moderately concerning content"),
            ("false_positive_test", "I hate waiting in traffic"),
            ("false_negative_test", "You are not very smart")
        ]
        
        results = []
        failed_cases = []
        
        for label, text in test_cases:
            print(f"\n{'=' * 60}")
            print(f"🔍 CASO: {label}")
            
            try:
                # Análisis detallado del pipeline
                analysis = self.analyze_text_processing_pipeline(text)
                
                # Predicción final del loader
                final_result = self.loader.predict(text, return_probabilities=True, return_categories=False)
                
                # Combinar resultados
                case_result = {
                    'label': label,
                    'text': text,
                    'analysis': analysis,
                    'final_result': final_result,
                    'success': analysis['success'] and 'error' not in final_result
                }
                
                results.append(case_result)
                
                if not case_result['success']:
                    failed_cases.append(case_result)
                    print(f"❌ CASO FALLIDO: {label}")
                else:
                    print(f"✅ CASO EXITOSO: {label}")
                    
            except Exception as e:
                print(f"💥 ERROR CRÍTICO en {label}: {e}")
                failed_cases.append({
                    'label': label,
                    'text': text,
                    'error': str(e),
                    'success': False
                })
        
        self.detailed_results = results
        return results, failed_cases
    
    def analyze_prediction_patterns(self, results):
        """Analiza patrones en las predicciones para detectar problemas sistemáticos"""
        print(f"\n📊 ANÁLISIS DE PATRONES DE PREDICCIÓN")
        print("=" * 50)
        
        patterns = {
            'probability_distributions': {},
            'threshold_effectiveness': {},
            'class_activation_patterns': {},
            'multi_label_patterns': {},
            'potential_issues': []
        }
        
        # Recopilar datos
        all_predictions = []
        for result in results:
            if result['success'] and 'predictions' in result['final_result']:
                all_predictions.append(result['final_result']['predictions'])
        
        if not all_predictions:
            self.log_issue("No hay predicciones válidas para analizar")
            return patterns
        
        class_names = self.config['classes']['class_names']
        
        # 1. Distribución de probabilidades por clase
        print("📈 Analizando distribución de probabilidades...")
        for class_name in class_names:
            probs = [pred[class_name]['probability'] for pred in all_predictions]
            patterns['probability_distributions'][class_name] = {
                'mean': np.mean(probs),
                'std': np.std(probs),
                'min': np.min(probs),
                'max': np.max(probs),
                'q25': np.percentile(probs, 25),
                'q75': np.percentile(probs, 75)
            }
            
            # Detectar clases problemáticas
            if np.std(probs) < 0.01:
                patterns['potential_issues'].append(f"Clase {class_name}: probabilidades muy constantes (std={np.std(probs):.4f})")
            
            if np.max(probs) < 0.1:
                patterns['potential_issues'].append(f"Clase {class_name}: probabilidades siempre muy bajas (max={np.max(probs):.4f})")
            
            if np.min(probs) > 0.9:
                patterns['potential_issues'].append(f"Clase {class_name}: probabilidades siempre muy altas (min={np.min(probs):.4f})")
        
        # 2. Efectividad de thresholds
        print("🎯 Analizando efectividad de thresholds...")
        thresholds = self.config['thresholds']
        
        for class_name in class_names:
            threshold = thresholds[class_name]
            probs = [pred[class_name]['probability'] for pred in all_predictions]
            detections = [pred[class_name]['detected'] for pred in all_predictions]
            
            above_threshold = sum(1 for p in probs if p > threshold)
            below_threshold = sum(1 for p in probs if p <= threshold)
            
            patterns['threshold_effectiveness'][class_name] = {
                'threshold': threshold,
                'above_threshold': above_threshold,
                'below_threshold': below_threshold,
                'detection_rate': sum(detections) / len(detections),
                'avg_margin': np.mean([p - threshold for p in probs])
            }
            
            # Detectar thresholds problemáticos
            if above_threshold == 0 and below_threshold > 0:
                patterns['potential_issues'].append(f"Threshold de {class_name} demasiado alto: ninguna predicción lo supera")
            
            if below_threshold == 0 and above_threshold > 0:
                patterns['potential_issues'].append(f"Threshold de {class_name} demasiado bajo: todas las predicciones lo superan")
        
        # 3. Patrones de activación
        print("🔍 Analizando patrones de activación...")
        activation_matrix = []
        for pred in all_predictions:
            activations = [1 if pred[class_name]['detected'] else 0 for class_name in class_names]
            activation_matrix.append(activations)
        
        activation_matrix = np.array(activation_matrix)
        
        for i, class_name in enumerate(class_names):
            activation_rate = np.mean(activation_matrix[:, i])
            patterns['class_activation_patterns'][class_name] = {
                'activation_rate': activation_rate,
                'never_activated': activation_rate == 0,
                'always_activated': activation_rate == 1
            }
            
            if activation_rate == 0:
                patterns['potential_issues'].append(f"Clase {class_name}: nunca se activa")
            elif activation_rate == 1:
                patterns['potential_issues'].append(f"Clase {class_name}: siempre se activa")
        
        # 4. Patrones multi-label
        print("🏷️ Analizando patrones multi-label...")
        multi_detections = [sum(activations) for activations in activation_matrix]
        patterns['multi_label_patterns'] = {
            'avg_detections_per_text': np.mean(multi_detections),
            'max_simultaneous': np.max(multi_detections),
            'single_label_rate': sum(1 for x in multi_detections if x == 1) / len(multi_detections),
            'multi_label_rate': sum(1 for x in multi_detections if x > 1) / len(multi_detections),
            'no_detection_rate': sum(1 for x in multi_detections if x == 0) / len(multi_detections)
        }
        
        return patterns
    
    def generate_detailed_report(self, results, failed_cases, patterns):
        """Genera un reporte detallado de todos los hallazgos"""
        print(f"\n📋 GENERANDO REPORTE DETALLADO")
        print("=" * 50)
        
        # Función para convertir numpy tipos a tipos Python nativos
        def convert_numpy_types(obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.bool_):
                return bool(obj)
            elif isinstance(obj, dict):
                return {k: convert_numpy_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(item) for item in obj]
            else:
                return obj
        
        report = {
            'summary': {
                'total_cases': len(results),
                'successful_cases': len([r for r in results if r['success']]),
                'failed_cases': len(failed_cases),
                'success_rate': len([r for r in results if r['success']]) / len(results) if results else 0,
                'total_issues': len(self.issues),
                'total_warnings': len(self.warnings)
            },
            'failed_cases': failed_cases,
            'patterns': convert_numpy_types(patterns),
            'issues': self.issues,
            'warnings': self.warnings,
            'recommendations': []
        }
        
        # Generar recomendaciones
        if patterns['potential_issues']:
            report['recommendations'].extend([
                "REVISAR THRESHOLDS: Algunos thresholds pueden necesitar ajuste",
                "VERIFICAR DATOS DE ENTRENAMIENTO: Patrones inusuales detectados"
            ])
        
        if failed_cases:
            report['recommendations'].append("CORREGIR CASOS FALLIDOS: Hay textos que causan errores")
        
        if report['summary']['success_rate'] < 0.95:
            report['recommendations'].append("MEJORAR ROBUSTEZ: Tasa de éxito menor al 95%")
        
        # Guardar reporte
        try:
            report_path = self.model_dir / "prediction_debug_report.json"
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"💾 Reporte guardado: {report_path}")
        except Exception as e:
            print(f"⚠️ Error guardando reporte: {e}")
            # Intentar guardar una versión simplificada
            try:
                simple_report = {
                    'summary': report['summary'],
                    'issues': self.issues,
                    'warnings': self.warnings,
                    'recommendations': report['recommendations']
                }
                report_path = self.model_dir / "prediction_debug_report_simple.json"
                with open(report_path, 'w', encoding='utf-8') as f:
                    json.dump(simple_report, f, indent=2, ensure_ascii=False)
                print(f"💾 Reporte simplificado guardado: {report_path}")
            except Exception as e2:
                print(f"❌ No se pudo guardar reporte: {e2}")
        
        return report
    
    def print_summary(self, report):
        """Imprime resumen final del análisis"""
        print(f"\n" + "=" * 60)
        print("📋 RESUMEN DE DEBUG DE PREDICCIONES")
        print("=" * 60)
        
        summary = report['summary']
        
        print(f"📊 ESTADÍSTICAS GENERALES:")
        print(f"   Total de casos probados: {summary['total_cases']}")
        print(f"   Casos exitosos: {summary['successful_cases']}")
        print(f"   Casos fallidos: {summary['failed_cases']}")
        print(f"   Tasa de éxito: {summary['success_rate']:.1%}")
        
        if report['failed_cases']:
            print(f"\n❌ CASOS FALLIDOS:")
            for case in report['failed_cases']:
                print(f"   - {case['label']}: {case.get('error', 'Ver análisis detallado')}")
        
        if report['patterns']['potential_issues']:
            print(f"\n⚠️ PROBLEMAS POTENCIALES:")
            for issue in report['patterns']['potential_issues']:
                print(f"   - {issue}")
        
        if report['issues']:
            print(f"\n❌ ISSUES CRÍTICOS:")
            for issue in report['issues']:
                print(f"   - {issue}")
        
        if report['warnings']:
            print(f"\n⚠️ ADVERTENCIAS:")
            for warning in report['warnings']:
                print(f"   - {warning}")
        
        if report['recommendations']:
            print(f"\n💡 RECOMENDACIONES:")
            for rec in report['recommendations']:
                print(f"   - {rec}")
        
        # Veredicto final
        if summary['failed_cases'] == 0 and len(report['issues']) == 0:
            print(f"\n🎉 MODELO FUNCIONA PERFECTAMENTE")
            print(f"   ✅ Todos los casos de test pasan")
            print(f"   ✅ No hay issues críticos")
            print(f"   ✅ Pipeline de predicción robusto")
        elif summary['success_rate'] >= 0.95 and len(report['issues']) <= 2:
            print(f"\n✅ MODELO FUNCIONA BIEN")
            print(f"   ✅ Alta tasa de éxito ({summary['success_rate']:.1%})")
            print(f"   ⚠️ Algunos issues menores a resolver")
        else:
            print(f"\n❌ MODELO REQUIERE ATENCIÓN")
            print(f"   ❌ Tasa de éxito baja o issues críticos")
            print(f"   🔧 Revisar recomendaciones urgentemente")
        
        print("=" * 60)
    
    def run_complete_debug(self):
        """Ejecuta debug completo de predicciones"""
        print(f"\n🚀 EJECUTANDO DEBUG COMPLETO DE PREDICCIONES")
        print("=" * 60)
        
        # Test de casos diversos
        results, failed_cases = self.test_diverse_text_cases()
        
        # Análisis de patrones
        patterns = self.analyze_prediction_patterns(results)
        
        # Generar reporte
        report = self.generate_detailed_report(results, failed_cases, patterns)
        
        # Mostrar resumen
        self.print_summary(report)
        
        return report

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Debug exhaustivo de predicciones del modelo Multitóxico')
    parser.add_argument('--model-dir', '-d', default='models/bilstm_advanced', 
                   help='Directorio del modelo (default: models/bilstm_advanced)')
    
    args = parser.parse_args()
    
    # Ejecutar debug
    debugger = PredictionDebugger(args.model_dir)
    report = debugger.run_complete_debug()
    
    return report

if __name__ == "__main__":
    main()