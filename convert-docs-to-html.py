#!/usr/bin/env python3
"""Convierte documentos Markdown a HTML con estilo profesional"""

import markdown
import sys
from pathlib import Path

def convert_md_to_html(md_file, output_file, title):
    """Convierte un archivo Markdown a HTML con estilo"""
    
    # Leer contenido Markdown
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Convertir Markdown a HTML
    html_content = markdown.markdown(
        md_content,
        extensions=['tables', 'fenced_code', 'codehilite', 'toc', 'nl2br']
    )
    
    # Template HTML profesional
    html_template = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Rhinometric v2.1.0</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
        }}
        
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        
        h1, h2, h3, h4 {{
            color: #667eea;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
        }}
        
        h1 {{
            font-size: 2.5em;
            border-bottom: 3px solid #667eea;
            padding-bottom: 0.3em;
            margin-top: 0;
        }}
        
        h2 {{
            font-size: 2em;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 0.3em;
        }}
        
        h3 {{
            font-size: 1.5em;
            color: #764ba2;
        }}
        
        h4 {{
            font-size: 1.2em;
        }}
        
        p {{
            margin-bottom: 1em;
        }}
        
        ul, ol {{
            margin-left: 2em;
            margin-bottom: 1em;
        }}
        
        li {{
            margin-bottom: 0.5em;
        }}
        
        code {{
            background: #f7fafc;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            color: #e53e3e;
            font-size: 0.9em;
        }}
        
        pre {{
            background: #2d3748;
            color: #f7fafc;
            padding: 20px;
            border-radius: 8px;
            overflow-x: auto;
            margin-bottom: 1em;
            border-left: 4px solid #667eea;
        }}
        
        pre code {{
            background: transparent;
            color: #f7fafc;
            padding: 0;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 1.5em;
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
        
        blockquote {{
            border-left: 4px solid #667eea;
            padding-left: 20px;
            margin: 1em 0;
            color: #666;
            font-style: italic;
            background: #f7fafc;
            padding: 15px 20px;
            border-radius: 4px;
        }}
        
        a {{
            color: #667eea;
            text-decoration: none;
            border-bottom: 2px solid transparent;
            transition: border-color 0.3s;
        }}
        
        a:hover {{
            border-bottom-color: #667eea;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            margin: -40px -40px 40px -40px;
            border-radius: 12px 12px 0 0;
            text-align: center;
        }}
        
        .header h1 {{
            color: white;
            border: none;
            margin: 0;
            font-size: 2.5em;
        }}
        
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
        }}
        
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #e2e8f0;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }}
        
        .warning {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 1em 0;
            border-radius: 4px;
        }}
        
        .info {{
            background: #d1ecf1;
            border-left: 4px solid #17a2b8;
            padding: 15px;
            margin: 1em 0;
            border-radius: 4px;
        }}
        
        .success {{
            background: #d4edda;
            border-left: 4px solid #28a745;
            padding: 15px;
            margin: 1em 0;
            border-radius: 4px;
        }}
        
        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            .container {{
                box-shadow: none;
                padding: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🦏 {title}</h1>
            <p>Rhinometric v2.1.0 - Plataforma de Observabilidad Empresarial</p>
        </div>
        
        {html_content}
        
        <div class="footer">
            <p>© 2025 Rhinometric Platform | <a href="https://rhinometric.com">rhinometric.com</a></p>
            <p>Soporte: <a href="mailto:soporte@rhinometric.com">soporte@rhinometric.com</a></p>
        </div>
    </div>
</body>
</html>"""
    
    # Guardar HTML
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    print(f"✅ Convertido: {md_file} → {output_file}")

if __name__ == "__main__":
    # Instalar markdown si no está
    try:
        import markdown
    except ImportError:
        print("Instalando markdown...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "markdown"])
        import markdown
    
    # Convertir los 3 documentos
    base_path = Path("rhinometric-trial-v2.1.0-universal/docs")
    output_path = Path("c:/Users/canel/rhinometric-overview/docs")
    
    conversions = [
        (base_path / "manual_usuario.md", output_path / "manual_usuario.html", "Manual de Usuario"),
        (base_path / "guia_instalacion.md", output_path / "guia_instalacion.html", "Guía de Instalación"),
    ]
    
    for md_file, html_file, title in conversions:
        if md_file.exists():
            convert_md_to_html(md_file, html_file, title)
        else:
            print(f"❌ No encontrado: {md_file}")
    
    print("\n✅ Conversión completada")
