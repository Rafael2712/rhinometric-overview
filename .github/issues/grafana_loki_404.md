# Issue: Página 404 en Grafana al acceder a logs de Loki

## Descripción
Cuando se intenta acceder a la página de logs de Loki directamente en Grafana, se muestra un error 404.
Sin embargo, los logs son accesibles a través de la sección Explore de Grafana.

## Estado actual
- Loki está funcionando y recolectando logs
- Los logs son consultables desde Grafana Explore
- La integración básica funciona correctamente

## Impacto
- Bajo: No afecta la funcionalidad principal
- Los usuarios pueden acceder a los logs mediante Explore

## Para resolver en el futuro
- Investigar la configuración de rutas en Grafana
- Verificar la integración de plugins de Loki en Grafana
- Revisar los datasources de Grafana
