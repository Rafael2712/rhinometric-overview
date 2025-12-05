#!/bin/bash
# Script para verificar trazas en Tempo

echo "Consultando trazas en Tempo de los ultimos 10 minutos..."
echo ""

START=$(( $(date +%s) - 600 ))
END=$(date +%s)

curl -s "http://localhost:3200/api/search?q=%7B%7D&limit=100&start=$START&end=$END" | python3 -c "
import sys, json
data = json.load(sys.stdin)
traces = data.get('traces', [])
print('Total de trazas: ' + str(len(traces)))
print('')
print('Trazas por servicio:')
print('')
from collections import Counter
services = Counter([t['rootServiceName'] for t in traces])
for service, count in services.most_common():
    print('   ' + service + ': ' + str(count) + ' trazas')
print('')
print('Servicios unicos: ' + str(len(services)))
"
