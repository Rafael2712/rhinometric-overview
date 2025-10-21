# 📦 RHINOMETRIC TRIAL - INSTRUCCIONES DE ENTREGA

## 🎯 PARA TI (QUIEN ENVÍA EL PAQUETE)

### Archivo a Enviar

**Ubicación**: `c:\Users\canel\mi-proyecto\infrastructure\mi-proyecto\rhinometric-trial-v1.0.0.zip`

**Tamaño**: ~40 KB

**Contenido**: Todo lo necesario para instalar Rhinometric Trial

---

## 📧 EMAIL PARA ENVIAR AL CLIENTE

```
Asunto: Rhinometric Trial - Instalación (180 días)

Hola [Nombre del Cliente],

Te envío el paquete de instalación de Rhinometric Trial, válido por 180 días.

IMPORTANTE: Antes de empezar, necesitas tener Docker Desktop instalado.

════════════════════════════════════════════════════════════════

PASO 1: INSTALAR DOCKER DESKTOP (si no lo tienes)

1. Descarga desde: https://www.docker.com/products/docker-desktop
2. Abre el archivo .dmg descargado
3. Arrastra Docker a la carpeta Aplicaciones
4. Abre Docker Desktop desde Aplicaciones
5. Espera a que aparezca el ícono de Docker en la barra superior
6. Cuando diga "Docker Desktop is running", continúa al Paso 2

════════════════════════════════════════════════════════════════

PASO 2: DESCOMPRIMIR EL PAQUETE

1. Haz doble clic en el archivo adjunto: rhinometric-trial-v1.0.0.zip
2. macOS lo descomprimirá automáticamente
3. Verás una carpeta llamada "trial-package"

════════════════════════════════════════════════════════════════

PASO 3: EJECUTAR EL INSTALADOR

1. Abre Terminal (Aplicaciones → Utilidades → Terminal)
2. Escribe: cd ~/Downloads/trial-package
3. Presiona Enter
4. Escribe: ./start-trial.sh
5. Presiona Enter
6. Sigue las instrucciones en pantalla

El proceso tarda 5-10 minutos la primera vez.

════════════════════════════════════════════════════════════════

PASO 4: ACCEDER A RHINOMETRIC

Cuando termine, abre tu navegador y ve a:

🎨 Grafana (Dashboard principal): http://localhost:3000
   Usuario: admin
   Password: (se mostrará al finalizar la instalación)

📊 Dashboard de Licencias: http://localhost:8080

════════════════════════════════════════════════════════════════

SOLUCIÓN DE PROBLEMAS:

"Docker no está corriendo"
→ Abre Docker Desktop y espera a que inicie

"Permission denied al ejecutar start-trial.sh"
→ Ejecuta primero: chmod +x start-trial.sh

"Puerto ya en uso"
→ Algo está usando el puerto 3000. Cierra otras aplicaciones.

"No tengo Terminal"
→ Búscalo en Spotlight (Cmd+Space) escribiendo "Terminal"

════════════════════════════════════════════════════════════════

SOPORTE:

Si tienes problemas, contáctame:
📧 Email: soporte@rhinometric.com
📱 Teléfono: [Tu teléfono]

Toda la documentación está en el archivo README.md dentro del paquete.

¡Disfruta evaluando Rhinometric!

Saludos,
[Tu Nombre]
Rhinometric Team
```

---

## 📋 CHECKLIST ANTES DE ENVIAR

Verifica que:

- [x] El archivo `rhinometric-trial-v1.0.0.zip` existe
- [x] Tamaño es razonable (~40 KB)
- [x] Has probado el paquete en un Mac limpio (recomendado)
- [x] Email personalizado con nombre del cliente
- [x] Contacto de soporte incluido
- [x] Explicación clara de los 4 pasos

---

## 🧪 CÓMO PROBAR ANTES DE ENVIAR (Opcional pero Recomendado)

### Si tienes acceso a un Mac:

