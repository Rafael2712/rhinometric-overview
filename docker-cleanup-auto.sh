#!/bin/bash
# Script de limpieza automÃ¡tica para Docker
# Previene acumulaciÃ³n de espacio en disco

echo "í·¹ [$(date '+%Y-%m-%d %H:%M:%S')] Iniciando limpieza automÃ¡tica de Docker..."

# 1. Eliminar contenedores detenidos
echo "í³¦ Eliminando contenedores detenidos..."
docker container prune -f 2>&1 | grep -v "^$"

# 2. Eliminar imÃ¡genes sin usar (mantener Ãºltimos 7 dÃ­as)
echo "í¶¼ï¸  Eliminando imÃ¡genes antiguas (>7 dÃ­as)..."
docker image prune -a -f --filter "until=168h" 2>&1 | grep -v "^$"

# 3. Eliminar volÃºmenes huÃ©rfanos
echo "í²¾ Eliminando volÃºmenes sin usar..."
docker volume prune -f 2>&1 | grep -v "^$"

# 4. Limpiar build cache (mantener Ãºltimos 7 dÃ­as)
echo "í¿—ï¸  Limpiando cache de builds..."
docker builder prune -a -f --filter "until=168h" 2>&1 | grep -v "^$"

# 5. Mostrar espacio recuperado
echo ""
echo "í³Š Estado del disco despuÃ©s de limpieza:"
df -h / | tail -1 | awk '{print "   Usado: "$3" / "$2" total ("$5") - Libre: "$4}'

# 6. Mostrar uso de Docker
echo ""
echo "í°³ Espacio usado por Docker:"
docker system df 2>/dev/null | tail -n +2

echo ""
echo "âœ… [$(date '+%Y-%m-%d %H:%M:%S')] Limpieza completada"
echo "=================================================="
