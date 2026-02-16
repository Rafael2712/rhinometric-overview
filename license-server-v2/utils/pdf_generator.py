#!/usr/bin/env python3
"""
PDF Generator for Rhinometric Documentation
Converts text documentation to professional PDF files
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.pdfgen import canvas
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def generate_pdf_from_text(text_file: Path, output_pdf: Path, title: str = "Rhinometric Documentation"):
    """
    Generate a professional PDF from a text file
    
    Args:
        text_file: Path to input .txt file
        output_pdf: Path for output .pdf file
        title: Document title
    """
    try:
        # Read text content
        with open(text_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Create PDF document
        doc = SimpleDocTemplate(
            str(output_pdf),
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )
        
        # Styles
        styles = getSampleStyleSheet()
        
        # Only add custom styles if they don't exist
        if 'CustomTitle' not in styles:
            styles.add(ParagraphStyle(
                name='CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor='#667eea',
                spaceAfter=30,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            ))
        if 'CustomHeading' not in styles:
            styles.add(ParagraphStyle(
                name='CustomHeading',
                parent=styles['Heading2'],
                fontSize=16,
                textColor='#2c3e50',
                spaceAfter=12,
                spaceBefore=12,
                fontName='Helvetica-Bold'
            ))
        if 'CustomBody' not in styles:
            styles.add(ParagraphStyle(
                name='CustomBody',
                parent=styles['BodyText'],
                fontSize=11,
                textColor='#333333',
                alignment=TA_JUSTIFY,
                spaceAfter=12,
                fontName='Helvetica'
            ))
        if 'CustomCode' not in styles:
            styles.add(ParagraphStyle(
                name='CustomCode',
                parent=styles['Normal'],
                fontSize=10,
                textColor='#667eea',
                backColor='#f0f3f7',
                fontName='Courier',
                leftIndent=20,
                spaceAfter=8
            ))
        
        # Build story
        story = []
        
        # Add title
        story.append(Paragraph(title, styles['CustomTitle']))
        story.append(Spacer(1, 0.3*inch))
        
        # Process content line by line
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            
            if not line:
                story.append(Spacer(1, 0.1*inch))
                continue
            
            # Detect headers (lines with ===)
            if line.startswith('═'):
                continue
            
            # Detect section titles (ALL CAPS or ending with :)
            if line.isupper() and len(line) > 3 and not line.startswith('•'):
                story.append(Paragraph(line, styles['CustomHeading']))
            # Detect code blocks (indented or with special chars)
            elif line.startswith(('  ', '\t', '   ', '$', './')) or '-' in line[:3]:
                story.append(Paragraph(line.replace('<', '&lt;').replace('>', '&gt;'), styles['CustomCode']))
            # Normal text
            else:
                # Escape HTML entities
                line_escaped = line.replace('<', '&lt;').replace('>', '&gt;')
                # Make bold text
                if ':' in line_escaped:
                    parts = line_escaped.split(':', 1)
                    if len(parts[0]) < 30:  # Likely a label
                        line_escaped = f"<b>{parts[0]}:</b>{parts[1]}"
                story.append(Paragraph(line_escaped, styles['CustomBody']))
        
        # Add footer spacer
        story.append(Spacer(1, 0.5*inch))
        
        # Footer
        footer_text = "© 2025 Rhinometric - Enterprise Observability Platform"
        story.append(Paragraph(f"<i>{footer_text}</i>", styles['CustomBody']))
        
        # Build PDF
        doc.build(story)
        
        logger.info(f"✅ PDF generated successfully: {output_pdf}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error generating PDF: {e}")
        return False


def generate_all_documentation_pdfs(docs_dir: Path):
    """
    Generate PDF versions of all .txt documentation files
    
    Args:
        docs_dir: Directory containing .txt files
    """
    txt_files = {
        'manual_usuario.txt': ('Manual de Usuario - Rhinometric v2.1.0', 'manual_usuario.pdf'),
        'guia_instalacion.txt': ('Guía de Instalación - Rhinometric v2.1.0', 'guia_instalacion.pdf')
    }
    
    success_count = 0
    for txt_filename, (title, pdf_filename) in txt_files.items():
        txt_path = docs_dir / txt_filename
        pdf_path = docs_dir / pdf_filename
        
        if txt_path.exists():
            if generate_pdf_from_text(txt_path, pdf_path, title):
                success_count += 1
        else:
            logger.warning(f"Text file not found: {txt_path}")
    
    logger.info(f"Generated {success_count}/{len(txt_files)} PDF documents")
    return success_count == len(txt_files)


if __name__ == "__main__":
    # Test generation
    import sys
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) > 1:
        docs_dir = Path(sys.argv[1])
    else:
        docs_dir = Path(__file__).parent.parent / "docs"
    
    generate_all_documentation_pdfs(docs_dir)
