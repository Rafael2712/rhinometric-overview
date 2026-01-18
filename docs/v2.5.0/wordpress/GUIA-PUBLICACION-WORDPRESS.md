# Guía de Publicación de Páginas en WordPress

**Servidor:** rhinometric.com  
**Acceso:** https://rhinometric.com/wp-admin  
**Fecha:** 16 de Diciembre 2025

---

## 📋 PÁGINAS A PUBLICAR (5 total)

### 1️⃣ HOME - Página de Inicio
- **Archivo:** `00-home-page.html`
- **Título WordPress:** Home
- **Slug/URL:** `/` (página principal)
- **Plantilla:** Página Completa (Full Width)

### 2️⃣ DEMO OVA - Descarga Demo
- **Archivo:** `01-demo-ova-page.html`
- **Título WordPress:** Demo
- **Slug/URL:** `/demo`
- **Plantilla:** Página Completa (Full Width)

### 3️⃣ TRIAL LINUX - Formulario Trial
- **Archivo:** `02-trial-linux-page.html`
- **Título WordPress:** Trial
- **Slug/URL:** `/trial`
- **Plantilla:** Página Completa (Full Width)
- **⚠️ IMPORTANTE:** Contiene JavaScript que conecta a API: `http://54.197.192.198:8090/api/v1/trial/generate`

### 4️⃣ DOCUMENTATION - Documentación
- **Archivo:** `03-documentation-page.html`
- **Título WordPress:** Documentation
- **Slug/URL:** `/documentation`
- **Plantilla:** Página Completa (Full Width)

### 5️⃣ CONTACT - Contacto
- **Archivo:** `04-contact-page.html`
- **Título WordPress:** Contact
- **Slug/URL:** `/contact`
- **Plantilla:** Página Completa (Full Width)

---

## 🚀 PROCESO DE PUBLICACIÓN (PASO A PASO)

### PASO 1: Acceder a WordPress Admin
1. Abrir navegador
2. Ir a: `https://rhinometric.com/wp-admin`
3. Usuario: `[tu usuario de WordPress]`
4. Contraseña: `[tu contraseña de WordPress]`

### PASO 2: Crear Nueva Página (REPETIR PARA CADA UNA)

#### 2.1 Crear Página
1. En el menú lateral izquierdo: **Páginas → Añadir nueva**
2. Título de la página: `[Ver lista arriba]`
3. Click en el botón **"⋮"** (3 puntos verticales arriba a la derecha)
4. Seleccionar: **Editor de código** (Code Editor)

#### 2.2 Copiar HTML
1. Abrir el archivo HTML correspondiente (00-home-page.html, etc.)
2. **COPIAR TODO EL CONTENIDO** del archivo (Ctrl+A, Ctrl+C)

#### 2.3 Pegar en WordPress
1. En el editor de código de WordPress: **BORRAR TODO** el contenido existente
2. **PEGAR** el HTML copiado (Ctrl+V)
3. Click en **"⋮"** → Volver a **Editor visual** (para verificar que se ve bien)

#### 2.4 Configurar Opciones
1. En el panel derecho **"Configuración de página"**:
   - **Permalink (URL):** Establecer el slug correcto (ver lista arriba)
   - **Plantilla:** Seleccionar "Página Completa" o "Full Width"
   - **Visibilidad:** Público
   - **Estado:** Publicado

2. Click en **"Publicar"** (botón azul arriba a la derecha)

#### 2.5 Verificar
1. Click en **"Ver página"** después de publicar
2. Verificar que se vea correctamente
3. Si hay problemas de CSS, puede ser necesario ajustar el tema

### PASO 3: Configurar Home como Página Principal
1. En WordPress Admin: **Ajustes → Lectura**
2. En "Tu página de inicio muestra":
   - Seleccionar: **Una página estática**
   - Página de inicio: Seleccionar **"Home"**
3. Click en **"Guardar cambios"**

---

