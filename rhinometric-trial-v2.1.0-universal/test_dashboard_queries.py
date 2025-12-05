#!/usr/bin/env python3
import requests
import json

def test_query(name, query):
    try:
        r = requests.get('http://localhost:9090/api/v1/query', params={'query': query}, timeout=5)
        data = r.json()
        if data['status'] == 'success':
            results = len(data['data']['result'])
            print(f"✅ {name}: {results} series")
            if results > 0:
                for m in data['data']['result'][:3]:
                    api_name = m['metric'].get('api_name', 'N/A')
                    value = m['value'][1]
                    print(f"   - {api_name}: {value}")
        else:
            print(f"❌ {name}: {data.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"❌ {name}: {str(e)}")

print("=== TESTING DASHBOARD QUERIES ===\n")

test_query("1. Health Status", "api_proxy_health_status")
test_query("2. Total Requests", "api_proxy_requests_total")
test_query("3. Request Rate (all)", "sum(rate(api_proxy_requests_total[5m])) by (api_name)")
test_query("4. Request Rate (200)", 'sum(rate(api_proxy_requests_total{status="200"}[5m])) by (api_name)')
test_query("5. Response Time p95", "histogram_quantile(0.95, sum(rate(api_proxy_request_duration_seconds_bucket[5m])) by (api_name, le))")
test_query("6. Cache Hits", "sum(rate(api_proxy_cache_hits_total[5m])) by (api_name)")
test_query("7. Success Count", 'sum(increase(api_proxy_requests_total{status="200"}[1m])) by (api_name)')
test_query("8. Error Count", 'sum(increase(api_proxy_requests_total{status="0"}[1m])) by (api_name)')
