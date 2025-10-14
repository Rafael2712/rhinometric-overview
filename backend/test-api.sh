#!/bin/bash

# Test script para RhinoMetric SaaS API

echo "🧪 Testing RhinoMetric SaaS API"
echo "================================"

# Health Check
echo "1. Health Check:"
curl -s http://localhost:3001/api/v1/health | jq '.' || echo "❌ Health check failed"
echo ""

# Status Check  
echo "2. Status Check:"
curl -s http://localhost:3001/api/v1/status | jq '.' || echo "❌ Status check failed"
echo ""

# Get all tenants (should require auth, but let's see the response)
echo "3. Tenants endpoint (should require auth):"
curl -s http://localhost:3001/api/v1/tenants | jq '.' || echo "❌ Tenants endpoint failed"
echo ""

# Auth endpoint test (should return error for missing credentials)
echo "4. Auth endpoint (should return error):"
curl -s -X POST http://localhost:3001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{}' | jq '.' || echo "❌ Auth endpoint failed"
echo ""

echo "✅ API testing completed"