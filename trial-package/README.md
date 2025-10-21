# 🦏 Rhinometric - Plataforma de Observabilidad

**Versión Trial: 180 días (6 meses)**

Bienvenido a Rhinometric, la plataforma completa de observabilidad que integra métricas, logs y trazas distribuidas en una solución unificada.

---

## 🏷️ Acerca de Rhinometric

Rhinometric es una plataforma profesional de observabilidad que unifica:
- **Métricas** con Prometheus
- **Logs** con Loki
- **Trazas distribuidas** con Tempo
- **Visualización** con Grafana
- **Alerting** con Alertmanager

Todo integrado, configurado y soportado por el equipo de Rhinometric.

### 📧 Contacto

- **Soporte Técnico**: soporte@rhinometric.com
- **Ventas**: ventas@rhinometric.com
- **Información General**: info@rhinometric.com

---

## 📋 Contenido

- [Requisitos](#-requisitos)
- [Instalación Rápida](#-instalación-rápida-3-pasos)
- [Instalación Detallada](#-instalación-detallada)
- [Acceso a Servicios](#-acceso-a-servicios)
- [Uso Básico](#-uso-básico)
- [Comandos Útiles](#-comandos-útiles)
- [Solución de Problemas](#-solución-de-problemas)
- [Limitaciones Trial](#-limitaciones-de-la-versión-trial)
- [Soporte](#-soporte)

---

## 💻 Requisitos

### Hardware Mínimo
- **Procesador**: 4 núcleos (Intel Core i5 o superior)
- **RAM**: 8 GB (se recomiendan 16 GB)
- **Disco**: 20 GB de espacio libre
- **Sistema Operativo**: macOS 10.15+ (Catalina o superior)

### Software Necesario
- **Docker Desktop**: Versión 4.0 o superior
  - Descarga: https://www.docker.com/products/docker-desktop

> ⚠️ **IMPORTANTE**: Docker Desktop debe estar instalado y corriendo ANTES de continuar.

---

## 🚀 Instalación Rápida (3 Pasos)

### Paso 1: Instalar Docker Desktop

Si aún no tienes Docker Desktop:

1. Descarga desde: https://www.docker.com/products/docker-desktop
2. Instala la aplicación (arrastra a Aplicaciones)
3. Abre Docker Desktop y espera a que inicie
4. Verifica que el ícono de Docker en la barra superior muestre "Docker is running"

### Paso 2: Descomprimir el paquete

```bash
# Navega a donde descargaste el paquete
cd ~/Downloads

# Descomprime
unzip rhinometric-trial-v1.0.zip

# Entra al directorio
cd rhinometric-trial-v1.0
```

### Paso 3: Ejecutar el instalador

```bash
# Dar permisos de ejecución
chmod +x start-trial.sh

# Ejecutar instalador
./start-trial.sh
```

¡Eso es todo! El script te guiará paso a paso.

---

## 📖 Instalación Detallada

### 1. Verificar Docker

```bash
# Verificar que Docker está instalado
docker --version

# Verificar que Docker está corriendo
docker ps
```

Si ves errores, asegúrate de que Docker Desktop está abierto y corriendo.

### 2. Ejecutar el instalador

```bash
./start-trial.sh
```

El script:
- ✅ Verifica que Docker esté instalado y corriendo
- ✅ Verifica recursos del sistema
- ✅ Genera archivo `.env` con contraseñas seguras
- ✅ Crea directorios necesarios
- ✅ Genera licencia Trial de 180 días
- ✅ Descarga e inicia todos los servicios
- ✅ Muestra credenciales de acceso

### 3. Tiempo de instalación

- **Primera vez**: 5-10 minutos (descarga de imágenes Docker)
- **Siguientes veces**: 1-2 minutos

### 4. Durante la instalación

El script te preguntará:

```
Nombre del cliente u organización: [Introduce tu empresa]
¿Iniciar Rhinometric ahora? (S/n): S
```

---

## 🌐 Acceso a Servicios

Una vez instalado, accede a:

### 🎨 Grafana (Dashboard Principal)
```
URL:      http://localhost:3000
Usuario:  admin
Password: [ver archivo credentials.txt]
```

### 📈 Prometheus (Métricas)
```
URL: http://localhost:9090
```

### 📝 Loki (Logs)
```
URL: http://localhost:3100
```

### 🔍 Tempo (Trazas Distribuidas)
```
URL: http://localhost:3200
```

### 🚨 Alertmanager (Alertas)
```
URL: http://localhost:9093
```

### 🔑 License Dashboard (Monitoreo de Licencias)
```
URL: http://localhost:8080
```

### 🌐 Nginx (Proxy Unificado)
```
URL: http://localhost
```

---

## 🎓 Uso Básico

### Primer Login en Grafana

1. Abre: http://localhost:3000
2. Usuario: `admin`
3. Password: (busca en `credentials.txt`)
4. Explora los datasources predefinidos:
   - Prometheus
   - Loki
   - Tempo

### Ver Métricas del Sistema

1. En Grafana, ve a **Explore** (icono de brújula)
2. Selecciona datasource: **Prometheus**
3. Escribe query: `up`
4. Click en **Run Query**
5. Verás todos los servicios activos

### Ver Logs

1. En Grafana, ve a **Explore**
2. Selecciona datasource: **Loki**
3. Escribe query: `{job="grafana"}`
4. Verás los logs de Grafana

### Monitorear Licencias

1. Abre: http://localhost:8080
2. Verás dashboard con:
   - Licencias totales
   - Licencias activas
   - Días restantes
   - Estado de cada licencia

---

## 🛠️ Comandos Útiles

### Ver estado de servicios
```bash
docker compose ps
```

### Ver logs en tiempo real
```bash
# Todos los servicios
docker compose logs -f

# Solo Grafana
docker compose logs -f grafana

# Solo errores
docker compose logs | grep -i error
```

### Reiniciar servicios
```bash
# Reiniciar todo
docker compose restart

# Reiniciar servicio específico
docker compose restart grafana
```

### Detener servicios (sin borrar datos)
```bash
docker compose stop
```

### Iniciar servicios (después de detener)
```bash
docker compose start
```

### Ver uso de recursos
```bash
docker stats
```

### Detener y eliminar TODO (incluye datos)
```bash
# ⚠️ CUIDADO: Esto borra TODOS los datos
docker compose down -v
```

---

## 🔍 Solución de Problemas

### Docker no está corriendo

**Problema**: Error "Cannot connect to Docker daemon"

**Solución**:
1. Abre Docker Desktop desde Aplicaciones
2. Espera 30 segundos a que inicie
3. Vuelve a ejecutar `./start-trial.sh`

### Puerto ya en uso

**Problema**: Error "port is already allocated"

**Solución**:
```bash
# Ver qué proceso usa el puerto 3000
lsof -i :3000

# Matar el proceso (reemplaza PID con el número que aparece)
kill -9 PID

# O cambiar puertos editando docker-compose.yml
```

### Servicios no inician

**Problema**: Contenedores se detienen inmediatamente

**Solución**:
```bash
# Ver logs detallados
docker compose logs

# Verificar memoria disponible
docker info | grep Memory

# Docker Desktop debe tener al menos 6GB asignados
```

### Grafana no carga

**Problema**: http://localhost:3000 no responde

**Solución**:
```bash
# Verificar que Grafana está corriendo
docker compose ps grafana

# Ver logs de Grafana
docker compose logs grafana

# Reiniciar Grafana
docker compose restart grafana

# Esperar 30 segundos y probar de nuevo
```

### Olvidé la contraseña de Grafana

**Solución**:
```bash
# Ver credenciales guardadas
cat credentials.txt

# O consultar archivo .env
cat .env | grep GRAFANA_PASSWORD
```

### Limpieza completa y reinicio

```bash
# 1. Detener y eliminar todo
docker compose down -v

# 2. Limpiar datos (opcional)
rm -rf data/ licenses/ .env credentials.txt

# 3. Volver a instalar
./start-trial.sh
```

---

## ⚖️ Limitaciones de la Versión Trial

Esta versión Trial incluye las siguientes limitaciones:

### ⏱️ Duración
- **180 días** (6 meses) desde la instalación
- Después de este periodo, necesitarás una licencia comercial

### 📊 Retención de Datos
- **7 días** de retención en Prometheus
- **7 días** de retención en Loki
- **7 días** de retención en Tempo

### 👥 Usuarios
- Máximo **5 usuarios** en Grafana
- Sin autenticación multi-factor
- Sin SSO/LDAP

### 🚫 No Incluye
- Alta disponibilidad (HA)
- Backups automáticos
- Soporte 24/7
- Personalización de marca (White Label)
- Integraciones empresariales
- Almacenamiento remoto (S3, GCS)

### ✅ Incluye (Completamente Funcional)
- ✅ Grafana completo
- ✅ Prometheus (métricas)
- ✅ Loki (logs)
- ✅ Tempo (trazas distribuidas)
- ✅ Alertmanager
- ✅ Exportadores de sistema (Node, cAdvisor)
- ✅ Dashboard de licencias
- ✅ Nginx como proxy
- ✅ Provisionamiento automático de datasources

---

## 🎯 Conversión a Versión Comercial

### Características de la Versión Comercial

| Característica | Trial | Comercial |
|----------------|-------|-----------|
| Duración | 180 días | Ilimitado |
| Retención de datos | 7 días | Personalizable |
| Alta disponibilidad | ❌ | ✅ |
| Usuarios | 5 máx. | Ilimitados |
| Soporte | Email básico | 24/7 + Teléfono |
| Backups | Manual | Automáticos |
| White Label | ❌ | ✅ |
| SLA | Sin garantía | 99.9% |
| Almacenamiento | Local | S3/GCS/Azure |
| Multi-tenant | ❌ | ✅ |

### Contacto Comercial

Para convertir tu trial a versión comercial:

📧 **Email**: ventas@rhinometric.com  
📞 **Teléfono**: +34 XXX XXX XXX  
🌐 **Web**: https://rhinometric.com/pricing

---

## 📚 Recursos Adicionales

### Documentación

- **Grafana**: https://grafana.com/docs/
- **Prometheus**: https://prometheus.io/docs/
- **Loki**: https://grafana.com/docs/loki/
- **Tempo**: https://grafana.com/docs/tempo/

### Tutoriales Recomendados

1. **Grafana Fundamentals**: https://grafana.com/tutorials/grafana-fundamentals/
2. **Prometheus Basics**: https://prometheus.io/docs/introduction/first_steps/
3. **Loki Quickstart**: https://grafana.com/docs/loki/latest/getting-started/

---

## 📞 Soporte

### Soporte Trial (Email)

📧 **soporte@rhinometric.com**

**Tiempo de respuesta**: 24-48 horas hábiles

### FAQ y Troubleshooting

Consulta: `docs/FAQ.md` y `docs/TROUBLESHOOTING.md`

### Comunidad

- **Slack**: [Unirse a la comunidad](https://rhinometric.slack.com)
- **GitHub**: [Reportar issues](https://github.com/rhinometric/issues)

---

## 📄 Licencia y Legal

### Términos de Uso Trial

Esta versión Trial de Rhinometric está proporcionada bajo los siguientes términos:

#### ✅ Uso Permitido:
- Evaluación del producto en entornos no productivos
- Testing y pruebas de concepto (POC)
- Demos comerciales internas
- Formación y capacitación del equipo

#### ❌ Uso NO Permitido:
- Despliegue en entornos de producción
- Redistribución o reventa del software
- Modificación del código fuente
- Uso comercial sin licencia válida
- Uso después de los 180 días de trial

**Términos completos**: Ver `LICENSE.txt` en este directorio.

### 🔓 Componentes Open Source

Rhinometric utiliza y agradece a los siguientes proyectos open source:

| Componente | Licencia | Propósito |
|------------|----------|-----------|
| **Grafana** | Apache 2.0 | Visualización de datos |
| **Prometheus** | Apache 2.0 | Recolección de métricas |
| **Loki** | Apache 2.0 | Gestión de logs |
| **Tempo** | Apache 2.0 | Trazas distribuidas |
| **PostgreSQL** | PostgreSQL License | Base de datos |
| **Redis** | BSD 3-Clause | Cache y sesiones |
| **Alertmanager** | Apache 2.0 | Gestión de alertas |

**Nota importante**: Aunque estos componentes son open source, la **integración, configuración personalizada, dashboards, sistema de licencias y soporte técnico** son proporcionados por Rhinometric y están sujetos a la licencia trial.

Para detalles completos de las licencias de terceros, ver `THIRD_PARTY_LICENSES.txt`.

---

## ✅ Checklist Post-Instalación

Después de instalar, verifica:

- [ ] Grafana accesible en http://localhost:3000
- [ ] Login exitoso con admin + password
- [ ] Prometheus muestra métricas (query `up` en Explore)
- [ ] Loki recibe logs
- [ ] Tempo está disponible
- [ ] License Dashboard muestra tu licencia
- [ ] Archivo `credentials.txt` guardado en lugar seguro
- [ ] Todos los servicios corriendo (`docker compose ps`)

---

## 🎉 ¡Listo para Empezar!

Tu plataforma Rhinometric Trial está lista para usar.

**Próximos pasos sugeridos**:

1. Explora Grafana y los dashboards predefinidos
2. Crea tu primer dashboard personalizado
3. Configura alertas en Alertmanager
4. Integra tus aplicaciones con Prometheus
5. Envía logs a Loki desde tus servicios

**¿Necesitas ayuda?** → soporte@rhinometric.com

---

<div align="center">

**Rhinometric** - Observabilidad Unificada

© 2025 Rhinometric. Todos los derechos reservados.

</div>