## ⚙️ CONFIGURACIONES ADICIONALES

### Menú de Navegación
1. **Apariencia → Menús**
2. Crear menú llamado "Principal" o "Main Menu"
3. Agregar las 5 páginas en este orden:
   - Home (Inicio)
   - Demo
   - Trial
   - Documentation
   - Contact
4. Asignar a "Menú Principal" o "Primary Menu"

### Verificar URLs
Después de publicar, verificar que las URLs funcionen:
- `https://rhinometric.com/` → Home
- `https://rhinometric.com/demo` → Demo
- `https://rhinometric.com/trial` → Trial
- `https://rhinometric.com/documentation` → Documentation
- `https://rhinometric.com/contact` → Contact

---

## 🔧 SOLUCIÓN DE PROBLEMAS

### Problema 1: El CSS no se ve bien
**Solución:**
- El tema de WordPress puede estar interfiriendo
- Opción A: Usar un tema "blank" o minimalista
- Opción B: Agregar CSS personalizado en **Apariencia → Personalizar → CSS adicional**

### Problema 2: El JavaScript del formulario trial no funciona
**Solución:**
- Verificar que WordPress no esté bloqueando el script
- Puede ser necesario instalar plugin "Allow HTML in WordPress"
- O usar un plugin de código personalizado como "Code Snippets"

### Problema 3: Links externos bloqueados (CORS)
**Solución:**
- El servidor AWS (54.197.192.198:8090) ya tiene CORS habilitado
- Si persiste, verificar en consola del navegador (F12)

### Problema 4: Páginas 404 después de publicar
**Solución:**
1. **Ajustes → Enlaces permanentes**
2. Seleccionar "Nombre de la entrada"
3. Click en "Guardar cambios"
4. Esto regenera los permalinks

---

## ✅ CHECKLIST FINAL

Después de publicar todas las páginas, verificar:

- [ ] **Home (/)** - Página principal se ve correctamente
- [ ] **Demo (/demo)** - Botón de descarga OVA funciona
- [ ] **Trial (/trial)** - Formulario envía datos a API y muestra respuesta
- [ ] **Documentation (/documentation)** - Página se muestra (contenido básico)
- [ ] **Contact (/contact)** - Formulario de contacto visible
- [ ] **Menú de navegación** - Todas las páginas accesibles desde menú
- [ ] **Link del email** - `rhinometric.com/documentation` ahora funciona (no más 404)
- [ ] **Mobile responsive** - Páginas se ven bien en móvil

---

## 📝 NOTAS IMPORTANTES

### Formulario Trial (02-trial-linux-page.html)
Este formulario contiene JavaScript que hace POST a:
```
http://54.197.192.198:8090/api/v1/trial/generate
```

**NO cambiar esta URL** - es la correcta para el servidor de licencias AWS.

### Link de Documentation en emails
Una vez publicada la página `/documentation`, el link en los emails de licencias anuales funcionará automáticamente:
```
https://rhinometric.com/documentation
```

### Backup
Antes de hacer cambios importantes:
1. **Herramientas → Exportar** (exportar todo el contenido)
2. Guardar el archivo XML de backup

---

## 🎯 PRÓXIMOS PASOS (DESPUÉS DE PUBLICAR)

1. **Probar formulario trial end-to-end:**
   - Ir a https://rhinometric.com/trial
   - Llenar formulario
   - Verificar que se cree licencia en AWS
   - Verificar que llegue email

2. **Crear contenido para Documentation:**
   - Agregar guías de instalación
   - Agregar manuales de usuario
   - Agregar FAQs

3. **Mejorar SEO:**
   - Instalar plugin Yoast SEO
   - Configurar meta descriptions
   - Agregar imágenes con alt text

4. **Analytics:**
   - Agregar Google Analytics
   - Configurar seguimiento de conversiones

---

**¿Dudas o problemas durante la publicación?**  
Avísame y te ayudo a resolverlos en tiempo real.