```bash
# 1. Copiar el ZIP a un Mac de prueba
scp rhinometric-trial-v1.0.0.zip usuario@mac:/Users/usuario/Downloads/

# 2. En el Mac, descomprimir
cd ~/Downloads
unzip rhinometric-trial-v1.0.0.zip

# 3. Entrar y probar
cd trial-package
./start-trial.sh

# 4. Verificar que funciona
# - Grafana en http://localhost:3000
# - Dashboard en http://localhost:8080
# - Todos los servicios corriendo: docker compose ps

# 5. Limpiar después de probar
docker compose down -v
cd ..
rm -rf trial-package
```

---

## 🚀 LO QUE SUCEDE CUANDO EL CLIENTE EJECUTA start-trial.sh

### Paso a Paso Automático:

1. **Verificación de Docker**
   - Comprueba que Docker está instalado
   - Comprueba que Docker está corriendo
   - Verifica que Docker Compose está disponible

2. **Verificación de Recursos**
   - Comprueba RAM disponible
   - Comprueba espacio en disco
   - Advierte si no hay suficiente

3. **Generación de Configuración**
   - Crea archivo `.env` con contraseñas aleatorias
   - Guarda credenciales en `credentials.txt`
   - Configura JWT secret único

4. **Creación de Directorios**
   - Crea carpetas para datos
   - Crea carpetas para licencias
   - Configura permisos

5. **Generación de Licencia**
   - Pregunta nombre del cliente
   - Calcula fecha de expiración (180 días)
   - Genera archivo de licencia

6. **Descarga e Inicio**
   - Descarga imágenes Docker (~2-5 GB)
   - Construye imágenes personalizadas
   - Inicia 11 contenedores
   - Espera a que estén listos

7. **Finalización**
   - Muestra credenciales de acceso
   - Muestra URLs de servicios
   - Muestra comandos útiles

---

## 📊 SERVICIOS QUE SE INSTALARÁN

Una vez completada la instalación, el cliente tendrá:

| Servicio | URL | Descripción |
|----------|-----|-------------|
| **Grafana** | http://localhost:3000 | Dashboard principal ⭐ |
| **Prometheus** | http://localhost:9090 | Métricas |
| **Loki** | http://localhost:3100 | Logs |
| **Tempo** | http://localhost:3200 | Trazas |
| **Alertmanager** | http://localhost:9093 | Alertas |
| **License Dashboard** | http://localhost:8080 | Monitor licencias ⭐ |
| **Nginx** | http://localhost | Proxy |

**Total**: 11 contenedores Docker

**Recursos consumidos**:
- RAM: ~6-8 GB
- CPU: ~4 vCPUs
- Disco: ~20 GB

---

## 📞 SOPORTE POST-INSTALACIÓN

### Problemas Más Comunes

#### 1. "Docker no está corriendo"

**Síntoma**: Error al ejecutar el script
```
❌ Docker no está corriendo
```

**Solución**:
1. Abrir Docker Desktop desde Aplicaciones
2. Esperar 30-60 segundos
3. Verificar que el ícono de Docker en la barra superior muestre "running"
4. Volver a ejecutar `./start-trial.sh`

---

#### 2. "Permission denied"

**Síntoma**: 
```
-bash: ./start-trial.sh: Permission denied
```

**Solución**:
```bash
chmod +x start-trial.sh
./start-trial.sh
```

---

#### 3. "Port 3000 already in use"

**Síntoma**: Grafana no inicia, error de puerto

**Solución Rápida**:
```bash
# Ver qué está usando el puerto
lsof -i :3000

# Matar el proceso (reemplaza PID)
kill -9 PID
```

**Solución Alternativa**: Cambiar puerto en `docker-compose.yml`:
```yaml
grafana:
  ports:
    - "3001:3000"  # Cambiar 3000 por 3001
```

---

#### 4. "Out of memory" o servicios muy lentos

**Síntoma**: Contenedores se reinician constantemente

**Solución**:
1. Abrir Docker Desktop
2. Ir a Settings (⚙️)
3. Resources
4. Aumentar Memory a 8 GB mínimo
5. Aumentar CPU a 4 cores mínimo
6. Apply & Restart
7. Volver a ejecutar `./start-trial.sh`

