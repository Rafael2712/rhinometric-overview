#!/usr/bin/env python3
"""
Script para convertir el documento de auditoría Markdown a PDF usando WeasyPrint
"""

import markdown
from weasyprint import HTML, CSS
from pathlib import Path
import sys

def convert_md_to_pdf(md_file: str):
    """Convierte un archivo Markdown a PDF con estilos profesionales"""
    
    md_path = Path(md_file)
    if not md_path.exists():
        print(f"❌ Error: El archivo {md_file} no existe")
        sys.exit(1)
    
    print(f"🔄 Leyendo {md_file}...")
    
    # Leer contenido Markdown
    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Convertir Markdown a HTML
    print("🔄 Convirtiendo Markdown a HTML...")
    html_content = markdown.markdown(
        md_content,
        extensions=[
            'tables',
            'fenced_code',
            'codehilite',
            'toc',
            'nl2br',
            'sane_lists'
        ]
    )
    
    # HTML template con estilos
    html_template = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Auditoría Rhinometric v2.5.0</title>
        <style>
            @page {{
                size: A4;
                margin: 2cm;
                @top-center {{
                    content: "Rhinometric v2.5.0 - Auditoría Técnica";
                    font-size: 10pt;
                    color: #666;
                }}
                @bottom-center {{
                    content: "Página " counter(page) " de " counter(pages);
                    font-size: 10pt;
                    color: #666;
                }}
            }}
            
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 100%;
                margin: 0;
                padding: 0;
            }}
            
            h1 {{
                color: #2563eb;
                border-bottom: 3px solid #2563eb;
                padding-bottom: 10px;
                margin-top: 30px;
                page-break-before: always;
            }}
            
            h1:first-of-type {{
                page-break-before: auto;
            }}
            
            h2 {{
                color: #1e40af;
                border-bottom: 2px solid #93c5fd;
                padding-bottom: 8px;
                margin-top: 25px;
            }}
            
            h3 {{
                color: #1e3a8a;
                margin-top: 20px;
            }}
            
            h4 {{
                color: #1e293b;
                margin-top: 15px;
            }}
            
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                font-size: 0.9em;
                page-break-inside: auto;
            }}
            
            tr {{
                page-break-inside: avoid;
                page-break-after: auto;
            }}
            
            thead {{
                display: table-header-group;
            }}
            
            table th {{
                background-color: #2563eb;
                color: white;
                padding: 12px;
                text-align: left;
                font-weight: 600;
            }}
            
            table td {{
                border: 1px solid #e5e7eb;
                padding: 10px;
                background-color: #f9fafb;
            }}
            
            table tr:hover td {{
                background-color: #f3f4f6;
            }}
            
            code {{
                background-color: #f1f5f9;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 0.9em;
                color: #dc2626;
            }}
            
            pre {{
                background-color: #1e293b;
                color: #e2e8f0;
                padding: 15px;
                border-radius: 6px;
                overflow-x: auto;
                page-break-inside: avoid;
            }}
            
            pre code {{
                background-color: transparent;
                color: inherit;
                padding: 0;
            }}
            
            ul, ol {{
                margin-left: 25px;
                margin-bottom: 15px;
            }}
            
            li {{
                margin-bottom: 8px;
            }}
            
            blockquote {{
                border-left: 4px solid #2563eb;
                padding-left: 15px;
                margin-left: 0;
                color: #64748b;
                font-style: italic;
            }}
            
            a {{
                color: #2563eb;
                text-decoration: none;
            }}
            
            a:hover {{
                text-decoration: underline;
            }}
            
            .checkmark {{
                color: #22c55e;
                font-weight: bold;
            }}
            
            .cross {{
                color: #ef4444;
                font-weight: bold;
            }}
            
            .warning {{
                color: #f59e0b;
                font-weight: bold;
            }}
            
            hr {{
                border: none;
                border-top: 2px solid #e5e7eb;
                margin: 30px 0;
            }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    # Generar PDF
    output_path = md_path.with_suffix('.pdf')
    print(f"🔄 Generando PDF: {output_path.name}...")
    
    try:
        HTML(string=html_template).write_pdf(
            output_path,
            stylesheets=[
                CSS(string='''
                    @page { 
                        size: A4; 
                        margin: 2cm;
                    }
                ''')
            ]
        )
        
        print(f"✅ PDF generado exitosamente: {output_path}")
        print(f"📄 Tamaño: {output_path.stat().st_size / 1024:.1f} KB")
        
    except Exception as e:
        print(f"❌ Error generando PDF: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Uso: python convert-audit-to-pdf.py <archivo.md>")
        sys.exit(1)
    
    convert_md_to_pdf(sys.argv[1])
