#!/usr/bin/env python3
"""
Convierte archivos Markdown a HTML con estilo profesional
Luego se pueden convertir a PDF usando el navegador (Ctrl+P -> Guardar como PDF)
"""

import markdown
import os
from pathlib import Path

# Archivos a convertir
files_to_convert = [
    "RESUMEN_EJECUTIVO_RHINOMETRIC_FACTUAL.md",
    "RESUMEN_TECNICO_RHINOMETRIC_FACTUAL.md",
    "BACKLOG_RHINOMETRIC_FACTUAL.md"
]

# CSS profesional para el PDF
css_style = """
<style>
    @page {
        size: A4;
        margin: 2cm;
    }
    
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        line-height: 1.6;
        color: #333;
        max-width: 900px;
        margin: 0 auto;
        padding: 20px;
    }
    
    h1 {
        color: #2c3e50;
        border-bottom: 3px solid #3498db;
        padding-bottom: 10px;
        margin-top: 40px;
        page-break-before: always;
    }
    
    h1:first-of-type {
        page-break-before: auto;
    }
    
    h2 {
        color: #34495e;
        border-bottom: 2px solid #95a5a6;
        padding-bottom: 8px;
        margin-top: 30px;
    }
    
    h3 {
        color: #555;
        margin-top: 20px;
    }
    
    h4 {
        color: #666;
        margin-top: 15px;
    }
    
    code {
        background-color: #f4f4f4;
        padding: 2px 6px;
        border-radius: 3px;
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 0.9em;
    }
    
    pre {
        background-color: #f8f8f8;
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 15px;
        overflow-x: auto;
        page-break-inside: avoid;
    }
    
    pre code {
        background-color: transparent;
        padding: 0;
    }
    
    table {
        border-collapse: collapse;
        width: 100%;
        margin: 20px 0;
        page-break-inside: avoid;
    }
    
    th {
        background-color: #3498db;
        color: white;
        padding: 12px;
        text-align: left;
        font-weight: bold;
    }
    
    td {
        border: 1px solid #ddd;
        padding: 10px;
    }
    
    tr:nth-child(even) {
        background-color: #f9f9f9;
    }
    
    blockquote {
        border-left: 4px solid #3498db;
        padding-left: 20px;
        margin: 20px 0;
        color: #555;
        font-style: italic;
    }
    
    ul, ol {
        margin: 15px 0;
        padding-left: 30px;
    }
    
    li {
        margin: 8px 0;
    }
    
    a {
        color: #3498db;
        text-decoration: none;
    }
    
    a:hover {
        text-decoration: underline;
    }
    
    hr {
        border: none;
        border-top: 2px solid #ddd;
        margin: 40px 0;
    }
    
    .header-info {
        background-color: #ecf0f1;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 30px;
    }
    
    .download-pdf-btn {
        position: fixed;
        top: 20px;
        right: 20px;
        background: linear-gradient(135deg, #3498db, #2980b9);
        color: white;
        padding: 12px 24px;
        border: none;
        border-radius: 8px;
        font-size: 16px;
        font-weight: bold;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(52, 152, 219, 0.3);
        transition: all 0.3s ease;
        z-index: 1000;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .download-pdf-btn:hover {
        background: linear-gradient(135deg, #2980b9, #21618c);
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(52, 152, 219, 0.4);
    }
    
    .download-pdf-btn:active {
        transform: translateY(0);
    }
    
    @media print {
        .download-pdf-btn {
            display: none !important;
        }
        
        .header-info {
            page-break-after: avoid;
        }
        
        body {
            font-size: 11pt;
        }
        
        h1 {
            font-size: 24pt;
        }
        
        h2 {
            font-size: 18pt;
        }
        
        h3 {
            font-size: 14pt;
        }
        
        a {
            color: #000;
            text-decoration: none;
        }
        
        pre, blockquote, table {
            page-break-inside: avoid;
        }
    }
</style>
"""

def convert_markdown_to_html(md_file):
    """Convierte un archivo Markdown a HTML"""
    
    # Leer el archivo Markdown
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Convertir Markdown a HTML
    md = markdown.Markdown(extensions=[
        'tables',
        'fenced_code',
        'nl2br',
        'sane_lists'
    ])
    html_content = md.convert(md_content)
    
    # Nombre del archivo de salida
    html_file = md_file.replace('.md', '.html')
    
    # HTML completo con estilos
    full_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{Path(md_file).stem}</title>
    {css_style}
</head>
<body>
    <button class="download-pdf-btn" onclick="window.print()">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="7 10 12 15 17 10"></polyline>
            <line x1="12" y1="15" x2="12" y2="3"></line>
        </svg>
        Descargar PDF
    </button>
    
    <div class="header-info">
        <p><strong>Generado automáticamente desde:</strong> {md_file}</p>
        <p><strong>Fecha de generación:</strong> 17 de Diciembre, 2025</p>
    </div>
    {html_content}
    <hr>
    <footer style="text-align: center; color: #999; font-size: 0.9em; margin-top: 50px;">
        <p>© 2025 Rhinometric. Documento generado automáticamente.</p>
    </footer>
</body>
</html>
"""
    
    # Guardar HTML
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(full_html)
    
    print(f"✅ Convertido: {md_file} → {html_file}")
    return html_file

if __name__ == "__main__":
    print("🔄 Convirtiendo archivos Markdown a HTML...\n")
    
    html_files = []
    for md_file in files_to_convert:
        if os.path.exists(md_file):
            html_file = convert_markdown_to_html(md_file)
            html_files.append(html_file)
        else:
            print(f"❌ No encontrado: {md_file}")
    
    print("\n✅ Conversión completada!")
    print("\n📄 Archivos HTML generados:")
    for html_file in html_files:
        print(f"   - {html_file}")
    
    print("\n📋 INSTRUCCIONES PARA GENERAR PDFs:")
    print("   1. Abre cada archivo HTML en tu navegador (Chrome/Edge recomendado)")
    print("   2. Presiona Ctrl+P (o Cmd+P en Mac)")
    print("   3. Selecciona 'Guardar como PDF' como destino")
    print("   4. Ajusta márgenes si es necesario (recomendado: predeterminados)")
    print("   5. Haz clic en 'Guardar'")
    print("\n   Alternativamente, los archivos HTML se abrirán automáticamente ahora...")
