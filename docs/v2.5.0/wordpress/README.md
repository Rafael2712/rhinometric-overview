# WordPress Pages - Rhinometric v2.5.0

## 📦 Contenido

Este directorio contiene **3 páginas HTML listas para pegar** en WordPress sin necesidad de usar la API bloqueada.

### Archivos Incluidos

1. **01-demo-ova-page.html** - Página de descarga de la OVA demo (4 horas)
2. **02-trial-linux-page.html** - Página de descarga del instalador trial Linux (14 días)
3. **03-documentation-page.html** - Página central de documentación con enlaces a PDFs

---

## 🚀 Instrucciones de Uso

### Paso 1: Acceder a WordPress Admin

```
https://rhinometric.com/wp-admin
```

Login con tus credenciales de administrador.

### Paso 2: Crear Nueva Página

Para **cada archivo HTML**:

1. **Páginas** → **Añadir nueva**
2. **Título de la página:**
   - Para `01-demo-ova-page.html`: "Demo Rhinometric - Descarga OVA"
   - Para `02-trial-linux-page.html`: "Trial Rhinometric 14 días"
   - Para `03-documentation-page.html`: "Documentación Rhinometric"

3. **Cambiar a editor HTML:**
   - Click en **tres puntos verticales** (arriba derecha)
   - Seleccionar **"Editar como HTML"**

4. **Pegar el código:**
   - Abre el archivo HTML correspondiente en un editor de texto
   - Selecciona **todo el contenido** (Ctrl+A)
   - Copia (Ctrl+C)
   - Pega en el editor HTML de WordPress (Ctrl+V)

5. **Ajustar URL del License Server (si es necesario):**
   - Por defecto, los enlaces apuntan a: `https://licensing.rhinometric.com:5000`
   - Si tu servidor tiene otra URL, usa **Buscar y Reemplazar** (Ctrl+H):
     ```
     Buscar:    https://licensing.rhinometric.com:5000
     Reemplazar: https://TU-SERVIDOR:5000
     ```

6. **Vista previa:**
   - Click en **"Vista previa"** para ver cómo se ve la página

7. **Publicar:**
   - Si todo está correcto, click en **"Publicar"**

### Paso 3: Configurar URLs Amigables (Permalinks)

Después de publicar, configura URLs limpias:

1. **Páginas** → Busca la página recién creada
2. En **Ajustes de página** → **Permalink** → Editar:
   - Demo OVA: `/demo`
   - Trial Linux: `/trial`
   - Documentación: `/documentation` o `/docs`

3. **Guardar cambios**

### Paso 4: Actualizar Menú Principal

1. **Apariencia** → **Menús**
2. Selecciona tu menú principal (ej: "Main Menu")
3. **Añadir elementos:**
   - **Páginas** → Selecciona las 3 páginas recién creadas
   - **Añadir al menú**
4. Organizar en el menú:
   ```
   🏠 Inicio
   📦 Productos
       ├── Demo OVA (4h)
       └── Trial Linux (14 días)
   📚 Recursos
       ├── Documentación
       └── Soporte
   💰 Precios
   📧 Contacto
   ```
5. **Guardar menú**

---

## 🔗 URLs de Descarga Usadas

Todas las páginas HTML usan estos endpoints del **License Server v2**:

### Descargas

- **Demo OVA:** `https://licensing.rhinometric.com:5000/downloads/demo-ova`
- **Trial Installer:** `https://licensing.rhinometric.com:5000/downloads/trial-installer`

### Documentación

- **Guía Instalación (ES):** `https://licensing.rhinometric.com:5000/docs/installation-guide?lang=es`
- **Installation Guide (EN):** `https://licensing.rhinometric.com:5000/docs/installation-guide?lang=en`
- **Manual Usuario (ES):** `https://licensing.rhinometric.com:5000/docs/user-manual?lang=es`
- **User Manual (EN):** `https://licensing.rhinometric.com:5000/docs/user-manual?lang=en`

---

## 🎨 Características de las Páginas

### 01-demo-ova-page.html

✅ **Hero section** con badges (4 horas, todo incluido, VirtualBox/VMware)  
✅ **Botón de descarga prominente** para la OVA  
✅ **Grid de features** (Stack completo, Dashboards, API Connector, etc.)  
✅ **Pasos de instalación** visuales (1-2-3)  
✅ **Requisitos del sistema** detallados  
✅ **CTA de soporte** con enlaces a email y docs  

**Ideal para:** Usuarios que quieren probar Rhinometric en 5 minutos sin instalación compleja.

### 02-trial-linux-page.html

✅ **Hero section verde** (color trial)  
✅ **Plataformas soportadas** (Ubuntu, Debian, CentOS, RHEL)  
✅ **Guía de instalación rápida** con comandos copy-paste  
✅ **Checklist de requisitos** (hardware y software)  
✅ **Qué incluye el trial** con iconos visuales  
✅ **Warning box** con límites del trial (14 días, 5 hosts)  
✅ **CTA de upgrade** a licencia anual  

**Ideal para:** Usuarios técnicos que quieren evaluar en su infraestructura real.

### 03-documentation-page.html

✅ **Grid de documentación** con cards para cada tipo de doc  
✅ **Botones de descarga** para ES y EN en cada PDF  
✅ **Sección de recursos adicionales** (API Reference, Architecture)  
✅ **Quick links** a demo, trial, GitHub, soporte  
✅ **Sección de video tutoriales** (próximamente)  
✅ **GDPR notice** destacando que todo es on-premise  
✅ **Footer stats** (versión 2.5.0, 24+ componentes, etc.)  

