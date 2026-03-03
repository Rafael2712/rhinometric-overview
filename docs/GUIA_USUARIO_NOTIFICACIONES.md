# Guía de Usuario — Configuración de Notificaciones

> **Rhinometric Console v2.5.1**  
> Última actualización: 2026-03-03

---

## Índice

1. [Introducción](#introducción)
2. [Acceder a Configuración](#acceder-a-configuración)
3. [Paso 1: Activar Alertas de IA](#paso-1-activar-alertas-de-ia)
4. [Paso 2: Configurar Slack](#paso-2-configurar-slack)
5. [Paso 3: Configurar Email](#paso-3-configurar-email)
6. [Paso 4: Probar las Notificaciones](#paso-4-probar-las-notificaciones)
7. [Cómo Funcionan las Alertas](#cómo-funcionan-las-alertas)
8. [Preguntas Frecuentes](#preguntas-frecuentes)

---

## Introducción

Rhinometric Console puede enviar **alertas automáticas** cuando su sistema de IA detecta anomalías en la infraestructura. Las alertas se pueden configurar para llegar por dos canales:

- **Slack** — mensajes instantáneos en un canal de su workspace
- **Email** — correos electrónicos con detalle completo de la anomalía

Cada alerta incluye botones que lo llevan directamente al **dashboard relevante** dentro de la Console o en Grafana.

---

## Acceder a Configuración

1. Inicie sesión en **Rhinometric Console** con una cuenta de **Administrador**
2. En el menú lateral izquierdo, haga clic en **⚙️ Settings**
3. Verá dos secciones principales:
   - **AI Anomaly Alerting** — activa/desactiva las alertas
   - **Notification Channels** — configura Slack y Email

> ⚠️ Solo los usuarios con rol **Admin** o **Owner** pueden acceder a Settings.

---

## Paso 1: Activar Alertas de IA

En la sección **AI Anomaly Alerting**:

1. Asegúrese de que el toggle esté en **ON** (verde)
2. Haga clic en **Save** si realizó cambios

Cuando está activado:
- ✅ Las anomalías críticas detectadas por IA generarán alertas
- ✅ Las alertas se enviarán por los canales que configure abajo

Cuando está desactivado:
- ❌ No se envían alertas de anomalías de IA
- ✅ Las alertas estándar de Prometheus siguen funcionando normalmente

---

## Paso 2: Configurar Slack

### 2.1 Crear un Webhook en Slack

Antes de configurar en la Console, necesita crear un **Incoming Webhook** en Slack:

1. Vaya a https://api.slack.com/apps
2. Clic en **"Create New App"** → **"From scratch"**
3. Nombre: `Rhinometric Alerts`, Workspace: seleccione el suyo
4. En el menú izquierdo, vaya a **"Incoming Webhooks"**
5. Active el toggle **"Activate Incoming Webhooks"**
6. Clic en **"Add New Webhook to Workspace"**
7. Seleccione el **canal** donde quiere recibir alertas (ej: `#alerts`)
8. Clic en **"Allow"**
9. **Copie la URL del webhook** — la necesitará en el siguiente paso

> La URL tiene este formato: `https://hooks.slack.com/services/T.../B.../xxxxx`

### 2.2 Configurar en Rhinometric Console

En la sección **Notification Channels → Slack**:

| Campo | Qué poner | Ejemplo |
|-------|-----------|---------|
| **Enabled** | Activar el toggle | ✅ ON |
| **Webhook URL** | Pegar la URL copiada de Slack | `https://hooks.slack.com/services/T09T.../B0AJ.../gE4n...` |
| **Channel** | El canal donde recibirá alertas (con #) | `#nuevo-canal` |

3. Haga clic en **💾 Save Channels**
4. Debería ver un mensaje verde: **"Notification channels saved and Alertmanager reloaded"**

### 2.3 Resultado en Slack

Cuando se detecte una anomalía, recibirá un mensaje en Slack como este:

```
🔴 [CRITICAL] AI Anomaly: node_cpu_usage (unknown)

Certificado SSL con vencimiento anomalo detectado.

Desviacion: 104.6% respecto al baseline

Valor actual: 92.5 | Baseline esperado: 45.2

Contexto:
• Componente: node-exporter
• Metrica: node_cpu_usage
• Severidad: CRITICAL
• Estado: firing

🖥️ Ver Dashboard en Consola
📈 Ver CPU en Grafana

[Ver Dashboard en Consola]  [Ver en Grafana]
```

Los **botones** lo llevan directamente al dashboard correcto según la métrica de la anomalía.

---

## Paso 3: Configurar Email

### 3.1 Requisitos Previos

El sistema usa **Zoho Mail API** para enviar correos. Necesita:

- Una cuenta de Zoho Mail con un dominio verificado
- Credenciales de API de Zoho (las configura su administrador de sistemas)

> 📝 Si usa hosting en Hetzner, los puertos SMTP (587/465) están bloqueados. Por eso usamos la API de Zoho que funciona por HTTPS (puerto 443).

### 3.2 Configurar en Rhinometric Console

En la sección **Notification Channels → Email**:

| Campo | Qué poner | Ejemplo |
|-------|-----------|---------|
| **Enabled** | Activar el toggle | ✅ ON |
| **SMTP Host** | Servidor SMTP (usado como referencia) | `smtp.zoho.eu` |
| **SMTP Port** | Puerto SMTP | `587` |
| **SMTP Username** | Su usuario de Zoho | `user@sudominio.com` |
| **SMTP Password** | Contraseña (opcional si usa API) | `••••••••` |
| **Use TLS** | Mantener activado | ✅ ON |
| **From Email** | Dirección del remitente | `user@sudominio.com` |
| **To Emails** | Destinatarios (separados por coma) | `admin@sudominio.com` |

3. Haga clic en **💾 Save Channels**

### 3.3 Configuración de Zoho API (Administrador de Sistemas)

La configuración de Zoho API se almacena en el archivo de canales del servidor. Su administrador de sistemas debe configurar:

```json
{
  "zoho_api": {
    "client_id": "1000.XXXXXXXXXXXXX",
    "client_secret": "xxxxxxxxxxxxxxxxxxxxxxx",
    "refresh_token": "1000.xxxxxxxxxxxxxxxxxxxxxxx",
    "account_id": "74279XXXXXXXXX",
    "from_address": "user@sudominio.com"
  }
}
```

> Consulte la **Guía Técnica** (`NOTIFICATION_CHANNELS_TECHNICAL.md`) para instrucciones detalladas sobre cómo obtener estas credenciales de Zoho.

### 3.4 Resultado por Email

Recibirá un correo HTML con:

- **Encabezado rojo** (crítico) o **naranja** (warning) con el nombre de la anomalía
- **Detalles:** métrica, severidad, componente, servicio, valores
- **Dos botones:**
  - 🔵 **"Ver Dashboard en Consola"** — abre el dashboard relevante dentro de la Console
  - 🟡 **"Ver en Grafana"** — abre el panel específico de Grafana para esa métrica

---

## Paso 4: Probar las Notificaciones

### Probar Slack

1. En Settings → Notification Channels → Slack
2. Haga clic en el botón **"🚀 Test Slack"**
3. Debería recibir un mensaje de prueba en su canal de Slack
4. Si funciona, verá: ✅ **"Slack test message sent successfully"**
5. Si falla, verá un mensaje de error con detalles

### Probar Email

1. En Settings → Notification Channels → Email
2. Haga clic en el botón **"🚀 Test Email"**
3. Debería recibir un correo de prueba en los destinatarios configurados
4. Si funciona, verá: ✅ **"Test email sent successfully"**
5. Si falla, revise los detalles del error

---

## Cómo Funcionan las Alertas

### Flujo Completo

```
1. El servicio de IA detecta una anomalía
           ↓
2. Se crea una alerta en Prometheus
           ↓
3. Alertmanager recibe la alerta
           ↓
4. Si la severidad es CRITICAL:
     ├──→ Envía mensaje a Slack (canal configurado)
     └──→ Envía email vía Zoho API (destinatarios configurados)
           ↓
5. Ambos incluyen botones con enlaces directos:
     ├──→ "Ver Dashboard en Consola" → Dashboard embebido en la Console
     └──→ "Ver en Grafana" → Panel específico en Grafana
```

### ¿A Qué Dashboard Llegan los Enlaces?

| Tipo de Anomalía | Dashboard en Console | Dashboard en Grafana |
|-------------------|---------------------|---------------------|
| CPU (`node_cpu_usage`) | System Overview | Panel CPU (gauge) |
| Memoria (`node_memory_usage`) | System Overview | Panel Memory (gauge) |
| Disco (`node_disk_usage`, `node_disk_io`) | System Overview | Panel Disk (gauge) |
| Red (`node_network_*`) | System Overview | Panel Network Traffic |
| Website/SSL/Otros | AI Anomaly Service | Dashboard de Anomalías |

### ¿Quién Recibe las Alertas?

- **Slack:** Todos los miembros del canal configurado
- **Email:** Solo los destinatarios configurados en `To Emails`
- **Botón "Ver en Grafana":** Solo visible para usuarios Admin/Owner en la Console

---

## Preguntas Frecuentes

### ¿Por qué no recibo alertas?

1. Verifique que **AI Anomaly Alerting** esté **ON** en Settings
2. Verifique que el canal (Slack/Email) esté **Enabled**
3. Use los botones de **Test** para verificar la conexión
4. Solo las anomalías con severidad **CRITICAL** generan alertas

### ¿Puedo recibir alertas en múltiples canales de Slack?

Actualmente, las alertas se envían a **un solo canal** de Slack. Para enviar a múltiples canales, puede crear workflows en Slack que reenvíen mensajes.

### ¿Puedo agregar más destinatarios de email?

Sí. En el campo **To Emails**, separe las direcciones con coma:
```
admin@empresa.com, devops@empresa.com, cto@empresa.com
```

### ¿Qué pasa si Slack o el email fallan?

- Si Slack falla, el email sigue enviándose (y viceversa)
- Los errores se registran en los logs del backend
- La detección de anomalías **nunca se detiene** por fallos en las notificaciones

### ¿Cómo cambio el canal de Slack?

1. Cree un nuevo Incoming Webhook apuntando al nuevo canal en Slack
2. En Settings → Notification Channels → Slack:
   - Actualice el **Webhook URL** con la nueva URL
   - Actualice el **Channel** con el nuevo nombre
3. Haga clic en **Save Channels**
4. Pruebe con **Test Slack**

### ¿Los datos de configuración son seguros?

- Las credenciales se almacenan en un archivo con permisos `chmod 600` (solo lectura para el proceso)
- La API nunca devuelve la URL completa del webhook ni contraseñas SMTP
- Los tokens de Zoho API se refrescan automáticamente cada hora

### ¿Puedo recibir alertas de severidad WARNING o INFO?

Actualmente, solo las anomalías **CRITICAL** disparan alertas de IA. Las alertas WARNING e INFO de Prometheus estándar sí se envían por sus propios canales. Si necesita recibir alertas de IA de menor severidad, contacte a su administrador de sistemas para ajustar las reglas de enrutamiento en Alertmanager.
