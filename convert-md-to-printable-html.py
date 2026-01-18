#!/usr/bin/env python3
"""
Script para convertir Markdown a HTML estilizado (imprimible a PDF)
"""

import markdown
from pathlib import Path
import sys
import webbrowser

def convert_md_to_html(md_file: str):
    """Convierte Markdown a HTML con estilos profesionales para impresión"""
    
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
    html_body = markdown.markdown(
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
    
    # HTML template completo con estilos para impresión
    html_template = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rhinometric v2.5.0 - Auditoría Técnica Completa</title>
    <style>
        /* Estilos de impresión */
        @media print {{
            @page {{
                size: A4;
                margin: 1.5cm 2cm;
            }}
            
            body {{
                font-size: 11pt;
                line-height: 1.4;
            }}
            
            h1 {{
                page-break-before: always;
                font-size: 20pt;
                margin-top: 0;
            }}
            
            h1:first-of-type {{
                page-break-before: auto;
            }}
            
            h2 {{
                page-break-after: avoid;
                font-size: 16pt;
            }}
            
            h3 {{
                page-break-after: avoid;
                font-size: 14pt;
            }}
            
            table, pre, blockquote {{
                page-break-inside: avoid;
            }}
            
            tr {{
                page-break-inside: avoid;
            }}
            
            a {{
                color: #2563eb;
                text-decoration: none;
            }}
            
            /* Ocultar elementos no necesarios en impresión */
            .print-instructions {{
                display: none;
            }}
        }}
        
        /* Estilos de pantalla */
        @media screen {{
            body {{
                max-width: 1200px;
                margin: 0 auto;
                padding: 40px 20px;
                background-color: #f8fafc;
            }}
            
            .content-wrapper {{
                background-color: white;
                padding: 40px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                border-radius: 8px;
            }}
            
            .print-instructions {{
                background-color: #dbeafe;
                border: 2px solid #2563eb;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 30px;
                text-align: center;
            }}
            
            .print-instructions h2 {{
                color: #1e40af;
                margin-top: 0;
            }}
            
            .print-btn {{
                background-color: #2563eb;
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 16px;
                border-radius: 6px;
                cursor: pointer;
                margin: 10px;
            }}
            
            .print-btn:hover {{
                background-color: #1e40af;
            }}
        }}
        
        /* Estilos comunes */
        body {{
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, 'Roboto', 'Helvetica', 'Arial', sans-serif;
            color: #1e293b;
            line-height: 1.6;
        }}
        
        h1 {{
            color: #0f172a;
            border-bottom: 4px solid #2563eb;
            padding-bottom: 12px;
            margin-top: 40px;
            font-size: 2.2em;
        }}
        
        h2 {{
            color: #1e40af;
            border-bottom: 2px solid #93c5fd;
            padding-bottom: 10px;
            margin-top: 35px;
            font-size: 1.8em;
        }}
        
        h3 {{
            color: #1e3a8a;
            margin-top: 28px;
            font-size: 1.5em;
        }}
        
        h4 {{
            color: #334155;
            margin-top: 22px;
            font-size: 1.2em;
        }}
        
        /* Tablas */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 25px 0;
            font-size: 0.95em;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }}
        
        table thead tr {{
            background-color: #2563eb;
            color: white;
            text-align: left;
        }}
        
        table th {{
            padding: 14px 12px;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.85em;
            letter-spacing: 0.5px;
        }}
        
        table td {{
            padding: 12px;
            border: 1px solid #e2e8f0;
        }}
        
        table tbody tr {{
            background-color: #ffffff;
            border-bottom: 1px solid #e2e8f0;
        }}
        
        table tbody tr:nth-of-type(even) {{
            background-color: #f8fafc;
        }}
        
        table tbody tr:hover {{
            background-color: #f1f5f9;
        }}
        
        /* Código */
        code {{
            background-color: #f1f5f9;
            padding: 3px 7px;
            border-radius: 4px;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 0.9em;
            color: #dc2626;
            border: 1px solid #e2e8f0;
        }}
        
        pre {{
            background-color: #1e293b;
            color: #e2e8f0;
            padding: 20px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}
        
        pre code {{
            background-color: transparent;
            color: inherit;
            padding: 0;
            border: none;
        }}
        
        /* Listas */
        ul, ol {{
            margin-left: 30px;
            margin-bottom: 18px;
        }}
        
        li {{
            margin-bottom: 10px;
            line-height: 1.7;
        }}
        
        li input[type="checkbox"] {{
            margin-right: 8px;
            transform: scale(1.2);
        }}
        
        /* Blockquotes */
        blockquote {{
            border-left: 5px solid #2563eb;
            padding-left: 20px;
            margin-left: 0;
            color: #64748b;
            font-style: italic;
            background-color: #f8fafc;
            padding: 15px 20px;
            border-radius: 0 6px 6px 0;
        }}
        
        /* Enlaces */
        a {{
            color: #2563eb;
            text-decoration: none;
            border-bottom: 1px solid transparent;
            transition: border-color 0.2s;
        }}
        
        a:hover {{
            border-bottom-color: #2563eb;
        }}
        
        /* Emojis de estado */
        .emoji {{
            font-size: 1.2em;
            margin-right: 5px;
        }}
        
        /* Líneas horizontales */
        hr {{
            border: none;
            border-top: 2px solid #e5e7eb;
            margin: 40px 0;
        }}
        
        /* Alertas visuales */
        .alert-success {{
            background-color: #dcfce7;
            border-left: 4px solid #22c55e;
            padding: 15px;
            margin: 15px 0;
        }}
        
        .alert-warning {{
            background-color: #fef3c7;
            border-left: 4px solid #f59e0b;
            padding: 15px;
            margin: 15px 0;
        }}
        
        .alert-danger {{
            background-color: #fee2e2;
            border-left: 4px solid #ef4444;
            padding: 15px;
            margin: 15px 0;
        }}
    </style>
    <script>
        function printDocument() {{
            window.print();
        }}
        
        // Mostrar indicador de carga
        window.addEventListener('load', function() {{
            console.log('📄 Documento listo para imprimir');
        }});
    </script>
</head>
<body>
    <div class="print-instructions">
        <h2>📄 Documento Listo para Generar PDF</h2>
        <p>Para generar el PDF desde este HTML:</p>
        <ol style="text-align: left; display: inline-block;">
            <li>Haz clic en el botón "Imprimir a PDF" debajo</li>
            <li>O presiona <strong>Ctrl+P</strong> (Windows) o <strong>Cmd+P</strong> (Mac)</li>
            <li>En destino, selecciona <strong>"Guardar como PDF"</strong></li>
            <li>Ajusta márgenes a <strong>"Predeterminado"</strong></li>
            <li>Habilita <strong>"Gráficos de fondo"</strong> para mantener colores</li>
            <li>Haz clic en <strong>"Guardar"</strong></li>
        </ol>
        <br>
        <button class="print-btn" onclick="printDocument()">🖨️ Imprimir a PDF</button>
    </div>
    
    <div class="content-wrapper">
        {html_body}
    </div>
    
    <div class="print-instructions" style="margin-top: 40px;">
        <p><strong>Tip:</strong> El diseño está optimizado para páginas A4. Los saltos de página se aplicarán automáticamente en cada sección principal.</p>
    </div>
</body>
</html>
    """
    
    # Guardar HTML
    output_path = md_path.with_suffix('.html')
    print(f"🔄 Generando HTML: {output_path.name}...")
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_template)
        
        print(f"✅ HTML generado exitosamente: {output_path}")
        print(f"📄 Tamaño: {output_path.stat().st_size / 1024:.1f} KB")
        
        # Abrir en navegador
        print(f"\n🌐 Abriendo en navegador...")
        webbrowser.open(f'file:///{output_path.absolute()}')
        
        print("\n" + "="*60)
        print("📋 INSTRUCCIONES:")
        print("="*60)
        print("1. El documento se abrirá en tu navegador predeterminado")
        print("2. Presiona Ctrl+P (o Cmd+P en Mac) para imprimir")
        print("3. Selecciona 'Guardar como PDF' como destino")
        print("4. Habilita 'Gráficos de fondo' para mantener colores de tablas")
        print("5. Haz clic en 'Guardar'")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Error generando HTML: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Uso: python convert-md-to-printable-html.py <archivo.md>")
        sys.exit(1)
    
    convert_md_to_html(sys.argv[1])
