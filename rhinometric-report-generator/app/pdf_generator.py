"""
PDF Report Generator
Professional PDF generation using ReportLab with charts and tables
"""
import os
import io
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white, black
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image as RLImage, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

logger = logging.getLogger(__name__)


class PDFGenerator:
    """Professional PDF report generator"""
    
    # Brand colors
    PRIMARY_COLOR = HexColor('#1a73e8')
    SECONDARY_COLOR = HexColor('#34a853')
    WARNING_COLOR = HexColor('#fbbc04')
    DANGER_COLOR = HexColor('#ea4335')
    GRAY_COLOR = HexColor('#5f6368')
    
    def __init__(self, output_dir: str = "/app/reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=self.PRIMARY_COLOR,
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=self.GRAY_COLOR,
            spaceAfter=20,
            alignment=TA_CENTER
        ))
        
        # Section header
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=self.PRIMARY_COLOR,
            spaceAfter=12,
            spaceBefore=20
        ))
        
        # Status badge styles
        for status, color in [
            ('healthy', self.SECONDARY_COLOR),
            ('warning', self.WARNING_COLOR),
            ('critical', self.DANGER_COLOR)
        ]:
            self.styles.add(ParagraphStyle(
                name=f'Status_{status}',
                parent=self.styles['Normal'],
                fontSize=12,
                textColor=white,
                backColor=color,
                alignment=TA_CENTER,
                borderPadding=5
            ))
    
    def generate_report(
        self,
        data: Dict[str, Any],
        report_name: str = "report"
    ) -> str:
        """Generate PDF report from aggregated data"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{report_name}_{timestamp}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        logger.info(f"Generating PDF report: {filename}")
        
        # Create PDF document
        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=1*inch,
            bottomMargin=0.75*inch
        )
        
        # Build content
        story = []
        
        # Cover page
        story.extend(self._build_cover_page(data))
        story.append(PageBreak())
        
        # Executive summary
        story.extend(self._build_executive_summary(data))
        story.append(PageBreak())
        
        # System metrics
        story.extend(self._build_system_metrics_section(data))
        story.append(PageBreak())
        
        # Application metrics
        story.extend(self._build_application_metrics_section(data))
        
        # Anomalies section
        if data.get("anomalies", {}).get("count", 0) > 0:
            story.append(PageBreak())
            story.extend(self._build_anomalies_section(data))
        
        # Alerts section
        if data.get("alerts", {}).get("count", 0) > 0:
            story.append(PageBreak())
            story.extend(self._build_alerts_section(data))
        
        # Build PDF
        doc.build(story, onFirstPage=self._add_header_footer, onLaterPages=self._add_header_footer)
        
        logger.info(f"PDF report generated: {filepath}")
        return filepath
    
    def _build_cover_page(self, data: Dict[str, Any]) -> list:
        """Build cover page"""
        story = []
        
        # Logo placeholder
        story.append(Spacer(1, 2*inch))
        
        # Title
        title = Paragraph("RhinoMetric Report", self.styles['CustomTitle'])
        story.append(title)
        story.append(Spacer(1, 0.3*inch))
        
        # Subtitle
        report_type = data.get("report_type", "executive").title()
        subtitle = Paragraph(f"{report_type} Report", self.styles['CustomSubtitle'])
        story.append(subtitle)
        story.append(Spacer(1, 0.5*inch))
        
        # Report period
        generated_at = datetime.fromisoformat(data["generated_at"])
        period_text = f"""
        <para alignment="center">
        <b>Report Period:</b> Last {data['period_hours']} hours<br/>
        <b>Generated:</b> {generated_at.strftime('%Y-%m-%d %H:%M:%S')}
        </para>
        """
        story.append(Paragraph(period_text, self.styles['Normal']))
        story.append(Spacer(1, 1*inch))
        
        # Status indicator
        status = data.get("summary", {}).get("status", "healthy")
        health_score = data.get("summary", {}).get("health_score", 100)
        
        status_text = f"""
        <para alignment="center">
        <b style="font-size:18">System Status:</b><br/><br/>
        <span style="font-size:24; color:#{'34a853' if status == 'healthy' else 'fbbc04' if status == 'warning' else 'ea4335'}">
        {status.upper()}
        </span><br/><br/>
        <b>Health Score:</b> {health_score:.1f}/100
        </para>
        """
        story.append(Paragraph(status_text, self.styles['Normal']))
        
        return story
    
    def _build_executive_summary(self, data: Dict[str, Any]) -> list:
        """Build executive summary section"""
        story = []
        
        story.append(Paragraph("Executive Summary", self.styles['CustomTitle']))
        story.append(Spacer(1, 0.3*inch))
        
        summary = data.get("summary", {})
        
        # Key metrics table
        metrics_data = [
            ["Metric", "Value"],
            ["Health Score", f"{summary.get('health_score', 0):.1f}/100"],
            ["System Status", summary.get("status", "unknown").upper()],
            ["Total Anomalies", str(summary.get("total_anomalies", 0))],
            ["Active Alerts", str(summary.get("active_alerts", 0))],
            ["Avg CPU Usage", f"{summary.get('cpu_avg', 0):.1f}%"],
            ["Avg Memory Usage", f"{summary.get('memory_avg', 0):.1f}%"],
            ["Error Rate", f"{summary.get('error_rate', 0)*100:.2f}%"]
        ]
        
        table = Table(metrics_data, colWidths=[3*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.PRIMARY_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), HexColor('#f8f9fa')),
            ('GRID', (0, 0), (-1, -1), 1, self.GRAY_COLOR),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#f8f9fa')])
        ]))
        
        story.append(table)
        story.append(Spacer(1, 0.5*inch))
        
        # Insights
        insights = self._generate_insights(data)
        if insights:
            story.append(Paragraph("Key Insights", self.styles['SectionHeader']))
            for insight in insights:
                bullet = Paragraph(f"• {insight}", self.styles['Normal'])
                story.append(bullet)
                story.append(Spacer(1, 0.1*inch))
        
        return story
    
    def _build_system_metrics_section(self, data: Dict[str, Any]) -> list:
        """Build system metrics section"""
        story = []
        
        story.append(Paragraph("System Metrics", self.styles['CustomTitle']))
        story.append(Spacer(1, 0.3*inch))
        
        sys_metrics = data.get("system_metrics", {})
        
        # CPU, Memory, Disk table
        metrics_data = [
            ["Resource", "Current", "Average", "Min", "Max"]
        ]
        
        for metric_name, display_name in [
            ("cpu", "CPU Usage (%)"),
            ("memory", "Memory Usage (%)"),
            ("disk", "Disk Usage (%)")
        ]:
            metric = sys_metrics.get(metric_name, {})
            metrics_data.append([
                display_name,
                f"{metric.get('current', 0):.1f}",
                f"{metric.get('avg', 0):.1f}",
                f"{metric.get('min', 0):.1f}",
                f"{metric.get('max', 0):.1f}"
            ])
        
        table = Table(metrics_data, colWidths=[2*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.PRIMARY_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, self.GRAY_COLOR),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#f8f9fa')])
        ]))
        
        story.append(table)
        story.append(Spacer(1, 0.5*inch))
        
        # Network metrics
        network = sys_metrics.get("network", {})
        if network:
            story.append(Paragraph("Network Traffic", self.styles['SectionHeader']))
            
            net_data = [
                ["Direction", "Current (MB/s)", "Average (MB/s)", "Max (MB/s)"]
            ]
            
            for direction in ["receive", "transmit"]:
                net_metric = network.get(direction, {})
                net_data.append([
                    direction.title(),
                    f"{net_metric.get('current', 0)/1024/1024:.2f}",
                    f"{net_metric.get('avg', 0)/1024/1024:.2f}",
                    f"{net_metric.get('max', 0)/1024/1024:.2f}"
                ])
            
            net_table = Table(net_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
            net_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.SECONDARY_COLOR),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, self.GRAY_COLOR)
            ]))
            
            story.append(net_table)
        
        return story
    
    def _build_application_metrics_section(self, data: Dict[str, Any]) -> list:
        """Build application metrics section"""
        story = []
        
        story.append(Paragraph("Application Metrics", self.styles['CustomTitle']))
        story.append(Spacer(1, 0.3*inch))
        
        app_metrics = data.get("application_metrics", {})
        
        metrics_data = [
            ["Metric", "Current", "Average", "Max"]
        ]
        
        for metric_name, display_name, unit in [
            ("http_request_rate", "HTTP Request Rate", "req/s"),
            ("http_error_rate", "HTTP Error Rate", "%"),
            ("api_latency_p95", "API Latency (P95)", "ms"),
            ("db_connections", "DB Connections", "conn")
        ]:
            metric = app_metrics.get(metric_name, {})
            current = metric.get('current', 0)
            avg = metric.get('avg', 0)
            max_val = metric.get('max', 0)
            
            if metric_name == "http_error_rate":
                current *= 100
                avg *= 100
                max_val *= 100
            elif metric_name == "api_latency_p95":
                current *= 1000
                avg *= 1000
                max_val *= 1000
            
            metrics_data.append([
                display_name,
                f"{current:.2f} {unit}",
                f"{avg:.2f} {unit}",
                f"{max_val:.2f} {unit}"
            ])
        
        table = Table(metrics_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.PRIMARY_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, self.GRAY_COLOR),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#f8f9fa')])
        ]))
        
        story.append(table)
        
        return story
    
    def _build_anomalies_section(self, data: Dict[str, Any]) -> list:
        """Build anomalies section"""
        story = []
        
        anomalies_info = data.get("anomalies", {})
        anomalies_list = anomalies_info.get("anomalies", [])
        
        story.append(Paragraph("Detected Anomalies", self.styles['CustomTitle']))
        story.append(Spacer(1, 0.3*inch))
        
        # Statistics summary
        stats = anomalies_info.get("statistics", {})
        if stats:
            stats_text = f"""
            <b>Total Anomalies:</b> {anomalies_info.get('count', 0)}<br/>
            <b>Detection Rate:</b> {stats.get('detection_rate', 0):.1f}%<br/>
            <b>Models Trained:</b> {stats.get('models_trained', 0)}
            """
            story.append(Paragraph(stats_text, self.styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
        
        # Anomalies table
        if anomalies_list:
            anomaly_data = [["Metric", "Timestamp", "Severity", "Confidence"]]
            
            for anomaly in anomalies_list[:20]:  # Limit to 20
                anomaly_data.append([
                    anomaly.get("metric_name", "Unknown"),
                    anomaly.get("timestamp", "")[:19],
                    anomaly.get("severity", "medium").upper(),
                    f"{anomaly.get('confidence', 0):.2f}"
                ])
            
            table = Table(anomaly_data, colWidths=[2*inch, 2*inch, 1*inch, 1*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.DANGER_COLOR),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, self.GRAY_COLOR),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#f8f9fa')])
            ]))
            
            story.append(table)
        
        return story
    
    def _build_alerts_section(self, data: Dict[str, Any]) -> list:
        """Build alerts section"""
        story = []
        
        alerts_info = data.get("alerts", {})
        alerts_list = alerts_info.get("alerts", [])
        
        story.append(Paragraph("Active Alerts", self.styles['CustomTitle']))
        story.append(Spacer(1, 0.3*inch))
        
        summary_text = f"""
        <b>Total Alerts:</b> {alerts_info.get('count', 0)}<br/>
        <b>Active Alerts:</b> {alerts_info.get('active', 0)}
        """
        story.append(Paragraph(summary_text, self.styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        if alerts_list:
            alert_data = [["Alert Name", "Severity", "Status", "Started At"]]
            
            for alert in alerts_list[:15]:  # Limit to 15
                labels = alert.get("labels", {})
                status = alert.get("status", {})
                
                alert_data.append([
                    labels.get("alertname", "Unknown"),
                    labels.get("severity", "warning").upper(),
                    status.get("state", "unknown").upper(),
                    alert.get("startsAt", "")[:19]
                ])
            
            table = Table(alert_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 2*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.WARNING_COLOR),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, self.GRAY_COLOR),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#f8f9fa')])
            ]))
            
            story.append(table)
        
        return story
    
    def _generate_insights(self, data: Dict[str, Any]) -> list:
        """Generate actionable insights"""
        insights = []
        
        summary = data.get("summary", {})
        sys_metrics = data.get("system_metrics", {})
        app_metrics = data.get("application_metrics", {})
        
        # CPU insights
        cpu_avg = summary.get("cpu_avg", 0)
        if cpu_avg > 80:
            insights.append(f"CPU usage is critically high ({cpu_avg:.1f}%). Consider scaling horizontally.")
        elif cpu_avg > 60:
            insights.append(f"CPU usage is elevated ({cpu_avg:.1f}%). Monitor for potential bottlenecks.")
        
        # Memory insights
        mem_avg = summary.get("memory_avg", 0)
        if mem_avg > 90:
            insights.append(f"Memory usage is critically high ({mem_avg:.1f}%). Risk of OOM errors.")
        elif mem_avg > 70:
            insights.append(f"Memory usage is elevated ({mem_avg:.1f}%). Consider memory optimization.")
        
        # Error rate insights
        error_rate = summary.get("error_rate", 0)
        if error_rate > 0.05:
            insights.append(f"Error rate is high ({error_rate*100:.2f}%). Investigate failed requests immediately.")
        elif error_rate > 0.01:
            insights.append(f"Error rate is elevated ({error_rate*100:.2f}%). Review error logs.")
        
        # Anomaly insights
        anomaly_count = summary.get("total_anomalies", 0)
        if anomaly_count > 10:
            insights.append(f"{anomaly_count} anomalies detected. Review AI detection results for patterns.")
        elif anomaly_count > 0:
            insights.append(f"{anomaly_count} anomalies detected in monitoring period.")
        
        # Alert insights
        active_alerts = summary.get("active_alerts", 0)
        if active_alerts > 0:
            insights.append(f"{active_alerts} active alerts require attention.")
        
        if not insights:
            insights.append("System is operating within normal parameters.")
        
        return insights
    
    def _add_header_footer(self, canvas, doc):
        """Add header and footer to each page"""
        canvas.saveState()
        
        # Header
        canvas.setStrokeColor(self.PRIMARY_COLOR)
        canvas.setLineWidth(2)
        canvas.line(0.75*inch, doc.height + 1.2*inch, doc.width + 0.75*inch, doc.height + 1.2*inch)
        
        # Footer
        canvas.setFont('Helvetica', 9)
        canvas.setFillColor(self.GRAY_COLOR)
        footer_text = f"RhinoMetric v2.2.0 Enterprise | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        canvas.drawString(0.75*inch, 0.5*inch, footer_text)
        
        # Page number
        page_num = canvas.getPageNumber()
        canvas.drawRightString(doc.width + 0.75*inch, 0.5*inch, f"Page {page_num}")
        
        canvas.restoreState()


# Global PDF generator instance
pdf_generator = PDFGenerator()
