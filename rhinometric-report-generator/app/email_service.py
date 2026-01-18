"""
Email Delivery Service
Sends reports via SMTP with attachments and HTML templates
"""
import os
import logging
from typing import List, Optional
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import aiosmtplib
from jinja2 import Environment, FileSystemLoader
from app.config import config_manager

logger = logging.getLogger(__name__)


class EmailService:
    """Email delivery service with SMTP support"""
    
    def __init__(self, templates_dir: str = "/app/templates"):
        self.config = config_manager.config.smtp
        self.templates_dir = templates_dir
        
        # Setup Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(templates_dir),
            autoescape=True
        )
    
    async def send_report_email(
        self,
        recipients: List[str],
        report_name: str,
        report_data: dict,
        pdf_path: Optional[str] = None,
        html_path: Optional[str] = None
    ) -> bool:
        """Send report via email with attachments"""
        
        if not self.config.enabled:
            logger.info("Email service disabled, skipping send")
            return False
        
        if not recipients:
            logger.warning("No recipients specified")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.config.from_name} <{self.config.from_email}>"
            msg['To'] = ", ".join(recipients)
            msg['Subject'] = self._generate_subject(report_name, report_data)
            msg['Date'] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")
            
            # Generate email body
            html_body = self._generate_email_body(report_name, report_data)
            text_body = self._html_to_text(html_body)
            
            # Attach bodies
            msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
            msg.attach(MIMEText(html_body, 'html', 'utf-8'))
            
            # Attach PDF report
            if pdf_path and os.path.exists(pdf_path):
                with open(pdf_path, 'rb') as f:
                    pdf_attachment = MIMEApplication(f.read(), _subtype='pdf')
                    pdf_attachment.add_header(
                        'Content-Disposition',
                        'attachment',
                        filename=os.path.basename(pdf_path)
                    )
                    msg.attach(pdf_attachment)
                logger.info(f"Attached PDF: {pdf_path}")
            
            # Attach HTML report
            if html_path and os.path.exists(html_path):
                with open(html_path, 'rb') as f:
                    html_attachment = MIMEApplication(f.read(), _subtype='html')
                    html_attachment.add_header(
                        'Content-Disposition',
                        'attachment',
                        filename=os.path.basename(html_path)
                    )
                    msg.attach(html_attachment)
                logger.info(f"Attached HTML: {html_path}")
            
            # Send email
            await self._send_smtp(msg, recipients)
            
            logger.info(f"Report email sent successfully to {len(recipients)} recipient(s)")
            return True
        
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
    
    async def _send_smtp(self, msg: MIMEMultipart, recipients: List[str]):
        """Send email via SMTP"""
        smtp_config = {
            'hostname': self.config.host,
            'port': self.config.port,
            'use_tls': self.config.use_tls,
            'timeout': 30
        }
        
        # Add authentication if configured
        if self.config.username and self.config.password:
            smtp_config['username'] = self.config.username
            smtp_config['password'] = self.config.password
        
        async with aiosmtplib.SMTP(**smtp_config) as smtp:
            await smtp.send_message(msg)
    
    def _generate_subject(self, report_name: str, report_data: dict) -> str:
        """Generate email subject line"""
        status = report_data.get("summary", {}).get("status", "unknown")
        health_score = report_data.get("summary", {}).get("health_score", 100)
        
        status_emoji = {
            "healthy": "✅",
            "warning": "⚠️",
            "critical": "🚨"
        }.get(status, "📊")
        
        timestamp = datetime.now().strftime("%Y-%m-%d")
        
        return f"{status_emoji} RhinoMetric {report_name.title()} Report - {timestamp} (Health: {health_score:.0f}/100)"
    
    def _generate_email_body(self, report_name: str, report_data: dict) -> str:
        """Generate HTML email body from template"""
        try:
            template = self.jinja_env.get_template('email_report.html')
            
            return template.render(
                report_name=report_name,
                data=report_data,
                generated_at=datetime.fromisoformat(report_data["generated_at"]),
                current_year=datetime.now().year
            )
        
        except Exception as e:
            logger.error(f"Error rendering email template: {e}")
            return self._generate_fallback_email_body(report_name, report_data)
    
    def _generate_fallback_email_body(self, report_name: str, report_data: dict) -> str:
        """Generate simple fallback email body"""
        summary = report_data.get("summary", {})
        
        status = summary.get("status", "unknown").upper()
        health_score = summary.get("health_score", 100)
        anomalies = summary.get("total_anomalies", 0)
        alerts = summary.get("active_alerts", 0)
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #1a73e8 0%, #34a853 100%); 
                          color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; }}
                .metric {{ background: white; padding: 15px; margin: 10px 0; border-radius: 4px; 
                         border-left: 4px solid #1a73e8; }}
                .metric-label {{ font-weight: bold; color: #5f6368; }}
                .metric-value {{ font-size: 24px; color: #1a73e8; font-weight: bold; }}
                .status-healthy {{ color: #34a853; }}
                .status-warning {{ color: #fbbc04; }}
                .status-critical {{ color: #ea4335; }}
                .footer {{ text-align: center; margin-top: 30px; color: #5f6368; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎯 RhinoMetric Report</h1>
                    <p>{report_name.title()} Report</p>
                </div>
                <div class="content">
                    <div class="metric">
                        <div class="metric-label">System Status</div>
                        <div class="metric-value status-{status.lower()}">{status}</div>
                    </div>
                    
                    <div class="metric">
                        <div class="metric-label">Health Score</div>
                        <div class="metric-value">{health_score:.0f}/100</div>
                    </div>
                    
                    <div class="metric">
                        <div class="metric-label">Anomalies Detected</div>
                        <div class="metric-value">{anomalies}</div>
                    </div>
                    
                    <div class="metric">
                        <div class="metric-label">Active Alerts</div>
                        <div class="metric-value">{alerts}</div>
                    </div>
                    
                    <p style="margin-top: 30px;">
                        <strong>📎 Reports attached:</strong><br/>
                        Detailed PDF and HTML reports are attached to this email.
                    </p>
                    
                    <p>
                        <strong>📊 Dashboard:</strong><br/>
                        <a href="http://localhost:3000/d/rhinometric-ai-anomaly">View Live Dashboard</a>
                    </p>
                </div>
                
                <div class="footer">
                    <p>RhinoMetric v2.2.0 Enterprise Edition</p>
                    <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text (simple version)"""
        import re
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html)
        
        # Clean up whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = text.strip()
        
        return text


# Global email service instance
email_service = EmailService()
