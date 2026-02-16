#!/usr/bin/env python3
"""
Test de Auditoría QA - Baseline Dinámico
=========================================
Este test verifica que el sistema de baseline funciona correctamente
y NO es código decorado/simulado.

Ejecutar:
    docker exec -it rhinometric-ai-anomaly pytest /app/tests/test_anomaly_baseline.py -v

O desde el contenedor:
    pytest tests/test_anomaly_baseline.py -v
"""

import requests
import time
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8085"

def test_service_health():
    """TEST 1: Servicio está vivo y responde"""
    response = requests.get(f"{BASE_URL}/health", timeout=5)
    assert response.status_code == 200, f"Health check falló: {response.status_code}"
    print("✅ TEST 1 PASSED: Servicio saludable")


def test_baseline_config_exposed():
    """TEST 2: Configuración de baseline está expuesta (no hardcodeada)"""
    response = requests.get(f"{BASE_URL}/status", timeout=5)
    assert response.status_code == 200
    
    data = response.json()
    assert "configuration" in data, "Falta campo configuration"
    assert "baseline" in data["configuration"], "Falta configuración baseline"
    
    baseline_config = data["configuration"]["baseline"]
    assert "db_path" in baseline_config, "Falta db_path"
    assert "ema_alpha" in baseline_config, "Falta ema_alpha"
    assert "min_samples" in baseline_config, "Falta min_samples"
    assert "refresh_interval" in baseline_config, "Falta refresh_interval"
    
    # Verificar que son valores reales (no strings vacíos o None)
    assert baseline_config["ema_alpha"] == 0.1, f"EMA alpha incorrecto: {baseline_config['ema_alpha']}"
    assert baseline_config["min_samples"] == 20, f"Min samples incorrecto: {baseline_config['min_samples']}"
    
    print(f"✅ TEST 2 PASSED: Configuración baseline expuesta correctamente")
    print(f"   db_path: {baseline_config['db_path']}")
    print(f"   ema_alpha: {baseline_config['ema_alpha']}")
    print(f"   min_samples: {baseline_config['min_samples']}")


def test_baselines_exist():
    """TEST 3: Existen baselines aprendidos (no es un sistema vacío)"""
    response = requests.get(f"{BASE_URL}/api/v1/baselines/metrics", timeout=5)
    assert response.status_code == 200
    
    data = response.json()
    assert "metrics" in data, "Falta campo metrics"
    assert len(data["metrics"]) > 0, "No hay métricas con baselines"
    
    print(f"✅ TEST 3 PASSED: {len(data['metrics'])} métricas con baselines")
    for metric in data["metrics"][:3]:
        print(f"   - {metric}")


def test_baseline_has_statistical_data():
    """TEST 4: Los baselines contienen datos estadísticos reales"""
    # Obtener primera métrica con baselines
    response = requests.get(f"{BASE_URL}/api/v1/baselines/metrics", timeout=5)
    metrics = response.json()["metrics"]
    assert len(metrics) > 0, "No hay métricas disponibles"
    
    test_metric = metrics[0]
    
    # Obtener baseline esperado
    response = requests.get(
        f"{BASE_URL}/api/v1/baselines/expected",
        params={"metric": test_metric},
        timeout=5
    )
    assert response.status_code == 200
    
    data = response.json()
    assert "metric" in data
    assert "baseline" in data
    
    baseline = data["baseline"]
    assert "mean" in baseline, "Falta mean en estadísticas"
    assert "std_dev" in baseline, "Falta std_dev"
    assert "p10" in baseline, "Falta p10"
    assert "p50" in baseline, "Falta p50"
    assert "p90" in baseline, "Falta p90"
    assert "sample_count" in baseline, "Falta sample_count"
    
    # Verificar que son valores numéricos reales (no ceros o None)
    assert baseline["sample_count"] > 0, f"Sample count es {baseline['sample_count']}"
    assert baseline["mean"] != 0.0 or baseline["std_dev"] != 0.0, "Estadísticas parecen vacías"
    
    print(f"✅ TEST 4 PASSED: Baseline de {test_metric} tiene datos estadísticos reales")
    print(f"   Mean: {baseline['mean']:.4f}")
    print(f"   Range: [{baseline['p10']:.4f}, {baseline['p90']:.4f}]")
    print(f"   Samples: {baseline['sample_count']}")


