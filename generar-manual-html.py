#!/usr/bin/env python3
"""Convierte Manual de Usuario Markdown a HTML con botón de descarga PDF"""

import markdown
import sys
from pathlib import Path

# Leer contenido Markdown
md_file = Path("c:/Users/canel/rhinometric-overview/docs/manual_usuario.md")
with open(md_file, 'r', encoding='utf-8') as f:
    md_content = f.read()

# Convertir Markdown a HTML
html_body = markdown.markdown(
    md_content,
    extensions=['tables', 'fenced_code', 'nl2br']
)

# Template HTML con botón de descarga PDF (estilo Rhinometric)
html_template = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Manual de Usuario - Rhinometric v2.1.0</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        @page {{
            size: A4;
            margin: 2cm;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #2d3748;
            background: #f7fafc;
        }}
        
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .header p {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        
        .download-btn {{
            display: inline-block;
            background: white;
            color: #667eea;
            padding: 15px 30px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: bold;
            margin-top: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
            transition: transform 0.2s;
        }}
        
        .download-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.3);
        }}
        
        .content {{
            padding: 40px;
        }}
        
        h1, h2, h3, h4 {{
            color: #2d3748;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
        }}
        
        h2 {{
            font-size: 2em;
            border-bottom: 2px solid #667eea;
            padding-bottom: 0.3em;
            color: #667eea;
        }}
        
        h3 {{
            font-size: 1.5em;
            color: #764ba2;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 1.5em 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        th, td {{
            padding: 12px;
            text-align: left;
            border: 1px solid #e2e8f0;
        }}
        
        th {{
            background: #667eea;
            color: white;
            font-weight: 600;
        }}
        
        tr:nth-child(even) {{
            background: #f7fafc;
        }}
        
        code {{
            background: #2d3748;
            color: #68d391;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }}
        
        pre {{
            background: #2d3748;
            color: #f7fafc;
            padding: 20px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 1em 0;
            border-left: 4px solid #667eea;
        }}
        
        pre code {{
            background: transparent;
            color: #f7fafc;
            padding: 0;
        }}
        
        ul, ol {{
            margin-left: 2em;
            margin-bottom: 1em;
        }}
        
        li {{
            margin-bottom: 0.5em;
        }}
        
        .footer {{
            background: #2d3748;
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .footer a {{
            color: #68d391;
            text-decoration: none;
        }}
        
        @media print {{
            body {{
                background: white;
            }}
            .header, .download-btn {{
                background: #667eea !important;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}
            .download-btn {{
                display: none;
            }}
        }}
    </style>
    <script>
        function downloadPDF() {{
            window.print();
        }}
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🦏 Manual de Usuario</h1>
            <p>Rhinometric v2.1.0 - Plataforma de Observabilidad Empresarial</p>
            <a href="#" class="download-btn" onclick="downloadPDF(); return false;">
                📥 Descargar PDF
            </a>
        </div>
        
        <div class="content">
            {html_body}
        </div>
        
        <div class="footer">
            <p><strong>© 2025 Rhinometric. Todos los derechos reservados.</strong></p>
            <p>Soporte: <a href="mailto:soporte@rhinometric.com">soporte@rhinometric.com</a></p>
            <p>Web: <a href="https://rhinometric.com">rhinometric.com</a></p>
        </div>
    </div>
</body>
</html>"""

# Guardar HTML
output_file = Path("c:/Users/canel/rhinometric-overview/docs/manual_usuario.html")
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(html_template)

print(f"✅ HTML generado: {output_file}")
print("📄 Incluye botón 'Descargar PDF' que usa window.print()")
