# 📄 Conversión de Documentación a PDF

Este directorio contiene la documentación en Markdown que debe convertirse a PDF para adjuntar en los emails de licencias.

## Archivos Markdown

- **manual_usuario.md** (20 páginas) - Manual completo del usuario
- **guia_instalacion.md** (15 páginas) - Guía de instalación paso a paso

## Conversión a PDF

### Opción 1: Pandoc (Recomendado)

```bash
# Instalar Pandoc
# Ubuntu/Debian
sudo apt-get install pandoc texlive-latex-base texlive-fonts-recommended

# macOS
brew install pandoc basictex

# Windows
# Descargar desde: https://pandoc.org/installing.html

# Convertir archivos
cd docs/
pandoc manual_usuario.md -o manual_usuario.pdf --toc --toc-depth=2 --pdf-engine=xelatex
pandoc guia_instalacion.md -o guia_instalacion.pdf --toc --toc-depth=2 --pdf-engine=xelatex
```

### Opción 2: Markdown to PDF (VS Code Extension)

1. Instalar extensión: https://marketplace.visualstudio.com/items?itemName=yzane.markdown-pdf
2. Abrir `manual_usuario.md` en VS Code
3. `Ctrl+Shift+P` → "Markdown PDF: Export (pdf)"
4. Repetir con `guia_instalacion.md`

### Opción 3: Online Converter

1. Ir a: https://www.markdowntopdf.com/
2. Subir `manual_usuario.md`
3. Descargar PDF
4. Repetir con `guia_instalacion.md`

## Verificación

Después de convertir, verificar que los PDFs están en este directorio:

```bash
ls -lh docs/
# Debe mostrar:
# manual_usuario.pdf (≈1.5 MB)
# guia_instalacion.pdf (≈800 KB)
```

## Uso en Emails

Los PDFs se adjuntan automáticamente cuando se crea una licencia a través de la API:

```bash
POST http://localhost:5000/api/admin/licenses
```

El sistema busca los PDFs en `/app/docs/` (montado desde este directorio en Docker).

## Política de Privacidad GDPR

⚠️ **PENDIENTE**: `politica_privacidad_GDPR.pdf` requiere contenido legal.

Este archivo NO se adjunta en emails hasta que se cree con información legal correcta:
- Empresa registrada en UE
- Datos personales almacenados
- Ubicación de servidores
- Procesadores de datos terceros
- Información del DPO (Data Protection Officer)

Contactar departamento legal antes de crear este documento.
