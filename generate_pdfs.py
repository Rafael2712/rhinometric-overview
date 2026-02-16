#!/usr/bin/env python3
"""
Generador de PDFs de Documentación Rhinometric
Convierte los informes Markdown a PDF profesionales
"""

import markdown
from markdown_pdf import MarkdownPdf, Section
import os
from datetime import datetime

def generate_technical_report():
    """Generar Informe Técnico en PDF"""
    print("📄 Generando Informe Técnico...")
    
    pdf = MarkdownPdf()
    pdf.add_section(Section("INFORME_TECNICO_RHINOMETRIC_PLATFORM.md"))
    pdf.save("INFORME_TECNICO_RHINOMETRIC_2025.pdf")
    
    print("✅ Informe Técnico generado: INFORME_TECNICO_RHINOMETRIC_2025.pdf")

def generate_executive_report():
    """Generar Informe Ejecutivo en PDF"""
    print("📊 Generando Informe Ejecutivo...")
    
    pdf = MarkdownPdf()
    pdf.add_section(Section("INFORME_EJECUTIVO_RHINOMETRIC.md"))
    pdf.save("INFORME_EJECUTIVO_RHINOMETRIC_2025.pdf")
    
    print("✅ Informe Ejecutivo generado: INFORME_EJECUTIVO_RHINOMETRIC_2025.pdf")

def generate_development_roadmap():
    """Generar Roadmap de Desarrollo en PDF"""
    print("🗺️  Generando Roadmap de Desarrollo...")
    
    pdf = MarkdownPdf()
    pdf.add_section(Section("PENDIENTES_DESARROLLO_RHINOMETRIC.md"))
    pdf.save("ROADMAP_DESARROLLO_RHINOMETRIC_2025.pdf")
    
    print("✅ Roadmap generado: ROADMAP_DESARROLLO_RHINOMETRIC_2025.pdf")

def main():
    """Generar todos los PDFs"""
    print("\n" + "="*60)
    print("🚀 GENERADOR DE DOCUMENTACIÓN RHINOMETRIC")
    print("="*60 + "\n")
    
    start_time = datetime.now()
    
    try:
        generate_technical_report()
        generate_executive_report()
        generate_development_roadmap()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print("\n" + "="*60)
        print(f"✨ COMPLETADO en {duration:.2f} segundos")
        print("="*60)
        print("\n📦 Archivos generados:")
        print("   1. INFORME_TECNICO_RHINOMETRIC_2025.pdf")
        print("   2. INFORME_EJECUTIVO_RHINOMETRIC_2025.pdf")
        print("   3. ROADMAP_DESARROLLO_RHINOMETRIC_2025.pdf")
        print("\n💡 Estos archivos están listos para compartir con clientes y equipo.\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print("\nIntentando método alternativo...\n")
        
        # Método alternativo usando weasyprint si markdown_pdf falla
        try:
            import subprocess
            
            files = [
                ("INFORME_TECNICO_RHINOMETRIC_PLATFORM.md", "INFORME_TECNICO_RHINOMETRIC_2025.pdf"),
                ("INFORME_EJECUTIVO_RHINOMETRIC.md", "INFORME_EJECUTIVO_RHINOMETRIC_2025.pdf"),
                ("PENDIENTES_DESARROLLO_RHINOMETRIC.md", "ROADMAP_DESARROLLO_RHINOMETRIC_2025.pdf")
            ]
            
            for md_file, pdf_file in files:
                # Convertir MD a HTML primero
                with open(md_file, 'r', encoding='utf-8') as f:
                    md_content = f.read()
                
                html_content = markdown.markdown(
                    md_content, 
                    extensions=['tables', 'fenced_code', 'codehilite']
                )
                
                # Agregar CSS para mejor presentación
                html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: Arial, Helvetica, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 40px auto;
            padding: 20px;
            color: #333;
        }}
        h1 {{ color: #667eea; border-bottom: 3px solid #667eea; padding-bottom: 10px; }}
        h2 {{ color: #764ba2; margin-top: 30px; }}
        h3 {{ color: #555; }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #667eea;
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        code {{
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }}
        pre {{
            background-color: #f4f4f4;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        blockquote {{
            border-left: 4px solid #667eea;
            padding-left: 20px;
            margin: 20px 0;
            color: #666;
            font-style: italic;
        }}
        .footer {{
            margin-top: 50px;
            padding-top: 20px;
            border-top: 2px solid #ddd;
            text-align: center;
            color: #888;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    {html_content}
    <div class="footer">
        <p>Rhinometric Platform - Documentación Oficial</p>
        <p>Generado el {datetime.now().strftime("%d de %B, %Y")}</p>
    </div>
</body>
</html>
"""
                
                # Guardar HTML temporal
                html_file = md_file.replace('.md', '_temp.html')
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(html_template)
                
                print(f"✅ Generado HTML: {html_file}")
                print(f"   Para convertir a PDF, usa:")
                print(f"   - Abrir {html_file} en Chrome/Edge")
                print(f"   - Ctrl+P → Guardar como PDF → {pdf_file}")
                print(f"   O instalar wkhtmltopdf: https://wkhtmltopdf.org/downloads.html\n")
            
            print("\n💡 Los archivos HTML están listos. Conviértelos a PDF usando tu navegador.")
            
        except Exception as e2:
            print(f"❌ Error en método alternativo: {str(e2)}")

if __name__ == "__main__":
    main()
