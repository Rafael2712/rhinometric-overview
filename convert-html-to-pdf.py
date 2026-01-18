#!/usr/bin/env python3
"""Convierte HTML a PDF usando weasyprint"""

import sys
import subprocess
from pathlib import Path

def install_weasyprint():
    """Instala weasyprint si no está disponible"""
    try:
        import weasyprint
        return True
    except ImportError:
        print("📦 Instalando weasyprint...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "weasyprint"])
            return True
        except Exception as e:
            print(f"❌ Error instalando weasyprint: {e}")
            return False

def convert_html_to_pdf(html_file, pdf_file):
    """Convierte HTML a PDF"""
    from weasyprint import HTML
    
    print(f"🔄 Convirtiendo {html_file.name} a PDF...")
    HTML(filename=str(html_file)).write_pdf(pdf_file)
    print(f"✅ PDF creado: {pdf_file}")

if __name__ == "__main__":
    if not install_weasyprint():
        print("❌ No se pudo instalar weasyprint")
        sys.exit(1)
    
    # Rutas
    html_path = Path("c:/Users/canel/rhinometric-overview/docs")
    pdf_path = Path("c:/Users/canel/rhinometric-overview/docs")
    
    conversions = [
        (html_path / "manual_usuario.html", pdf_path / "manual_usuario.pdf"),
        (html_path / "guia_instalacion.html", pdf_path / "guia_instalacion.pdf"),
    ]
    
    for html_file, pdf_file in conversions:
        if html_file.exists():
            try:
                convert_html_to_pdf(html_file, pdf_file)
            except Exception as e:
                print(f"❌ Error: {e}")
        else:
            print(f"❌ No encontrado: {html_file}")
    
    print("\n✅ Conversión completada")
