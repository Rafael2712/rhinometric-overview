#!/usr/bin/env python3
"""
RhinoMetric Report Generator - Test Suite
Tests all core functionality of the Report Generator v2.2.0
"""
import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8086"
COLORS = {
    'GREEN': '\033[92m',
    'RED': '\033[91m',
    'YELLOW': '\033[93m',
    'BLUE': '\033[94m',
    'RESET': '\033[0m'
}


class TestReportGenerator:
    """Test suite for Report Generator"""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests_run = 0
    
    def log(self, message: str, color: str = 'RESET'):
        """Print colored log message"""
        print(f"{COLORS[color]}{message}{COLORS['RESET']}")
    
    def test(self, name: str, func):
        """Run a test function"""
        self.tests_run += 1
        try:
            self.log(f"\n[TEST {self.tests_run}] {name}", 'BLUE')
            func()
            self.passed += 1
            self.log(f"✅ PASSED: {name}", 'GREEN')
            return True
        except AssertionError as e:
            self.failed += 1
            self.log(f"❌ FAILED: {name}", 'RED')
            self.log(f"   Error: {str(e)}", 'RED')
            return False
        except Exception as e:
            self.failed += 1
            self.log(f"💥 ERROR: {name}", 'RED')
            self.log(f"   Exception: {str(e)}", 'RED')
            return False
    
    def assert_status_code(self, response, expected: int):
        """Assert HTTP status code"""
        assert response.status_code == expected, \
            f"Expected status {expected}, got {response.status_code}. Response: {response.text}"
    
    def assert_contains(self, data: dict, key: str):
        """Assert dictionary contains key"""
        assert key in data, f"Response missing key: {key}. Keys: {list(data.keys())}"
    
    # === TEST CASES ===
    
    def test_health_check(self):
        """Test 1: Health check endpoint"""
        response = requests.get(f"{BASE_URL}/health")
        self.assert_status_code(response, 200)
        
        data = response.json()
        self.assert_contains(data, 'status')
        self.assert_contains(data, 'version')
        
        assert data['status'] == 'healthy', f"Service not healthy: {data['status']}"
        assert data['version'] == '2.2.0', f"Wrong version: {data['version']}"
        
        self.log(f"   Health: {data['status']} | Version: {data['version']} | Uptime: {data.get('uptime_seconds', 0):.1f}s")
    
    def test_root_endpoint(self):
        """Test 2: Root endpoint"""
        response = requests.get(f"{BASE_URL}/")
        self.assert_status_code(response, 200)
        
        data = response.json()
        assert data['service'] == 'RhinoMetric Report Generator'
        assert 'endpoints' in data
        
        self.log(f"   Service: {data['service']}")
    
    def test_metrics_endpoint(self):
        """Test 3: Prometheus metrics endpoint"""
        response = requests.get(f"{BASE_URL}/metrics")
        self.assert_status_code(response, 200)
        
        metrics = response.text
        assert 'rhinometric_reports_generated_total' in metrics
        assert 'rhinometric_report_generation_seconds' in metrics
        
        self.log("   Metrics endpoint working")
    
    def test_config_endpoint(self):
        """Test 4: Configuration endpoint"""
        response = requests.get(f"{BASE_URL}/api/v1/config")
        self.assert_status_code(response, 200)
        
        config = response.json()
        self.assert_contains(config, 'server')
        self.assert_contains(config, 'smtp')
        self.assert_contains(config, 'storage')
        
        self.log(f"   Reports configured: {config.get('reports_configured', 0)}")
        self.log(f"   SMTP enabled: {config['smtp'].get('enabled', False)}")
    
    def test_generate_executive_report_pdf(self):
        """Test 5: Generate executive PDF report (no email)"""
        payload = {
            "report_type": "executive",
            "period_hours": 24,
            "formats": ["pdf"],
            "recipients": [],
            "include_charts": True,
            "include_anomalies": True,
            "include_metrics": True
        }
        
        self.log("   Generating PDF report (this may take 30-60 seconds)...")
        start_time = time.time()
        
        response = requests.post(
            f"{BASE_URL}/api/v1/reports/generate",
            json=payload,
            timeout=120
        )
        
        generation_time = time.time() - start_time
        
        self.assert_status_code(response, 200)
        
        data = response.json()
        self.assert_contains(data, 'report_id')
        self.assert_contains(data, 'status')
        self.assert_contains(data, 'files')
        
        assert data['status'] == 'completed', f"Report status: {data['status']}"
        assert 'pdf' in data['files'], "PDF file not generated"
        
        self.log(f"   Report ID: {data['report_id']}")
        self.log(f"   Status: {data['status']}")
        self.log(f"   Generation time: {generation_time:.2f}s")
        self.log(f"   PDF: {data['files']['pdf']}")
        
        # Store report_id for next test
        self.last_report_id = data['report_id']
        return data['report_id']
    
    def test_list_reports(self):
        """Test 6: List generated reports"""
        response = requests.get(f"{BASE_URL}/api/v1/reports/list?limit=10")
        self.assert_status_code(response, 200)
        
        data = response.json()
        self.assert_contains(data, 'reports')
        self.assert_contains(data, 'count')
        
        assert data['count'] > 0, "No reports found"
        
        self.log(f"   Total reports: {data['count']}")
        
        if data['reports']:
            first_report = data['reports'][0]
            self.log(f"   Latest: {first_report['filename']} ({first_report['size_bytes']} bytes)")
    
    def test_download_report(self):
        """Test 7: Download generated report"""
        # First list reports to get a filename
        response = requests.get(f"{BASE_URL}/api/v1/reports/list?limit=1")
        self.assert_status_code(response, 200)
        
        data = response.json()
        assert data['count'] > 0, "No reports available to download"
        
        filename = data['reports'][0]['filename']
        
        # Download the report
        response = requests.get(f"{BASE_URL}/api/v1/reports/download/{filename}")
        self.assert_status_code(response, 200)
        
        assert response.headers['content-type'] == 'application/pdf'
        assert len(response.content) > 1000, "PDF file too small"
        
        self.log(f"   Downloaded: {filename} ({len(response.content)} bytes)")
    
    def test_generate_technical_report(self):
        """Test 8: Generate technical report"""
        payload = {
            "report_type": "technical",
            "period_hours": 24,
            "formats": ["pdf"],
            "recipients": [],
            "include_charts": True,
            "include_anomalies": True,
            "include_metrics": True
        }
        
        self.log("   Generating technical report...")
        start_time = time.time()
        
        response = requests.post(
            f"{BASE_URL}/api/v1/reports/generate",
            json=payload,
            timeout=120
        )
        
        generation_time = time.time() - start_time
        
        self.assert_status_code(response, 200)
        
        data = response.json()
        assert data['report_type'] == 'technical'
        assert data['status'] == 'completed'
        
        self.log(f"   Report ID: {data['report_id']}")
        self.log(f"   Generation time: {generation_time:.2f}s")
    
    def test_generate_anomaly_report(self):
        """Test 9: Generate anomaly analysis report"""
        payload = {
            "report_type": "anomaly",
            "period_hours": 48,
            "formats": ["pdf"],
            "recipients": [],
            "include_charts": True,
            "include_anomalies": True,
            "include_metrics": False
        }
        
        self.log("   Generating anomaly report...")
        
        response = requests.post(
            f"{BASE_URL}/api/v1/reports/generate",
            json=payload,
            timeout=120
        )
        
        self.assert_status_code(response, 200)
        
        data = response.json()
        assert data['report_type'] == 'anomaly'
        
        self.log(f"   Report ID: {data['report_id']}")
    
    def test_data_aggregation(self):
        """Test 10: Verify data aggregation works"""
        # This is tested indirectly through report generation
        # but we can verify Prometheus connectivity
        import httpx
        
        try:
            # Test Prometheus
            prom_response = requests.get("http://localhost:9090/api/v1/query?query=up", timeout=5)
            assert prom_response.status_code == 200, "Prometheus not accessible"
            self.log("   ✓ Prometheus connection OK")
            
            # Test AI Anomaly API
            ai_response = requests.get("http://localhost:8085/health", timeout=5)
            assert ai_response.status_code == 200, "AI Anomaly API not accessible"
            self.log("   ✓ AI Anomaly API connection OK")
            
            # Test Grafana
            grafana_response = requests.get("http://localhost:3000/api/health", timeout=5)
            assert grafana_response.status_code == 200, "Grafana not accessible"
            self.log("   ✓ Grafana connection OK")
        
        except Exception as e:
            self.log(f"   ⚠️  Data source connectivity issue: {e}", 'YELLOW')
            raise
    
    def test_config_reload(self):
        """Test 11: Configuration reload"""
        response = requests.post(f"{BASE_URL}/api/v1/config/reload")
        self.assert_status_code(response, 200)
        
        data = response.json()
        assert data['status'] == 'success'
        
        self.log("   Configuration reloaded successfully")
    
    def test_pdf_generation_stress(self):
        """Test 12: Stress test - multiple reports"""
        self.log("   Generating 3 reports in sequence...")
        
        for i in range(3):
            payload = {
                "report_type": "executive",
                "period_hours": 1,
                "formats": ["pdf"],
                "recipients": []
            }
            
            response = requests.post(
                f"{BASE_URL}/api/v1/reports/generate",
                json=payload,
                timeout=120
            )
            
            self.assert_status_code(response, 200)
            self.log(f"   Report {i+1}/3: {response.json()['report_id']}")
            
            time.sleep(2)  # Small delay between requests
        
        self.log("   All stress test reports generated")
    
    # === RUN TESTS ===
    
    def run_all(self):
        """Run all tests"""
        self.log("\n" + "="*70, 'BLUE')
        self.log("🧪 RhinoMetric Report Generator - Test Suite v2.2.0", 'BLUE')
        self.log("="*70 + "\n", 'BLUE')
        
        tests = [
            ("Health Check", self.test_health_check),
            ("Root Endpoint", self.test_root_endpoint),
            ("Metrics Endpoint", self.test_metrics_endpoint),
            ("Configuration Endpoint", self.test_config_endpoint),
            ("Generate Executive PDF Report", self.test_generate_executive_report_pdf),
            ("List Reports", self.test_list_reports),
            ("Download Report", self.test_download_report),
            ("Generate Technical Report", self.test_generate_technical_report),
            ("Generate Anomaly Report", self.test_generate_anomaly_report),
            ("Data Aggregation Connectivity", self.test_data_aggregation),
            ("Configuration Reload", self.test_config_reload),
            ("PDF Generation Stress Test", self.test_pdf_generation_stress),
        ]
        
        for name, func in tests:
            self.test(name, func)
            time.sleep(1)  # Small delay between tests
        
        # Summary
        self.log("\n" + "="*70, 'BLUE')
        self.log("📊 TEST SUMMARY", 'BLUE')
        self.log("="*70, 'BLUE')
        self.log(f"Total Tests: {self.tests_run}")
        self.log(f"Passed: {self.passed}", 'GREEN' if self.passed == self.tests_run else 'YELLOW')
        self.log(f"Failed: {self.failed}", 'RED' if self.failed > 0 else 'GREEN')
        
        success_rate = (self.passed / self.tests_run * 100) if self.tests_run > 0 else 0
        self.log(f"Success Rate: {success_rate:.1f}%", 'GREEN' if success_rate == 100 else 'YELLOW')
        
        if self.failed == 0:
            self.log("\n✅ ALL TESTS PASSED! Report Generator is fully operational.", 'GREEN')
            return 0
        else:
            self.log(f"\n⚠️  {self.failed} test(s) failed. Review errors above.", 'YELLOW')
            return 1


if __name__ == "__main__":
    tester = TestReportGenerator()
    
    try:
        exit_code = tester.run_all()
        sys.exit(exit_code)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    
    except Exception as e:
        print(f"\n\n💥 Unexpected error: {e}")
        sys.exit(1)
