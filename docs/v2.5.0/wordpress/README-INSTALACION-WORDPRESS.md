# 🌐 Páginas WordPress para Rhinometric v2.5.0

## 📦 Contenido

Este directorio contiene 5 páginas HTML listas para publicar en WordPress:

1. **00-home-page.html** - Página principal con hero, beneficios, planes
2. **01-demo-ova-page.html** - Descarga Demo OVA (4 horas)
3. **02-trial-linux-page.html** - Solicitud Trial 14 días (con formulario funcional)
4. **03-documentation-page.html** - Hub de documentación
5. **04-contact-page.html** - Formulario de contacto y soporte

---

## ✅ Instrucciones de Instalación en WordPress

### Paso 1: Acceder a WordPress Admin

```
https://rhinometric.com/wp-admin
```

### Paso 2: Crear Nueva Página

1. **Páginas** → **Añadir nueva**
2. Título de la página (ej: "Inicio", "Demo", "Trial", etc.)
3. Click en los **tres puntos** (⋮) arriba a la derecha
4. Seleccionar **"Editar como HTML"** o **"Editor de código"**

### Paso 3: Pegar el Código

1. Abrir el archivo HTML correspondiente
2. **Copiar TODO el contenido**
3. **Pegar** en el editor de WordPress
4. **No** añadir etiquetas `<html>`, `<head>` o `<body>` adicionales

### Paso 4: Configurar Permalinks

- **Home**: `/` (página principal) o `/inicio`
- **Demo**: `/demo`
- **Trial**: `/trial`
- **Docs**: `/documentation`
- **Contact**: `/contact` o `/contacto`

### Paso 5: Publicar

Click en **"Publicar"** arriba a la derecha

---

## 🔧 Configuración Necesaria

### URLs a Actualizar

Si tu servidor de licencias NO está en `http://54.197.192.198:8090`, actualiza las URLs en:

**Archivo: 02-trial-linux-page.html**
```javascript
// Línea ~480
fetch('http://54.197.192.198:8090/api/v1/trial/generate', {
```

**Reemplazar con tu URL:**
```javascript
fetch('https://licensing.rhinometric.com:5000/api/v1/trial/generate', {
```

### Formulario de Contacto (Recomendado)

En **04-contact-page.html**, el formulario actual usa `mailto:`. Para una mejor experiencia:

1. Instalar plugin **Contact Form 7** o **WPForms**
2. Crear formulario personalizado
3. Reemplazar el `<form>` HTML con el shortcode:
   ```
   [contact-form-7 id="123" title="Rhinometric Contact"]
   ```

---

## 🎨 Personalización

### Colores del Brand

Actualiza estos colores si quieres cambiar la paleta:

- **Púrpura primario**: `#667eea` y `#764ba2`
- **Verde (success)**: `#10b981`
- **Azul (links)**: `#1e3a8a`

Buscar y reemplazar en todos los archivos.

### Logos e Imágenes

Los archivos actuales **NO incluyen imágenes externas** (todo es inline).

Si quieres añadir:
- Logo de Rhinometric
- Screenshots del producto
- Iconos personalizados

Súbelos a WordPress Media Library y reemplaza los emojis con `<img>` tags.

---

## ✅ Checklist Post-Instalación

### Página Home (00)
- [ ] Publicada como página principal
- [ ] Links a /demo y /trial funcionan
- [ ] Botón "Contactar Ventas" apunta a /contact

### Página Demo (01)
- [ ] Botón descarga OVA apunta a URL correcta
- [ ] Requisitos de sistema claramente visibles
- [ ] Links a documentación funcionan

### Página Trial (02) **CRÍTICO**
- [ ] Formulario envía POST a License Server
- [ ] Email de confirmación llega (probar con email real)
- [ ] Mensaje de éxito se muestra correctamente
- [ ] Botón de descarga instalador funciona

### Página Docs (03)
- [ ] Links a PDFs funcionan (cuando estén creados)
- [ ] Link a `/docs/installation-guide?lang=es` correcto
- [ ] Link a `/docs/user-manual?lang=en` correcto

### Página Contact (04)
- [ ] Formulario de contacto funciona
- [ ] Email llega a rafael.canelon@rhinometric.com
- [ ] Información de soporte visible

---

## 🧪 Testing

### Test Manual Completo

1. **Navegar a `/trial`**
2. **Completar formulario** con email real
3. **Click "Generar Licencia"**
4. **Verificar**:
   - Mensaje de éxito aparece
   - Email llega en < 2 minutos
   - Email contiene:
     - License key `RHINO-TRIAL-XXXXX`
     - Link de descarga funciona
     - Fecha de expiración correcta (14 días)

### Test Técnico (API)

```bash
# Probar endpoint desde terminal
curl -X POST http://54.197.192.198:8090/api/v1/trial/generate \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "company_name": "Test Company"
  }'

# Debe devolver:
# {"license_key":"RHINO-TRIAL-XXXXX","expires_at":"2026-XX-XX..."}
```

---

## 🐛 Troubleshooting

### Problema: Formulario no envía

**Causa**: CORS bloqueado por navegador

**Solución**: Añadir header CORS en License Server:
```python
# main.py
origins = ["https://rhinometric.com", "http://rhinometric.com"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Problema: Email no llega

**Causa**: SMTP no configurado o en spam

**Solución 1**: Verificar SMTP en servidor
```bash
docker logs license-server-license-api-1 --tail 50 | grep -i email
```

**Solución 2**: Configurar SPF/DKIM en DNS

### Problema: Estilos rotos en WordPress

**Causa**: Tema sobrescribe inline styles

**Solución**: Añadir `!important` a estilos críticos:
```css
background: #667eea !important;
color: white !important;
```

---

## 📊 Analytics (Recomendado)

Añadir Google Analytics o similar para trackear:

- Visitas a `/trial`
- Tasa de conversión formulario trial
- Descargas de demo OVA
- Solicitudes de contacto annual

---

## 🔒 Seguridad

### HTTPS (OBLIGATORIO)

Asegúrate de que:
- WordPress corre en HTTPS
- License Server tiene SSL/TLS
- Formularios solo en HTTPS

### Rate Limiting

Protege el endpoint `/api/v1/trial/generate` contra abuse:

```python
# Limitar a 5 trials por IP por hora
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/trial/generate")
@limiter.limit("5/hour")
def generate_trial(...):
```

---

## 📞 Soporte

**Problemas con instalación WordPress:**
rafael.canelon@rhinometric.com

**Modificaciones al diseño:**
Archivos HTML son editables directamente, no requieren build process.

---

**Última actualización:** 16 Diciembre 2025  
**Versión:** 2.5.0  
**Autor:** Rafael Canelón
