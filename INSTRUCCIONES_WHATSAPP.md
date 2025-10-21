# 📱 INSTRUCCIONES PARA WHATSAPP - RHINOMETRIC MAC

## 🎯 COPIA ESTO Y ENVÍALO POR WHATSAPP:

---

**👋 Hola, te envío Rhinometric Trial para Mac**

**REQUISITO**: Docker Desktop instalado
Si no lo tienes: https://www.docker.com/products/docker-desktop

---

**INSTALACIÓN (3 pasos, 5 minutos):**

**1️⃣ Abre Terminal** (Cmd+Espacio → escribe "Terminal")

**2️⃣ Copia y pega este comando completo** (todo de una vez):

```bash
curl -sL https://raw.githubusercontent.com/tu-repo/install-mac-simple.sh | bash
```

**3️⃣ Espera 5 minutos** y abre: http://localhost:3000

**Credenciales:**
- Usuario: `admin`
- Password: `admin123`

---

**❓ Si te da error "curl: command not found":**

Usa este método alternativo:

**Copia TODO este script** (selecciona desde `#!/bin/bash` hasta el final) y pégalo en Terminal:

[AQUÍ PEGAS EL CONTENIDO COMPLETO DE install-mac-simple.sh]

---

**✅ Si funciona verás:**
```
✅ RHINOMETRIC INSTALADO CORRECTAMENTE
🎨 GRAFANA: http://localhost:3000
```

**❌ Si no funciona**, envíame captura de pantalla del error.

---

**Trial**: 180 días  
**Soporte**: soporte@rhinometric.com

---

## 📋 MÉTODO ALTERNATIVO (SIN CURL)

Si el usuario no puede usar curl, envíale esto por WhatsApp:

---

**MÉTODO SIMPLE SIN CURL:**

**1️⃣ Crea el archivo:**
```bash
cd ~/Downloads
nano install-rhino.sh
```

**2️⃣ Pega el script completo** (te lo envío en el siguiente mensaje)

**3️⃣ Guarda:**
- Presiona: `Ctrl+O` (guardar)
- Presiona: `Enter` (confirmar)
- Presiona: `Ctrl+X` (salir)

**4️⃣ Ejecuta:**
```bash
chmod +x install-rhino.sh
./install-rhino.sh
```

**5️⃣ Abre:** http://localhost:3000

---

## 🚀 MÉTODO MÁS SIMPLE DE TODOS

**Envía el script completo como archivo de texto:**

1. Adjunta `install-mac-simple.sh` como archivo en WhatsApp
2. Dile al usuario:

---

**Descarga el archivo "install-mac-simple.sh" que te envié**

**Luego en Terminal:**
```bash
cd ~/Downloads
chmod +x install-mac-simple.sh
./install-mac-simple.sh
```

**Espera 5 minutos y abre:** http://localhost:3000

**Usuario: admin**
**Password: admin123**

---

## 📞 TROUBLESHOOTING RÁPIDO

**Error: "Docker no está instalado"**
→ Instala Docker Desktop: https://docker.com/products/docker-desktop

**Error: "Puerto 3000 ocupado"**
→ Ejecuta: `lsof -i :3000` y mata el proceso

**No arranca**
→ Ejecuta: `docker compose logs` y envíame captura

---

## ✅ VERIFICACIÓN

**Después de instalar, pide al usuario que ejecute:**

```bash
cd ~/rhinometric-trial
docker compose ps
```

**Debe ver 4 servicios "Up":**
- rhino-grafana
- rhino-prometheus
- rhino-loki
- rhino-postgres

---

## 📦 CONTENIDO DEL SCRIPT

El script `install-mac-simple.sh` hace TODO automáticamente:

1. ✅ Verifica Docker
2. ✅ Crea directorio `~/rhinometric-trial`
3. ✅ Genera `docker-compose.yml` (4 servicios básicos)
4. ✅ Crea configuraciones de Prometheus y Loki
5. ✅ Descarga imágenes Docker
6. ✅ Inicia servicios
7. ✅ Muestra credenciales

**Total: 4 servicios** (Grafana, Prometheus, Loki, PostgreSQL)

Mucho más simple que los 11 servicios anteriores.

---

## 🎯 RESUMEN PARA TI

**LO QUE DEBES ENVIAR POR WHATSAPP:**

**Opción A (recomendada):**
- Adjunta el archivo `install-mac-simple.sh`
- Copia las instrucciones de arriba

**Opción B:**
- Copia TODO el contenido del script `install-mac-simple.sh`
- Pégalo en WhatsApp como texto (mensaje largo)
- Instrucciones: "Pega esto en Terminal y presiona Enter"

**Opción C:**
- Sube el script a GitHub/Gist
- Envía el comando: `curl -sL [URL] | bash`

---

**Tiempo total**: 5 minutos
**Complejidad**: MÍNIMA
**Servicios**: 4 (lo esencial)
**Credenciales**: admin/admin123 (fijas, sin generación)
