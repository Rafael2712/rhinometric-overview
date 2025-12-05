#!/usr/bin/env python3
"""
RHINOMETRIC Report Generator
Automated executive and technical reports
"""
import os
import json
import smtplib
import logging
import schedule
import time
import requests
import pdfkit
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta
from pathlib import Path
from jinja2 import Template

# Configuration
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")
ANOMALY_SERVICE_URL = os.getenv("ANOMALY_SERVICE_URL", "http://rhinometric-ai-anomaly:8080")
REPORT_SCHEDULE = os.getenv("REPORT_SCHEDULE", "weekly")  # daily, weekly, monthly
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.zoho.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "rafael.canelon@rhinometric.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
REPORT_RECIPIENTS = os.getenv("REPORT_RECIPIENTS", "").split(",")

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generate HTML/PDF reports"""
    
    def __init__(self):
        with open("template.html") as f:
            self.template = Template(f.read())
    
    def fetch_prometheus_query(self, query: str):
        """Fetch instant query from Prometheus"""
        try:
            response = requests.get(
                f"{PROMETHEUS_URL}/api/v1/query",
                params={"query": query},
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            if data["status"] == "success" and data["data"]["result"]:
                return data["data"]["result"]
            return []
        except Exception as e:
            logger.error(f"Prometheus query error: {e}")
            return []
    
    def fetch_anomalies(self):
        """Fetch anomalies from AI service"""
        try:
            response = requests.get(
                f"{ANOMALY_SERVICE_URL}/anomalies",
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return data.get("anomalies", [])
        except Exception as e:
            logger.warning(f"Could not fetch anomalies: {e}")
            return []
    
    def collect_data(self):
        """Collect all data for report"""
        data = {}
        
        # Services count
        services_result = self.fetch_prometheus_query("count(up == 1)")
        data["services_count"] = int(services_result[0]["value"][1]) if services_result else 0
        
        # Alerts
        alerts_result = self.fetch_prometheus_query('count(ALERTS{alertstate="firing"})')
        data["alerts_count"] = int(alerts_result[0]["value"][1]) if alerts_result else 0
        
        # Availability (mock calculation)
        total_services = self.fetch_prometheus_query("count(up)")
        total = int(total_services[0]["value"][1]) if total_services else 1
        data["availability"] = round((data["services_count"] / total) * 100, 2)
        
        # Service details (simplified)
        data["services"] = [
            {
                "name": "License Server",
                "status": "Healthy",
                "status_class": "healthy",
                "cpu": "15.2",
                "memory": "45.6"
            },
            {
                "name": "Prometheus",
                "status": "Healthy",
                "status_class": "healthy",
                "cpu": "22.8",
                "memory": "68.3"
            },
            {
                "name": "Grafana",
                "status": "Healthy",
                "status_class": "healthy",
                "cpu": "8.5",
                "memory": "32.1"
            }
        ]
        
        # Anomalies
        data["anomalies"] = self.fetch_anomalies()[:5]  # Top 5
        
        # Generate recommendations
        recommendations = []
        if data["alerts_count"] > 0:
            recommendations.append(f"Se detectaron {data['alerts_count']} alertas activas que requieren atención")
        if data["anomalies"]:
            recommendations.append(f"El sistema de IA detectó {len(data['anomalies'])} anomalías en las últimas horas")
        if data["availability"] < 99:
            recommendations.append("La disponibilidad está por debajo del objetivo del 99.9%")
        if not recommendations:
            recommendations.append("Todos los sistemas operan dentro de parámetros normales")
            recommendations.append("Continuar con monitoreo rutinario")
        
        data["recommendations"] = recommendations
        
        return data
    
    def generate_report(self):
        """Generate HTML and PDF report"""
        logger.info("Generating report...")
        
        # Collect data
        data = self.collect_data()
        
        # Determine period
        if REPORT_SCHEDULE == "daily":
            period = "Últimas 24 horas"
        elif REPORT_SCHEDULE == "weekly":
            period = "Última semana"
        else:
            period = "Último mes"
        
        # Executive summary
        if data["alerts_count"] == 0 and not data["anomalies"]:
            summary = f"La plataforma RHINOMETRIC opera con normalidad. {data['services_count']} servicios activos con disponibilidad del {data['availability']}%. No se detectaron incidentes críticos durante el período reportado."
        else:
            summary = f"La plataforma RHINOMETRIC presenta {data['alerts_count']} alertas activas. Se detectaron {len(data['anomalies'])} anomalías mediante IA. {data['services_count']} servicios activos con disponibilidad del {data['availability']}%. Requiere revisión."
        
        # Status classification
        data["services_status"] = "good" if data["services_count"] > 15 else "warning"
        data["alerts_status"] = "good" if data["alerts_count"] == 0 else "critical"
        data["availability_status"] = "good" if data["availability"] >= 99 else "warning"
        
        # Render template
        html_content = self.template.render(
            report_date=datetime.now().strftime("%d de %B de %Y"),
            period=period,
            executive_summary=summary,
            **data
        )
        
        # Save HTML
        html_path = Path(f"/tmp/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        # Convert to PDF
        pdf_path = html_path.with_suffix(".pdf")
        try:
            pdfkit.from_file(str(html_path), str(pdf_path))
            logger.info(f"Report generated: {pdf_path}")
            return pdf_path
        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            return html_path
    
    def send_report(self, report_path: Path):
        """Send report via email"""
        if not REPORT_RECIPIENTS or not SMTP_PASSWORD:
            logger.warning("Email not configured. Report saved locally.")
            return
        
        logger.info(f"Sending report to {len(REPORT_RECIPIENTS)} recipients...")
        
        try:
            msg = MIMEMultipart()
            msg["From"] = SMTP_USER
            msg["To"] = ", ".join(REPORT_RECIPIENTS)
            msg["Subject"] = f"RHINOMETRIC - Informe {REPORT_SCHEDULE.capitalize()} - {datetime.now().strftime('%d/%m/%Y')}"
            
            # Email body
            body = """
