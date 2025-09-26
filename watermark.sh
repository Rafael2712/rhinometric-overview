#!/bin/bash
# Insertar marca oculta en logs
echo "<!-- RHN:$(date +%s):$(hostname) -->" >> /var/log/grafana.log
