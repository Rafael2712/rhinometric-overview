# 🌐 WORDPRESS PUBLISHING GUIDE - Rhinometric v2.5.0

## Guía Completa para Publicar las Páginas Web de Rhinometric

---

## Tabla de Contenidos

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Pre-requisitos](#pre-requisitos)
3. [Archivos HTML Disponibles](#archivos-html-disponibles)
4. [Publicación Paso a Paso](#publicación-paso-a-paso)
   - [Página 1: Demo OVA](#página-1-demo-ova)
   - [Página 2: Trial Linux](#página-2-trial-linux)
   - [Página 3: Documentación](#página-3-documentación)
5. [Configuración de Menús](#configuración-de-menús)
6. [Personalización](#personalización)
7. [Verificación Final](#verificación-final)
8. [URLs Finales](#urls-finales)

---

## Resumen Ejecutivo

Este documento te guiará paso a paso para publicar **3 páginas web profesionales** en tu sitio WordPress de Rhinometric.

**¿Qué vamos a publicar?**

1. **Página de Demo OVA** → Landing page para descarga de evaluación 4 horas
2. **Página de Trial Linux** → Landing page para descarga instalador 14 días
3. **Página de Documentación** → Hub central de manuales y guías (ES/EN)

**Tiempo estimado:** 15-20 minutos

**Nivel de dificultad:** ⭐⭐ (Intermedio - requiere acceso a wp-admin)

---

## Pre-requisitos

### Acceso Requerido

- ✅ Acceso a WordPress Admin Panel (`https://rhinometric.com/wp-admin`)
- ✅ Permisos para crear/editar páginas
- ✅ Capacidad de cambiar a editor HTML (Classic Editor o Gutenberg con HTML personalizado)

### Archivos Necesarios

Los 3 archivos HTML están en:
```
docs/v2.5.0/wordpress/
├── 01-demo-ova-page.html         (371 líneas)
├── 02-trial-linux-page.html      (451 líneas)
└── 03-documentation-page.html    (376 líneas)
```

### URLs del License Server

Todas las páginas apuntan a:
```
https://licensing.rhinometric.com:5000
```

**Si usas un servidor diferente**, deberás hacer búsqueda/reemplazo antes de pegar el HTML.

---

## Archivos HTML Disponibles

### 01-demo-ova-page.html

**Propósito:** Landing page para Demo OVA (4 horas de evaluación)

**Contenido:**
- Hero section con gradiente púrpura
- Badges: 4h, VirtualBox/VMware, All Included
- Botón de descarga → `/downloads/demo-ova`
- Grid de features (6 tarjetas)
- Pasos de instalación (3 pasos visuales)
- Requisitos del sistema
- CTA de soporte

**URL sugerida:** `/demo` o `/demo-ova`

**Diseño:** Gradientes púrpura/violeta, tema "premium"

---

### 02-trial-linux-page.html

**Propósito:** Landing page para Trial Linux (14 días de evaluación)

**Contenido:**
- Hero section con gradiente verde
- Badges: 14 días, 5 hosts, Auto-installation
- Botón de descarga → `/downloads/trial-installer`
- Compatibilidad de plataformas (Ubuntu, Debian, CentOS, RHEL)
- Comandos de instalación (copy-paste ready)
- Requisitos (hardware + software)
- Warning box con limitaciones trial
- CTA de upgrade a Annual

**URL sugerida:** `/trial` o `/trial-linux`

**Diseño:** Gradientes verde/esmeralda, tema "developer-friendly"

---

### 03-documentation-page.html

**Propósito:** Hub central de documentación

**Contenido:**
- Hero section con gradiente azul
- Grid de 4 tipos de documentación:
  1. **Guía de Instalación** (ES/EN) → botones descarga PDF
  2. **Manual de Usuario** (ES/EN) → botones descarga PDF
  3. **Referencia API** → link a `/api/docs`
  4. **Guía de Arquitectura** → link a docs
- Quick links (Demo, Trial, GitHub, Support, etc.)
- Sección "Próximamente: Video Tutorials"
- GDPR notice
- Footer con stats (versión, componentes, dashboards)

**URL sugerida:** `/documentation` o `/docs`

**Diseño:** Gradientes azul/cyan, tema "profesional/corporativo"

---

## Publicación Paso a Paso

### Página 1: Demo OVA

#### 1. Abrir archivo HTML

Abre `docs/v2.5.0/wordpress/01-demo-ova-page.html` en tu editor de texto.

#### 2. (Opcional) Verificar/Cambiar URL del servidor

**Buscar:**
```html
https://licensing.rhinometric.com:5000
```

**Si necesitas cambiar a otra URL:**
```html
# Por ejemplo, cambiar a dominio personalizado:
https://downloads.rhinometric.io
```

**Cómo hacer el reemplazo:**
- VS Code: `Ctrl+H` → Find/Replace
- Sublime: `Ctrl+H`
- Notepad++: `Ctrl+H`

**Cuántas instancias hay:**
- **01-demo-ova-page.html:** 2 menciones (comentario línea 13 + botón línea 235)
- **02-trial-linux-page.html:** 3 menciones (comentario + botón + comando wget)
- **03-documentation-page.html:** 6 menciones (comentario + 4 botones de PDFs + API link)

#### 3. Copiar todo el HTML

- Selecciona todo el contenido del archivo (`Ctrl+A`)
- Copia (`Ctrl+C`)

#### 4. Login en WordPress

```
https://rhinometric.com/wp-admin
```

#### 5. Crear nueva página

1. En el panel izquierdo: **Páginas** → **Añadir nueva**
2. Espera a que cargue el editor

#### 6. Configurar título

**Título sugerido:**
```
Demo Rhinometric - Descarga OVA
```

Alternativas:
- `Evaluación 4 Horas - Rhinometric Demo`
- `Rhinometric Demo OVA - Prueba Gratuita`

#### 7. Cambiar a editor HTML

**Si usas Gutenberg (editor por defecto WordPress 5.0+):**
1. Click en los **tres puntos verticales** (arriba derecha)
2. **Preferencias** o **Preferences**
3. Busca opción "Editor de código" o "Code editor"
4. O directamente: `Ctrl+Shift+Alt+M` (atajo)

**Si usas Classic Editor:**
1. Click en pestaña **Texto** (junto a "Visual")

#### 8. Pegar HTML

- Borra cualquier contenido que haya
- Pega el HTML copiado (`Ctrl+V`)

#### 9. Vista previa

- Click en **Vista previa** (botón arriba derecha)
- Se abrirá nueva pestaña mostrando la página

**Verificar:**
- ✅ Hero section con gradiente púrpura
- ✅ Título "Rhinometric Demo OVA" visible
- ✅ Badges (4h, VirtualBox, etc.)
- ✅ Botón de descarga visible
- ✅ Grid de features con 6 tarjetas
- ✅ Footer con diseño correcto

#### 10. Configurar permalink

1. En el panel derecho: **Enlace permanente** o **Permalink**
2. Cambiar a: `demo` o `demo-ova`
3. URL final será: `https://rhinometric.com/demo`

#### 11. Publicar

- Click en **Publicar** (botón azul arriba derecha)
- Confirmar "¿Estás seguro?"
- Esperar mensaje "Página publicada"

#### 12. Verificar página publicada

Abre en nueva pestaña:
```
https://rhinometric.com/demo
```

**Click en el botón de descarga** para verificar que funciona (descargará OVA o dará 404 si no está subida aún).

---

### Página 2: Trial Linux

Sigue los mismos pasos que Demo OVA, pero con estos valores:

**Archivo:** `02-trial-linux-page.html`

**Título sugerido:**
```
Trial Rhinometric - 14 Días Gratis
```

**Permalink:** `trial` o `trial-linux`

**URL final:** `https://rhinometric.com/trial`

**Qué verificar en vista previa:**
- ✅ Hero section con gradiente VERDE (no púrpura)
- ✅ Badges: 14 días, 5 hosts, Auto-installation
- ✅ Botón "Descargar Instalador Linux"
- ✅ Grid de plataformas (Ubuntu, Debian, CentOS, RHEL)
- ✅ Comandos de instalación con bloques de código
- ✅ Warning box amarillo con limitaciones trial
- ✅ CTA de upgrade

**Botón descarga apunta a:**
```
https://licensing.rhinometric.com:5000/downloads/trial-installer
```

---

### Página 3: Documentación

**Archivo:** `03-documentation-page.html`

**Título sugerido:**
```
Documentación Rhinometric v2.5.0
```

**Permalink:** `documentation` o `docs`

**URL final:** `https://rhinometric.com/documentation`

**Qué verificar en vista previa:**
- ✅ Hero section con gradiente AZUL
- ✅ Grid de 4 tarjetas de documentación
- ✅ Guía Instalación: 2 botones (ES/EN)
- ✅ Manual Usuario: 2 botones (ES/EN)
- ✅ API Reference: enlace funcional
- ✅ Architecture Guide: enlace funcional
- ✅ Quick links section con 6 enlaces
- ✅ Video tutorials (coming soon)
- ✅ GDPR notice azul claro
- ✅ Footer stats (versión 2.5.0, componentes, dashboards)

**Botones de descarga apuntan a:**
```
/docs/installation-guide?lang=es
/docs/installation-guide?lang=en
/docs/user-manual?lang=es
/docs/user-manual?lang=en
```

---

## Configuración de Menús

Una vez publicadas las 3 páginas, agrégalas al menú principal de tu sitio.

### 1. Acceder a Menús

```
WordPress Admin → Apariencia → Menús
```

### 2. Seleccionar menú (o crear uno nuevo)

Si ya tienes un menú principal, selecciónalo.

Si no:
1. **Crear un menú nuevo**
2. Nombre: "Menú Principal" o "Main Menu"
3. **Ubicación:** Primary Menu / Menú Principal

### 3. Añadir las páginas

En el panel izquierdo "Páginas":
1. Busca las 3 páginas recién creadas
2. Selecciona las 3
3. Click "Añadir al menú"

### 4. Organizar estructura

**Opción A: Menú plano**
```
Home
Productos
  ├─ Demo OVA (4h)
  ├─ Trial Linux (14 días)
Recursos
  ├─ Documentación
  ├─ Soporte
Contacto
```

**Opción B: Menú con dropdowns**
```
Home
Productos ▼
  ├─ Demo OVA
  ├─ Trial Linux
  └─ Licencias Annual
Recursos ▼
  ├─ Documentación
  ├─ API Reference
  ├─ GitHub
  └─ Soporte
Pricing
Contacto
```

**Arrastrar y soltar** las páginas para crear la jerarquía deseada.

**Indentar:** Arrastra ligeramente a la derecha para hacer sub-ítem.

### 5. Guardar menú

Click en **Guardar menú** (botón azul abajo)

### 6. Verificar en sitio web

Abre tu sitio y verifica que el menú aparece correctamente:
```
https://rhinometric.com
```

---

## Personalización

### Cambiar Textos Comerciales

#### Demo OVA - Textos editables

**Línea 226 (Hero title):**
```html
<h1>Prueba Rhinometric Demo OVA</h1>
```
→ Puedes cambiar a:
```html
<h1>Evalúa Rhinometric en 4 Horas</h1>
```

**Línea 228 (Subtitle):**
```html
<p class="subtitle">Evaluación gratuita de 4 horas...</p>
```

**Línea 236 (Botón texto):**
```html
📥 Descargar Demo OVA (4h)
```

#### Trial Linux - Textos editables

**Línea 218 (Hero title):**
```html
<h1>Rhinometric Trial - 14 Días Gratis</h1>
```

**Línea 220 (Subtitle):**
```html
<p class="subtitle">Instalación completa en tu servidor Linux...</p>
```

**Línea 228 (Botón texto):**
```html
📥 Descargar Instalador (14 días)
```

**Línea 334 (Pricing CTA):**
```html
<p style="font-size: 28px; color: #2c3e50; margin-bottom: 5px;">$1,999/año</p>
```

#### Documentación - Textos editables

**Línea 216 (Hero title):**
```html
<h1>Documentación Rhinometric</h1>
```

**Línea 225 (Subtitle):**
```html
Manuales, guías y recursos para dominar Rhinometric v2.5.0
```

**Línea 347 (Quick links section):**
Puedes añadir/quitar enlaces editando la lista `<ul>` en líneas 347-360.

---

### Cambiar Colores

Todos los estilos están inline (dentro de las etiquetas `style="..."`), así que son fáciles de cambiar.

#### Demo OVA - Gradiente principal (púrpura)

**Buscar:**
```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

**Cambiar a otro gradiente (ejemplo: naranja):**
```css
background: linear-gradient(135deg, #f857a6 0%, #ff5858 100%);
```

**Generador de gradientes:** https://cssgradient.io/

#### Trial Linux - Gradiente principal (verde)

**Buscar:**
```css
background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
```

#### Documentación - Gradiente principal (azul)

**Buscar:**
```css
background: linear-gradient(135deg, #0093E9 0%, #80D0C7 100%);
```

---

### Añadir Logo o Imagen

Si quieres añadir una imagen en el hero section:

**Antes del título, añade:**
```html
<img src="https://rhinometric.com/wp-content/uploads/2025/12/rhinometric-logo.png" 
     alt="Rhinometric Logo" 
     style="max-width: 300px; margin-bottom: 30px;">
<h1>Prueba Rhinometric Demo OVA</h1>
```

---

### Cambiar Tamaño de Fuentes

Si ves que el texto es muy grande o muy pequeño:

**Hero title:**
```html
<h1 style="font-size: 42px;">   <!-- Cambia 42px a 36px o 48px -->
```

**Subtítulo:**
```html
<p class="subtitle" style="font-size: 20px;">   <!-- Cambia a 18px o 22px -->
```

---

## Verificación Final

### Checklist de Testing

Una vez publicadas las 3 páginas, verifica:

#### Diseño Responsive

- [ ] **Desktop (1920x1080):** Todo se ve bien, sin desbordamientos
- [ ] **Tablet (768x1024):** Diseño se adapta, columnas se apilan
- [ ] **Mobile (375x667):** Diseño móvil, botones táctiles funcionan

**Cómo probar:**
- Chrome/Edge: `F12` → Toggle device toolbar → Seleccionar dispositivo
- Firefox: `Ctrl+Shift+M` → Responsive Design Mode

#### Navegación

- [ ] Menú principal muestra las 3 páginas
- [ ] Links del menú funcionan (no 404)
- [ ] Breadcrumbs (si los tienes) muestran ruta correcta

#### Enlaces de Descarga

**Demo OVA:**
- [ ] Click en botón "Descargar Demo OVA"
- [ ] URL es: `https://licensing.rhinometric.com:5000/downloads/demo-ova`
- [ ] Descarga archivo OVA (o 404 si no subido aún)

**Trial Linux:**
- [ ] Click en botón "Descargar Instalador Linux"
- [ ] URL es: `https://licensing.rhinometric.com:5000/downloads/trial-installer`
- [ ] Descarga `.sh` script (o 404 si no subido)

**Documentación - PDFs:**
- [ ] Click "Descargar PDF (ES)" → Guía Instalación
- [ ] Click "Descargar PDF (EN)" → Installation Guide
- [ ] Click "Descargar PDF (ES)" → Manual Usuario
- [ ] Click "Descargar PDF (EN)" → User Manual
- [ ] Todos abren PDFs (o 404 si no subidos)

#### Estilo Visual

- [ ] Gradientes se ven suaves (no pixelados)
- [ ] Botones tienen hover effect (cambia sombra al pasar mouse)
- [ ] Tarjetas/cards tienen sombra
- [ ] Textos son legibles (contraste adecuado)
- [ ] Iconos/emojis se ven bien

#### Compatibilidad de Navegador

Probar en:
- [ ] Chrome/Edge (90%+ de usuarios)
- [ ] Firefox
- [ ] Safari (si tienes Mac)
- [ ] Mobile Safari (iOS)
- [ ] Mobile Chrome (Android)

#### SEO Básico

- [ ] Título de página (`<title>`) es descriptivo
- [ ] Meta description existe
- [ ] URL es corta y limpia (`/demo` no `/pagina-123`)
- [ ] Headings jerarquía correcta (H1 → H2 → H3)

**Añadir meta tags (opcional):**

En WordPress Admin → Página Demo → Panel derecho → **Yoast SEO** o **Rank Math**:
- **Meta Title:** `Rhinometric Demo OVA - Prueba Gratis 4 Horas`
- **Meta Description:** `Descarga la demo OVA de Rhinometric y evalúa nuestra plataforma de observabilidad en 4 horas. Compatible con VirtualBox y VMware.`

---

## URLs Finales

Una vez publicado todo, estas serán tus URLs:

| Página | URL | Endpoint Descarga |
|--------|-----|-------------------|
| **Demo OVA** | `https://rhinometric.com/demo` | `/downloads/demo-ova` |
| **Trial Linux** | `https://rhinometric.com/trial` | `/downloads/trial-installer` |
| **Documentación** | `https://rhinometric.com/documentation` | `/docs/installation-guide?lang=es` |
|  |  | `/docs/user-manual?lang=en` |

### Share en Redes Sociales

**Demo OVA:**
```
🦏 ¿Quieres probar Rhinometric sin instalar nada?

Descarga nuestra Demo OVA y evalúa la plataforma completa en 4 horas.
✅ VirtualBox/VMware ready
✅ Stack completo incluido
✅ Sin configuración

👉 https://rhinometric.com/demo
```

**Trial Linux:**
```
🚀 Prueba Rhinometric en tu servidor Linux - GRATIS 14 días

✅ Instalación automática
✅ Ubuntu, Debian, CentOS compatible
✅ Hasta 5 hosts monitorizados

👉 https://rhinometric.com/trial
```

---

## Siguientes Pasos

Después de publicar las páginas:

1. **Analytics**
   - Añadir Google Analytics a las 3 páginas
   - Trackear clicks en botones de descarga
   - Medir conversión de visitas → descargas

2. **A/B Testing**
   - Probar diferentes títulos en hero section
   - Probar diferentes colores de botones
   - Probar diferentes CTAs

3. **Email Marketing**
   - Crear campaña de email apuntando a `/trial`
   - Newsletter con link a `/documentation`

4. **SEO**
   - Crear sitemap XML incluyendo las 3 páginas
   - Submit a Google Search Console
   - Añadir Open Graph tags para Facebook/LinkedIn

5. **Contenido Adicional**
   - Crear blog posts sobre casos de uso
   - Video tutorials en YouTube
   - Webinars de demostración

---

## Troubleshooting

### Problema: HTML se ve como texto plano

**Síntoma:** En vez de ver la página diseñada, ves el código HTML crudo.

**Causa:** WordPress no está en modo HTML, está en modo Visual/WYSIWYG.

**Solución:**
1. Editar página
2. Cambiar a modo "Texto" o "HTML"
3. Pegar de nuevo

---

### Problema: Diseño se rompe (CSS no funciona)

**Síntoma:** Página sin colores, todo texto negro sobre blanco.

**Causa:** Tema de WordPress está sobrescribiendo estilos inline.

**Solución:**
1. Añadir `!important` a estilos críticos:
   ```css
   background: linear-gradient(...) !important;
   ```
2. O usar plugin "Custom CSS" y añadir:
   ```css
   .rhino-demo-container * {
       all: unset;
   }
   ```

---

### Problema: Botón de descarga no funciona

**Síntoma:** Click en botón → nada pasa o 404.

**Causa:** License Server no está corriendo o archivo no existe.

**Solución:**
1. Verificar License Server:
   ```bash
   curl https://licensing.rhinometric.com:5000/api/health
   ```
2. Verificar archivos:
   ```bash
   curl -I https://licensing.rhinometric.com:5000/downloads/demo-ova
   ```
3. Si 404 → Subir archivos (ver [DEPLOYMENT_CHECKLIST.md](../DEPLOYMENT_CHECKLIST.md))

---

### Problema: Página muy ancha en móvil

**Síntoma:** Hay que hacer scroll horizontal en móvil.

**Causa:** Algún elemento tiene ancho fijo muy grande.

**Solución:**
Añadir al inicio del HTML (después del `<style>`):
```css
* {
    max-width: 100% !important;
}
```

---

## Recursos Adicionales

- **WordPress Codex:** https://codex.wordpress.org/Pages
- **HTML Validator:** https://validator.w3.org/
- **Responsive Checker:** https://responsivedesignchecker.com/
- **Page Speed Insights:** https://pagespeed.web.dev/

---

## Soporte

Si encuentras problemas durante la publicación:

📧 **Email:** rafael.canelon@rhinometric.com  
📁 **Archivos:** `docs/v2.5.0/wordpress/`  
📚 **Docs técnicas:** `docs/v2.5.0/DOWNLOAD_ENDPOINTS.md`

---

**Última actualización:** 16 Diciembre 2025  
**Versión:** 2.5.0  
**Autor:** Rafael Canelón