---

#### 5. "No space left on device"

**Síntoma**: Error al descargar imágenes

**Solución**:
```bash
# Limpiar imágenes viejas de Docker
docker system prune -a

# Liberar espacio en disco
# Eliminar archivos innecesarios de Downloads, etc.
```

---

#### 6. Cliente olvidó la contraseña de Grafana

**Solución**:
```bash
cd trial-package
cat credentials.txt
```

O:
```bash
cat .env | grep GRAFANA_PASSWORD
```

---

## 🔄 COMANDOS ÚTILES PARA EL CLIENTE

Una vez instalado, el cliente puede usar:

### Ver estado de servicios
```bash
cd trial-package
docker compose ps
```

### Ver logs en tiempo real
```bash
docker compose logs -f
```

### Reiniciar todo
```bash
docker compose restart
```

### Detener (sin borrar datos)
```bash
docker compose stop
```

### Iniciar (después de detener)
```bash
docker compose start
```

### Eliminar todo (incluye datos)
```bash
docker compose down -v
```

### Ver uso de recursos
```bash
docker stats
```

---

## 📈 SEGUIMIENTO Y CONVERSIÓN

### Indicadores de Uso Activo

Monitor si el cliente:
- ✅ Contacta con preguntas técnicas (está usando)
- ✅ Solicita integración con sus sistemas
- ✅ Pregunta por características enterprise
- ✅ Menciona "producción" o "escalamiento"
- ✅ Solicita extensión del trial

### Momentos Clave de Contacto

- **Día 1**: Email de bienvenida y verificación de instalación
- **Día 7**: Check-in: ¿cómo va? ¿necesitas ayuda?
- **Día 30**: Mitad del primer mes, ofrecer sesión de capacitación
- **Día 90**: Mitad del trial, mencionar versión comercial
- **Día 150**: Recordatorio de expiración próxima
- **Día 170**: Último aviso, oferta especial de conversión

---

## 💰 CONVERSIÓN A VERSIÓN COMERCIAL

Cuando el cliente quiera comprar:

### Beneficios de Upgrade:

| Característica | Trial | Comercial |
|----------------|-------|-----------|
| Duración | 180 días | Ilimitada ✅ |
| Retención | 7 días | 30/60/90 días ✅ |
| Usuarios | 5 máx | Ilimitados ✅ |
| HA | ❌ | ✅ |
| Backups | Manual | Automáticos ✅ |
| Soporte | Email | 24/7 ✅ |
| SLA | - | 99.9% ✅ |
| White Label | ❌ | ✅ |

### Proceso de Upgrade:

1. **No requiere reinstalación**
2. **Datos se preservan**
3. **Solo actualización de licencia**
4. **Migración guiada por soporte**

---

## ✅ RESUMEN FINAL

### Para Enviar al Cliente:

1. **Archivo**: `rhinometric-trial-v1.0.0.zip`
2. **Email**: Usar plantilla de arriba (personalizar)
3. **Requisitos**: Docker Desktop
4. **Tiempo**: 5-10 minutos instalación
5. **Soporte**: Incluir tu contacto

### El Cliente Recibirá:

- ✅ Paquete completo (40 KB)
- ✅ Instalador automático
- ✅ Documentación completa
- ✅ Licencia de 180 días
- ✅ 11 servicios de observabilidad
- ✅ Acceso inmediato a Grafana

### El Cliente Solo Necesita:

1. Descomprimir
2. Ejecutar script
3. Acceder a http://localhost:3000

**¡Eso es todo!**

---

**Fecha de Creación**: 17 de Octubre, 2025  
**Versión del Paquete**: 1.0.0  
**Validez Trial**: 180 días  
**Ubicación del ZIP**: `c:\Users\canel\mi-proyecto\infrastructure\mi-proyecto\rhinometric-trial-v1.0.0.zip`

---

## 📞 CONTACTO

**Soporte Técnico**: soporte@rhinometric.com  
**Comercial**: ventas@rhinometric.com  
**Web**: https://rhinometric.com
