#!/bin/bash
# Monitoreo continuo de generación de baselines
# Ejecutar: bash monitor_baselines.sh

echo "🔍 MONITOR BASELINES - Actualización cada 10min"
echo "================================================"
echo ""

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$TIMESTAMP] Verificando baselines..."
    
    # Query baselines desde API
    BASELINES=$(curl -s http://localhost:8085/api/v1/baselines/metrics 2>/dev/null)
    COUNT=$(echo "$BASELINES" | python -m json.tool 2>/dev/null | grep '"count"' | grep -o '[0-9]*')
    
    if [ -z "$COUNT" ]; then
        echo "  ⚠️  Error conectando al servicio"
    else
        echo "  📊 Métricas con baselines: $COUNT"
        
        # Verificar baselines en DB
        DB_COUNT=$(docker exec rhinometric-ai-anomaly python3 -c "
import sys
sys.path.insert(0, '/app')
from app.database import db
baselines = db.get_all_baselines()
print(len(baselines))
" 2>/dev/null)
        
        echo "  💾 Baselines en DB: $DB_COUNT"
        
        if [ "$DB_COUNT" -gt 0 ]; then
            echo "  ✅ Baselines generándose correctamente"
            
            # Actualizar métricas Prometheus
            docker exec rhinometric-ai-anomaly python3 -c "
import sys
sys.path.insert(0, '/app')
from app.api import update_baseline_metrics
update_baseline_metrics()
print('Métricas Prometheus actualizadas')
" 2>&1 | grep -v "^$"
            
            # Verificar métrica exportada
            METRIC_COUNT=$(curl -s http://localhost:8085/metrics 2>/dev/null | grep -c "rhinometric_baseline_count{")
            echo "  📈 Métricas exportadas: $METRIC_COUNT"
        fi
    fi
    
    echo ""
    echo "  💤 Próxima verificación en 10 minutos..."
    echo ""
    
    sleep 600  # 10 minutos
done
