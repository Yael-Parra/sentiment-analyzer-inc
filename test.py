#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 SCRIPT DE PRUEBA MODELO MULTITOXIC
🎯 Verifica funcionamiento completo del modelo exportado
📁 Ejecutar desde la raíz del proyecto
"""

import os
import sys
import json
from pathlib import Path
import time

# Configuración de rutas
PROJECT_ROOT = Path(__file__).parent
MODELS_DIR = PROJECT_ROOT / "models" / "bilstm_advanced"

print("🚀 PROBANDO MODELO MULTITOXIC")
print("=" * 50)
print(f"📁 Directorio del proyecto: {PROJECT_ROOT}")
print(f"📁 Directorio de modelos: {MODELS_DIR}")

# ======================
# 1. VERIFICAR ARCHIVOS
# ======================
print(f"\n🔍 1. VERIFICANDO ARCHIVOS DEL MODELO...")

if not MODELS_DIR.exists():
    print(f"❌ ERROR: Directorio de modelos no encontrado")
    print(f"   Esperado: {MODELS_DIR}")
    print(f"   Verificar que la exportación se haya completado")
    sys.exit(1)

# Buscar archivos del modelo más reciente
model_files = {
    'config': list(MODELS_DIR.glob("multitoxic_v1.0_*_config.json")),
    'loader': list(MODELS_DIR.glob("multitoxic_v1.0_*_loader.py")),
    'processor': list(MODELS_DIR.glob("multitoxic_v1.0_*_processor.pkl")),
    'features': list(MODELS_DIR.glob("multitoxic_v1.0_*_features.pkl")),
    'model': list(MODELS_DIR.glob("multitoxic_v1.0_*_model.pth"))
}

# Verificar que todos los archivos existen
missing_files = []
for file_type, files in model_files.items():
    if not files:
        missing_files.append(file_type)
    else:
        print(f"   ✅ {file_type}: {files[0].name}")

if missing_files:
    print(f"❌ ERROR: Archivos faltantes: {', '.join(missing_files)}")
    print(f"   Ejecutar la exportación del modelo primero")
    sys.exit(1)

# Usar el modelo más reciente (por timestamp)
latest_config = max(model_files['config'], key=lambda x: x.stat().st_mtime)
model_version = latest_config.stem.replace('_config', '')

print(f"✅ Archivos encontrados")
print(f"🏷️  Versión del modelo: {model_version}")

# ======================
# 2. CARGAR CONFIGURACIÓN
# ======================
print(f"\n📊 2. CARGANDO CONFIGURACIÓN...")

try:
    with open(latest_config, 'r') as f:
        config = json.load(f)
    
    print(f"   📊 Performance: F1-macro {config['performance']['test_metrics']['f1_macro']:.4f}")
    print(f"   🧠 Parámetros: {config['metadata']['total_parameters']:,}")
    print(f"   🏷️  Clases: {len(config['classes']['class_names'])}")
    print(f"   🔧 Features: {config['dataset_info']['features_count']}")
    
except Exception as e:
    print(f"❌ ERROR cargando configuración: {e}")
    sys.exit(1)

# ======================
# 3. IMPORTAR LOADER
# ======================
print(f"\n🔄 3. IMPORTANDO LOADER...")

# Añadir directorio de modelos al path para importar el loader
sys.path.insert(0, str(MODELS_DIR))

try:
    # Importar el módulo del loader dinámicamente
    loader_file = model_files['loader'][0]
    spec = None
    
    # Método alternativo más robusto
    import importlib.util
    spec = importlib.util.spec_from_file_location("multitoxic_loader", loader_file)
    loader_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loader_module)
    
    # Obtener la clase MultitoxicLoader
    MultitoxicLoader = loader_module.MultitoxicLoader
    print(f"   ✅ Loader importado exitosamente")
    
except Exception as e:
    print(f"❌ ERROR importando loader: {e}")
    print(f"   Verificar dependencias: pip install torch numpy pandas scikit-learn dill tqdm")
    sys.exit(1)

# ======================
# 4. CARGAR MODELO
# ======================
print(f"\n🧠 4. CARGANDO MODELO MULTITOXIC...")

try:
    start_time = time.time()
    
    # Inicializar loader
    loader = MultitoxicLoader(str(MODELS_DIR))
    
    # Cargar modelo usando el patrón de versión
    version_pattern = model_version.replace('multitoxic_v1.0_', '')
    loader.load_model(version_pattern)
    
    load_time = time.time() - start_time
    print(f"   ✅ Modelo cargado en {load_time:.2f} segundos")
    print(f"   🎯 Dispositivo: {loader.device}")
    
except Exception as e:
    print(f"❌ ERROR cargando modelo: {e}")
    print(f"   Verificar dependencias de PyTorch")
    sys.exit(1)

# ======================
# 5. PRUEBAS FUNCIONALES
# ======================
print(f"\n🧪 5. EJECUTANDO PRUEBAS FUNCIONALES...")

# Casos de prueba comprehensivos
test_cases = [
    {
        'name': 'Texto Limpio',
        'text': 'This is a great video, thanks for sharing! Very helpful content.',
        'expected': []
    },
    {
        'name': 'Toxicidad General',
        'text': 'You are so fucking stupid and annoying',
        'expected': ['toxic', 'abusive']
    },
    {
        'name': 'Contenido Racista',
        'text': 'These people are inferior animals and should go back',
        'expected': ['racist', 'hatespeech']
    },
    {
        'name': 'Amenaza Directa',
        'text': "I'm gonna find you and make you pay for this",
        'expected': ['threat', 'toxic']
    },
    {
        'name': 'Contenido Sexista',
        'text': 'Women should stay in the kitchen and shut up',
        'expected': ['sexist', 'hatespeech']
    },
    {
        'name': 'Homofobia',
        'text': 'Those gay perverts make me sick, disgusting filth',
        'expected': ['homophobic', 'hatespeech']
    },
    {
        'name': 'Multi-tóxico Complejo',
        'text': 'Stupid fucking women and their gay agenda, time for revolution',
        'expected': ['toxic', 'sexist', 'homophobic', 'radicalism']
    },
    {
        'name': 'Nacionalismo Extremo',
        'text': 'Real Americans need to take back our country from these inferior people',
        'expected': ['nationalist', 'racist']
    }
]

# Ejecutar pruebas
results = []
total_tests = len(test_cases)
passed_tests = 0

print(f"   🔬 Ejecutando {total_tests} casos de prueba...")

for i, test_case in enumerate(test_cases, 1):
    try:
        start_time = time.time()
        
        # Realizar predicción
        result = loader.predict(
            test_case['text'], 
            return_probabilities=True,
            return_categories=True,
            return_details=True
        )
        
        prediction_time = time.time() - start_time
        
        # Analizar resultado
        detected = result['detected_types']
        is_multi_toxic = result['is_multi_toxic']
        severity = result['severity']
        
        # Determinar si pasó la prueba
        if test_case['expected']:
            # Para casos tóxicos, verificar que se detecte al menos una categoría esperada
            test_passed = any(expected in detected for expected in test_case['expected'])
        else:
            # Para casos limpios, verificar que no se detecte toxicidad
            test_passed = len(detected) == 0
        
        if test_passed:
            passed_tests += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        print(f"\n   📝 Test {i}/{total_tests}: {test_case['name']} {status}")
        print(f"      Texto: {test_case['text'][:60]}{'...' if len(test_case['text']) > 60 else ''}")
        print(f"      Detectado: {detected if detected else ['CLEAN']}")
        print(f"      Esperado: {test_case['expected'] if test_case['expected'] else ['CLEAN']}")
        print(f"      Multi-tóxico: {is_multi_toxic}")
        print(f"      Severidad: {severity}")
        print(f"      Tiempo: {prediction_time:.3f}s")
        
        # Mostrar categorías si están disponibles
        if 'categories' in result and result['categories']['detections']:
            detected_cats = {k: v for k, v in result['categories']['detections'].items() if v}
            if detected_cats:
                print(f"      Categorías: {detected_cats}")
        
        results.append({
            'name': test_case['name'],
            'passed': test_passed,
            'detected': detected,
            'expected': test_case['expected'],
            'time': prediction_time
        })
        
    except Exception as e:
        print(f"   ❌ ERROR en test {i}: {e}")
        results.append({
            'name': test_case['name'],
            'passed': False,
            'error': str(e)
        })

# ======================
# 6. ANÁLISIS DE RESULTADOS
# ======================
print(f"\n📊 6. ANÁLISIS DE RESULTADOS...")

success_rate = (passed_tests / total_tests) * 100
avg_time = sum(r['time'] for r in results if 'time' in r) / len([r for r in results if 'time' in r])

print(f"   🎯 Tests pasados: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
print(f"   ⚡ Tiempo promedio de predicción: {avg_time:.3f}s")

# Análisis por categorías
categories_tested = set()
for test_case in test_cases:
    categories_tested.update(test_case['expected'])

print(f"   🏷️  Categorías probadas: {len(categories_tested)} ({', '.join(sorted(categories_tested)[:5])}...)")

# ======================
# 7. PRUEBA DE RENDIMIENTO
# ======================
print(f"\n⚡ 7. PRUEBA DE RENDIMIENTO...")

performance_text = "This is a sample text for performance testing. " * 5

try:
    # Múltiples predicciones para medir rendimiento
    times = []
    for _ in range(5):
        start_time = time.time()
        loader.predict(performance_text)
        times.append(time.time() - start_time)
    
    avg_perf_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    
    print(f"   📊 Tiempo promedio: {avg_perf_time:.3f}s")
    print(f"   📊 Tiempo mínimo: {min_time:.3f}s")
    print(f"   📊 Tiempo máximo: {max_time:.3f}s")
    print(f"   🚀 Throughput estimado: ~{1/avg_perf_time:.1f} predicciones/segundo")
    
except Exception as e:
    print(f"   ❌ ERROR en prueba de rendimiento: {e}")

# ======================
# 8. RESUMEN FINAL
# ======================
print(f"\n" + "=" * 50)
print(f"📋 RESUMEN DE PRUEBAS MULTITOXIC")
print(f"=" * 50)

print(f"🏷️  Modelo: {model_version}")
print(f"📊 Performance esperada: F1-macro {config['performance']['test_metrics']['f1_macro']:.4f}")
print(f"🧠 Parámetros: {config['metadata']['total_parameters']:,}")
print(f"🔧 Features: {config['dataset_info']['features_count']}")

print(f"\n🧪 RESULTADOS DE PRUEBAS:")
print(f"   ✅ Tests pasados: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
print(f"   ⚡ Rendimiento: ~{1/avg_time:.1f} predicciones/segundo")
print(f"   🎯 Funcionalidad: {'COMPLETA' if success_rate >= 75 else 'PARCIAL' if success_rate >= 50 else 'LIMITADA'}")

if success_rate >= 75:
    print(f"\n🎉 ¡MODELO MULTITOXIC FUNCIONANDO CORRECTAMENTE!")
    print(f"✅ Listo para usar en producción")
    print(f"🚀 Todas las funcionalidades principales verificadas")
elif success_rate >= 50:
    print(f"\n⚠️  Modelo funcionando con limitaciones")
    print(f"🔧 Revisar casos fallidos para ajustes")
else:
    print(f"\n❌ Modelo con problemas significativos")
    print(f"🔧 Revisar configuración y dependencias")

print(f"\n💻 EJEMPLO DE USO:")
print(f"```python")
print(f"from models.bilstm_advanced.{model_version}_loader import MultitoxicLoader")
print(f"loader = MultitoxicLoader('models/bilstm_advanced')")
print(f"loader.load_model()")
print(f"result = loader.predict('Your text here')")
print(f"print(result['detected_types'])")
print(f"```")

print(f"\n🔧 DEPENDENCIAS VERIFICADAS:")
try:
    import torch
    import numpy
    import pandas
    import sklearn
    import dill
    print(f"   ✅ Todas las dependencias principales disponibles")
except ImportError as e:
    print(f"   ⚠️  Dependencia faltante: {e}")

print(f"\n" + "=" * 50)
print(f"✅ PRUEBA COMPLETADA")
print(f"📅 {time.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"=" * 50)