**Ideal para:** Hub central de documentación con acceso a todos los manuales.

---

## 📱 Responsive Design

Todas las páginas incluyen **CSS responsive** que se adapta a:

- 💻 **Desktop** (1200px+)
- 📱 **Tablet** (768px - 1199px)
- 🤳 **Mobile** (< 768px)

Los estilos están **inline** (dentro de cada HTML) para evitar conflictos con el tema de WordPress.

---

## 🛠️ Personalización

### Cambiar Colores

Busca en el HTML las variables de gradientes:

```css
/* Demo OVA - Morado */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* Trial Linux - Verde */
background: linear-gradient(135deg, #2ecc71 0%, #27ae60 100%);

/* Documentación - Azul */
background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
```

Cambia los colores hexadecimales según tu brand guide.

### Cambiar Textos

Todos los textos están en español por defecto. Para traducir o modificar:

1. Abre el HTML en un editor de texto
2. Busca el texto que quieres cambiar
3. Reemplaza
4. Guarda
5. Pega de nuevo en WordPress (o edita directamente en WordPress)

### Añadir Imágenes

Para incluir imágenes (logos, screenshots):

1. Sube la imagen a **Medios** en WordPress
2. Copia la URL de la imagen
3. En el HTML, añade:
   ```html
   <img src="https://rhinometric.com/wp-content/uploads/2025/12/screenshot.png" 
        alt="Rhinometric Dashboard" 
        style="width: 100%; border-radius: 12px; margin: 20px 0;">
   ```

---

## ✅ Checklist de Publicación

Antes de dar por finalizado:

- [ ] Las 3 páginas creadas en WordPress
- [ ] URLs amigables configuradas (`/demo`, `/trial`, `/docs`)
- [ ] Páginas añadidas al menú principal
- [ ] Enlaces de descarga verificados (click en botones)
- [ ] Vista previa en mobile (responsive)
- [ ] Verificar que PDFs se descargan correctamente
- [ ] Probar desde navegador incógnito
- [ ] Compartir enlaces con el equipo para feedback
- [ ] Analytics configurado (Google Analytics / Matomo)

---

## 📊 SEO Recommendations

### Meta Tags Sugeridos

Para cada página, en **Yoast SEO** o similar:

**Demo OVA:**
```
Title: Demo Rhinometric - Prueba 4 Horas Gratis | Observability Platform
Description: Descarga la OVA de Rhinometric y prueba nuestra plataforma de observability en solo 5 minutos. VirtualBox/VMware compatible. Sin instalación compleja.
Keywords: rhinometric demo, observability demo, grafana ova, prometheus demo
```

**Trial Linux:**
```
Title: Trial Rhinometric 14 Días - Instalación Linux | Ubuntu, Debian, CentOS
Description: Evalúa Rhinometric en tu infraestructura durante 14 días. Instalador automático para Linux. Hasta 5 hosts. Stack completo de observabilidad.
Keywords: rhinometric trial, observability trial, grafana prometheus loki, monitoring trial
```

**Documentación:**
```
Title: Documentación Rhinometric v2.5.0 - Manuales y Guías | ES/EN
Description: Documentación completa de Rhinometric: guías de instalación, manuales de usuario, API reference. Disponible en español e inglés (PDF).
Keywords: rhinometric docs, rhinometric manual, grafana guide, observability documentation
```

### Open Graph (Redes Sociales)

Configura imágenes de preview para compartir en redes:

```html
<meta property="og:title" content="Demo Rhinometric - Prueba 4 Horas Gratis">
<meta property="og:description" content="Plataforma completa de observabilidad on-premise">
<meta property="og:image" content="https://rhinometric.com/images/og-demo.png">
<meta property="og:url" content="https://rhinometric.com/demo">
```

---

## 🔒 Seguridad

### HTTPS

Asegúrate de que todo el sitio usa HTTPS:

```
https://rhinometric.com/demo
https://rhinometric.com/trial
https://rhinometric.com/documentation
```

Si hay warnings de "contenido mixto" (HTTP + HTTPS):
- Busca enlaces `http://` en el HTML
- Cámbialo a `https://`

### Rate Limiting

Para evitar abusos de descarga, el License Server debería tener rate limiting:

```python
# En main.py del License Server (futuro)
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@app.get("/downloads/demo-ova")
@limiter.limit("3/hour")  # Máximo 3 descargas por hora por IP
async def download_demo_ova():
    ...
```

---

## 📞 Soporte

Si tienes problemas con las páginas de WordPress:

- **Email:** rafael.canelon@rhinometric.com
- **Documentación técnica:** `../DOWNLOAD_ENDPOINTS.md`
- **License Server:** `../../license-server-v2/main.py`

---

## 🎯 Próximas Mejoras

- [ ] Landing page principal con animaciones (hero animado)
- [ ] Formulario de contacto integrado en cada página
- [ ] Sistema de comentarios/reviews de usuarios
- [ ] Galería de screenshots/videos de la plataforma
- [ ] Comparativa de tiers (demo vs trial vs annual)
- [ ] Testimonios de clientes
- [ ] Blog con artículos técnicos (observability, DevOps)
- [ ] Versiones en inglés de las 3 páginas

---

**Última actualización:** 16 de Diciembre de 2025  
**Versión:** Rhinometric v2.5.0  
**Autor:** Rhinometric Development Team