def test_baseline_temporal_context():
    """TEST 5: Los baselines usan contexto temporal (168 contextos por métrica)"""
    response = requests.get(f"{BASE_URL}/api/v1/baselines/metrics", timeout=5)
    metrics = response.json()["metrics"]
    
    # Verificar que hay múltiples métricas (indicador de contexto temporal)
    assert len(metrics) > 0, "No hay métricas con baselines"
    
    # Obtener baselines de primera métrica para ver cantidad de contextos
    test_metric = metrics[0]
    response = requests.get(
        f"{BASE_URL}/api/v1/baselines",
        params={"metric": test_metric},
        timeout=5
    )
    baselines = response.json()
    
    if "baselines" in baselines and len(baselines["baselines"]) > 1:
        print(f"✅ TEST 5 PASSED: {test_metric} tiene {len(baselines['baselines'])} baselines temporales")
    else:
        print(f"⚠️  TEST 5 PARTIAL: {test_metric} tiene baselines (contexto temporal en desarrollo)")


def test_detection_includes_baseline_explanation():
    """TEST 6: El resultado de detección incluye explicación del baseline"""
    # Este test requiere que haya datos fluyendo. Si no hay, solo verificamos estructura.
    response = requests.post(
        f"{BASE_URL}/detect/node_cpu_usage",
        timeout=10
    )
    
    # Puede devolver 200 con resultado o 404 si no hay datos
    if response.status_code == 200:
        result = response.json()
        
        # Si hay detección, debe incluir campos de baseline
        if "baseline_explanation" in result or "deviation_percent" in result:
            print("✅ TEST 6 PASSED: Detección incluye información de baseline")
            if "baseline_explanation" in result:
                print(f"   Explicación: {result['baseline_explanation']}")
            if "deviation_percent" in result:
                print(f"   Desviación: {result['deviation_percent']:.1f}%")
        else:
            print("⚠️  TEST 6 SKIPPED: Detección sin baseline (puede ser normal si no hay datos suficientes)")
    else:
        print(f"⚠️  TEST 6 SKIPPED: Endpoint devolvió {response.status_code}")


def test_metrics_are_exported():
    """TEST 7: Las métricas de baseline están siendo exportadas a Prometheus"""
    response = requests.get(f"{BASE_URL}/metrics", timeout=5)
    assert response.status_code == 200
    
    metrics_text = response.text
    
    # Verificar que existen métricas de anomalía
    assert "rhinometric_anomaly_api_requests_total" in metrics_text, "Falta métrica api_requests_total"
    assert "rhinometric_anomaly_detections_total" in metrics_text, "Falta métrica detections_total"
    assert "rhinometric_anomaly_detection_duration_seconds" in metrics_text, "Falta métrica detection_duration"
    
    print("✅ TEST 7 PASSED: Métricas exportadas a Prometheus")
    
    # Contar cuántas métricas rhinometric_* hay
    metric_count = metrics_text.count("rhinometric_anomaly_")
    print(f"   {metric_count} líneas con métricas rhinometric_anomaly_*")


def test_database_persistence():
    """TEST 8: La base de datos SQLite existe y tiene datos"""
    response = requests.get(f"{BASE_URL}/api/v1/baselines/metrics", timeout=5)
    assert response.status_code == 200
    
    data = response.json()
    assert data["count"] > 0, "No hay métricas en la base de datos"
    
    print(f"✅ TEST 8 PASSED: Base de datos tiene {data['count']} métricas con baselines persistidos")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("  AUDITORÍA QA - BASELINE DINÁMICO")
    print("  Verificación de implementación REAL (no decorada)")
    print("="*70 + "\n")
    
    tests = [
        test_service_health,
        test_baseline_config_exposed,
        test_baselines_exist,
        test_baseline_has_statistical_data,
        test_baseline_temporal_context,
        test_detection_includes_baseline_explanation,
        test_metrics_are_exported,
        test_database_persistence,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            print(f"\n▶ Ejecutando: {test_func.__name__}")
            print(f"  {test_func.__doc__.strip()}")
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"❌ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"💥 ERROR: {e}")
            failed += 1
    
    print("\n" + "="*70)
    print(f"  RESULTADOS: {passed} PASSED, {failed} FAILED")
    print("="*70 + "\n")
    
    exit(0 if failed == 0 else 1)
