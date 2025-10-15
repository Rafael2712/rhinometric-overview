#!/bin/bash

echo "🔥 Enviando logs REALES a Loki..."

# Generar logs con formato correcto
for i in {1..20}; do
    TIMESTAMP=$(date +%s)000000000  # Nanoseconds
    LEVEL=$([ $((i % 4)) -eq 0 ] && echo "ERROR" || [ $((i % 3)) -eq 0 ] && echo "WARN" || echo "INFO")
    MESSAGE="Enterprise log $i - $LEVEL from rhinometric-api"
    
    # Formato JSON correcto para Loki
    curl -v -H "Content-Type: application/json" \
         -X POST "http://localhost:3100/loki/api/v1/push" \
         -d "{
             \"streams\": [
                 {
                     \"stream\": {
                         \"job\": \"rhinometric-api\",
                         \"level\": \"$LEVEL\",
                         \"service\": \"rhinometric-api\",
                         \"environment\": \"enterprise\"
                     },
                     \"values\": [
                         [\"$TIMESTAMP\", \"$MESSAGE\"]
                     ]
                 }
             ]
         }"
    
    echo "✅ Log $i enviado: $MESSAGE"
    sleep 0.5
done

echo "🎉 Logs enterprise enviados a Loki!"