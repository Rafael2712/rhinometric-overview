#!/usr/bin/env python3
import asyncio
import sys
sys.path.insert(0, '/app')

from app.prometheus_client import PrometheusClient

async def test():
    pc = PrometheusClient('http://prometheus:9090')
    
    # Test query that might return multiple series
    query = "node_cpu_seconds_total"
    
    print(f"Testing query: {query}")
    values = await pc.fetch_metric_values(query, hours=1)
    
    print(f"Type: {type(values)}")
    print(f"Length: {len(values)}")
    
    if len(values) > 0:
        print(f"First 3 values: {values[:3]}")
        print(f"Last 3 values: {values[-3:]}")
        
        # Check for nested structures
        has_nested = any(isinstance(v, (list, tuple)) for v in values)
        print(f"Has nested structures: {has_nested}")
        
        if has_nested:
            print("PROBLEM: Values contain nested structures!")
            for i, v in enumerate(values[:5]):
                print(f"  values[{i}]: {type(v)} = {v}")

if __name__ == "__main__":
    asyncio.run(test())
