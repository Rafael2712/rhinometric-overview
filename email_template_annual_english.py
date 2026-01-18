# ENGLISH EMAIL TEMPLATE FOR ANNUAL LICENSES - Rhinometric v2.5.0

def get_annual_license_email_html(license_key, expires_at_str, days_remaining, tier, max_hosts, server_base_url):
    """Generate English HTML email for Annual licenses with download links"""
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                   line-height: 1.6; color: #333; margin: 0; padding: 0; }}
            .container {{ max-width: 600px; margin: 0 auto; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                      color: white; padding: 40px 30px; text-align: center; }}
            .header h1 {{ margin: 0 0 10px 0; font-size: 32px; }}
            .header p {{ margin: 0; opacity: 0.9; font-size: 16px; }}
            
            .content {{ background: #f9fafb; padding: 30px; }}
            
            .license-box {{ background: white; padding: 25px; margin: 20px 0;
                           border-left: 4px solid #10b981; border-radius: 8px; 
                           box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .license-box h2 {{ color: #1e3a8a; margin-top: 0; font-size: 22px; }}
            
            .license-key {{ background: #f3f4f6; padding: 15px; 
                           font-family: 'Courier New', monospace;
                           font-size: 18px; font-weight: bold; 
                           border-radius: 6px; word-break: break-all; 
                           margin: 15px 0; border: 2px dashed #667eea; }}
            
            .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; 
                         gap: 15px; margin: 20px 0; }}
            .info-item {{ background: #f9fafb; padding: 12px; border-radius: 6px; }}
            .info-item strong {{ display: block; color: #6b7280; font-size: 12px; 
                                 text-transform: uppercase; margin-bottom: 5px; }}
            .info-item span {{ color: #1e3a8a; font-size: 16px; font-weight: 600; }}
            
            .download-section {{ background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                                 padding: 30px; border-radius: 8px; margin: 25px 0; 
                                 text-align: center; }}
            .download-section h3 {{ color: white; margin: 0 0 20px 0; font-size: 20px; }}
            
            .btn {{ display: inline-block; padding: 14px 28px; 
                   background: white; color: #10b981; 
                   text-decoration: none; border-radius: 6px; 
                   font-weight: 600; font-size: 16px;
                   box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                   transition: all 0.3s; }}
            .btn:hover {{ transform: translateY(-2px); box-shadow: 0 6px 12px rgba(0,0,0,0.15); }}
            
            .docs-section {{ background: white; padding: 25px; 
                            border-radius: 8px; margin: 20px 0; }}
            .docs-section h3 {{ color: #1e3a8a; margin-top: 0; }}
            .docs-links {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
            .doc-link {{ display: block; padding: 12px; background: #f3f4f6; 
                        text-decoration: none; color: #667eea; border-radius: 6px;
                        text-align: center; font-weight: 500; 
                        border: 1px solid #e5e7eb; }}
            .doc-link:hover {{ background: #667eea; color: white; }}
            
            .features {{ background: white; padding: 25px; border-radius: 8px; }}
            .features h3 {{ color: #1e3a8a; margin-top: 0; }}
            .features ul {{ list-style: none; padding: 0; margin: 0; }}
            .features li {{ padding: 8px 0; border-bottom: 1px solid #f3f4f6; }}
            .features li:last-child {{ border-bottom: none; }}
            
            .warning-box {{ background: #fffbeb; border: 2px solid #fcd34d;
                           padding: 20px; border-radius: 8px; margin: 20px 0; }}
            .warning-box h4 {{ color: #d97706; margin: 0 0 10px 0; }}
            
            .support-box {{ text-align: center; margin: 25px 0; padding: 20px;
                           background: white; border-radius: 8px; }}
            .support-box p {{ margin: 8px 0; }}
            .support-box a {{ color: #667eea; text-decoration: none; font-weight: 500; }}
            
            .footer {{ background: #1f2937; color: #9ca3af; padding: 25px; 
                      text-align: center; font-size: 12px; }}
            .footer strong {{ color: #f3f4f6; }}
            .footer p {{ margin: 8px 0; }}
            
            .highlight {{ color: #10b981; font-weight: bold; font-size: 18px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <!-- Header -->
            <div class="header">
                <h1>🔑 Your Rhinometric License</h1>
                <p>Enterprise On-Premise Observability Platform</p>
            </div>

            <!-- Content -->
            <div class="content">
                <!-- License Info Box -->
                <div class="license-box">
                    <h2>📋 License Information</h2>
                    
                    <p style="margin-bottom: 10px;"><strong>License Key:</strong></p>
                    <div class="license-key">{license_key}</div>
                    
                    <div class="info-grid">
                        <div class="info-item">
                            <strong>Tier</strong>
                            <span>{tier.replace('_', ' ').title()}</span>
                        </div>
                        <div class="info-item">
                            <strong>Max Hosts</strong>
                            <span>{max_hosts} hosts</span>
                        </div>
                        <div class="info-item">
                            <strong>Expires</strong>
                            <span>{expires_at_str}</span>
                        </div>
                        <div class="info-item">
                            <strong>Days Remaining</strong>
                            <span class="highlight">{days_remaining} days</span>
                        </div>
                    </div>
                </div>

                <!-- Download Section -->
                <div class="download-section">
                    <h3>📥 Download Annual Installer</h3>
                    <p style="color: rgba(255,255,255,0.9); margin-bottom: 20px;">
                        Production-ready installer for Linux (Ubuntu/Debian/CentOS)
                    </p>
                    <a href="{server_base_url}/downloads/annual-installer" class="btn">
                        ⬇️ Download Installer (Annual License)
                    </a>
                </div>

                <!-- Documentation Links -->
                <div class="docs-section">
                    <h3>📚 Documentation & Manuals</h3>
                    <p style="color: #6b7280; margin-bottom: 15px;">
                        Complete guides to get you started
                    </p>
                    <div class="docs-links">
                        <a href="{server_base_url}/docs/installation-guide?lang=en" class="doc-link">
                            📘 Installation Guide (EN)
                        </a>
                        <a href="{server_base_url}/docs/installation-guide?lang=es" class="doc-link">
                            📘 Guía Instalación (ES)
                        </a>
                        <a href="{server_base_url}/docs/user-manual?lang=en" class="doc-link">
                            📖 User Manual (EN)
                        </a>
                        <a href="{server_base_url}/docs/user-manual?lang=es" class="doc-link">
                            📖 Manual Usuario (ES)
                        </a>
                    </div>
                </div>

                <!-- Features Included -->
                <div class="features">
                    <h3>✅ Included Features</h3>
                    <ul>
                        <li>📊 Pre-configured Grafana dashboards</li>
                        <li>📈 Metrics monitoring with Prometheus (30-day retention)</li>
                        <li>📝 Centralized logs with Loki</li>
                        <li>🔍 Distributed tracing with Tempo + Jaeger</li>
                        <li>🚨 Advanced alerting with Alertmanager</li>
                        <li>🤖 AI-powered anomaly detection (Prophet + IsolationForest)</li>
                        <li>🎨 Rhinometric Console (Vue.js dashboard)</li>
                        <li>🔗 API Connector for external integrations</li>
                    </ul>
                </div>

                <!-- Important Notice -->
                <div class="warning-box">
                    <h4>⚠️ Important - On-Premise Solution</h4>
                    <p style="margin: 0; color: #78350f;">
                        Rhinometric is a <strong>100% on-premise</strong> solution. 
                        All your data stays in your infrastructure and never leaves your environment. 
                        <strong>GDPR compliant</strong> by design.
                    </p>
                </div>

                <!-- Support -->
                <div class="support-box">
                    <p style="font-size: 16px; color: #1e3a8a;"><strong>Need Help?</strong></p>
                    <p>📧 Email: <a href="mailto:rafael.canelon@rhinometric.com">rafael.canelon@rhinometric.com</a></p>
                    <p>🌐 Web: <a href="https://rhinometric.com">rhinometric.com</a></p>
                    <p>📚 Docs: <a href="https://rhinometric.com/documentation">rhinometric.com/documentation</a></p>
                    <p style="color: #6b7280; font-size: 14px; margin-top: 15px;">
                        <strong>Support hours:</strong> Monday-Friday, 9:00-18:00 CET<br>
                        <strong>Response time:</strong> &lt; 4 hours (Annual Standard)
                    </p>
                </div>
            </div>

            <!-- Footer -->
            <div class="footer">
                <p><strong>RHINOMETRIC</strong> | Enterprise Observability Platform</p>
                <p>© 2025 Rhinometric. All rights reserved.</p>
                <p style="margin-top: 15px; font-size: 10px; opacity: 0.8;">
                    This message was automatically generated by RHINOMETRIC License Monitor<br>
                    On-premise monitoring system - 100% GDPR compliant - No data leaves your infrastructure
                </p>
            </div>
        </div>
    </body>
    </html>
    """