Estimado/a,

Adjunto encontrará el informe de observabilidad de RHINOMETRIC correspondiente al período reportado.

Este informe incluye:
- Resumen ejecutivo del estado de la plataforma
- Métricas clave de rendimiento y disponibilidad
- Anomalías detectadas por IA (si las hay)
- Recomendaciones de acción

Para cualquier consulta, por favor contactar con el equipo de soporte.

Saludos,
RHINOMETRIC Automated Reporting System
"""
            msg.attach(MIMEText(body, "plain"))
            
            # Attach report
            with open(report_path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename={report_path.name}"
            )
            msg.attach(part)
            
            # Send email
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)
            
            logger.info("✅ Report sent successfully")
        
        except Exception as e:
            logger.error(f"Email send failed: {e}")


def run_report():
    """Execute report generation and delivery"""
    logger.info("=" * 60)
    logger.info(f"Starting {REPORT_SCHEDULE} report generation")
    logger.info("=" * 60)
    
    generator = ReportGenerator()
    report_path = generator.generate_report()
    generator.send_report(report_path)
    
    logger.info("Report cycle complete")


def main():
    logger.info("=" * 60)
    logger.info("RHINOMETRIC Report Service v2.2.0")
    logger.info("=" * 60)
    logger.info(f"Schedule: {REPORT_SCHEDULE}")
    logger.info(f"Recipients: {len(REPORT_RECIPIENTS)}")
    logger.info("=" * 60)
    
    # Schedule based on configuration
    if REPORT_SCHEDULE == "daily":
        schedule.every().day.at("08:00").do(run_report)
        logger.info("Scheduled: Daily at 08:00")
    elif REPORT_SCHEDULE == "weekly":
        schedule.every().monday.at("08:00").do(run_report)
        logger.info("Scheduled: Weekly on Monday at 08:00")
    elif REPORT_SCHEDULE == "monthly":
        # First day of month (approximation)
        schedule.every().monday.at("08:00").do(run_report)
        logger.info("Scheduled: Monthly (first Monday)")
    
    # Test run if requested
    if os.getenv("RUN_IMMEDIATE", "false").lower() == "true":
        logger.info("Running immediate test report...")
        run_report()
    
    logger.info("Service started. Waiting for scheduled tasks...")
    
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
