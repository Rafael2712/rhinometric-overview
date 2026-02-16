# API Documentation - RhinoMetric SaaS

## Base URL
- **Development**: `http://localhost:3001/api/v1`
- **Staging**: `https://staging-api.rhinometric.com/api/v1`
- **Production**: `https://api.rhinometric.com/api/v1`

## Authentication

All API endpoints (except public ones) require JWT authentication.

### Headers
```http
Authorization: Bearer <jwt-token>
Content-Type: application/json
```

## Endpoints

### 🔐 Authentication

#### Register New User and Tenant
```http
POST /auth/register
```

**Request Body:**
```json
{
  "email": "admin@company.com",
  "password": "securepassword123",
  "tenantName": "My Company",
  "firstName": "John",
  "lastName": "Doe"
}
```

**Response (201):**
```json
{
  "message": "Registration successful",
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": "uuid",
    "email": "admin@company.com",
    "role": "admin",
    "firstName": "John",
    "lastName": "Doe"
  },
  "tenant": {
    "id": "uuid",
    "name": "My Company",
    "slug": "my-company",
    "plan": "free"
  }
}
```

#### User Login
```http
POST /auth/login
```

**Request Body:**
```json
{
  "email": "admin@company.com",
  "password": "securepassword123"
}
```

**Response (200):**
```json
{
  "message": "Login successful",
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": "uuid",
    "email": "admin@company.com",
    "role": "admin",
    "firstName": "John",
    "lastName": "Doe"
  },
  "tenant": {
    "id": "uuid",
    "name": "My Company",
    "slug": "my-company",
    "plan": "free"
  }
}
```

#### Get Current User
```http
GET /auth/me
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "user": {
    "id": "uuid",
    "email": "admin@company.com",
    "role": "admin",
    "firstName": "John",
    "lastName": "Doe",
    "createdAt": "2024-01-01T00:00:00Z"
  },
  "tenant": {
    "id": "uuid",
    "name": "My Company",
    "slug": "my-company",
    "plan": "free"
  }
}
```

#### Logout
```http
POST /auth/logout
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "message": "Logout successful"
}
```

### 🏢 Tenant Management

#### List All Tenants (Admin)
```http
GET /tenants?page=1&limit=10
Authorization: Bearer <admin-token>
```

**Response (200):**
```json
{
  "tenants": [
    {
      "id": "uuid",
      "name": "Company A",
      "slug": "company-a",
      "plan": "professional",
      "status": "active",
      "user_count": 5,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 25,
    "pages": 3
  }
}
```

#### Get Single Tenant
```http
GET /tenants/:id
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "tenant": {
    "id": "uuid",
    "name": "Company A",
    "slug": "company-a",
    "plan": "professional",
    "status": "active",
    "user_count": 5,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

#### Create New Tenant
```http
POST /tenants
Authorization: Bearer <admin-token>
```

**Request Body:**
```json
{
  "name": "New Company",
  "plan": "starter"
}
```

**Response (201):**
```json
{
  "message": "Tenant created successfully",
  "tenant": {
    "id": "uuid",
    "name": "New Company",
    "slug": "new-company",
    "plan": "starter",
    "status": "active",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

#### Update Tenant
```http
PUT /tenants/:id
Authorization: Bearer <admin-token>
```

**Request Body:**
```json
{
  "name": "Updated Company Name",
  "plan": "professional",
  "status": "active"
}
```

**Response (200):**
```json
{
  "message": "Tenant updated successfully",
  "tenant": {
    "id": "uuid",
    "name": "Updated Company Name",
    "slug": "new-company",
    "plan": "professional",
    "status": "active",
    "updated_at": "2024-01-01T12:00:00Z"
  }
}
```

#### Delete Tenant
```http
DELETE /tenants/:id
Authorization: Bearer <admin-token>
```

**Response (200):**
```json
{
  "message": "Tenant deleted successfully"
}
```

#### Get Tenant Statistics
```http
GET /tenants/:id/stats
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "statistics": {
    "user_count": 5,
    "new_users_30d": 2,
    "tenant_created_at": "2024-01-01T00:00:00Z"
  }
}
```

### ⚕️ Health Check

#### Basic Health Check
```http
GET /health
```

**Response (200):**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "uptime": "3600s",
  "checks": {
    "database": {
      "status": "healthy",
      "responseTime": "15ms"
    },
    "memory": {
      "status": "healthy",
      "usage": "256MB"
    }
  },
  "system": {
    "node_version": "v10.24.0",
    "platform": "linux",
    "uptime": 3600
  }
}
```

#### Detailed Health Check
```http
GET /health/detailed
```

**Response (200):**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "responseTime": "25ms",
  "components": {
    "database": {
      "status": "healthy",
      "responseTime": "15ms",
      "connections": "active"
    },
    "memory": {
      "rss": "256MB",
      "heapTotal": "128MB",
      "heapUsed": "64MB",
      "external": "32MB"
    },
    "cpu": {
      "user": 1234567,
      "system": 987654
    }
  },
  "environment": {
    "node_env": "production",
    "api_version": "v1",
    "port": "3000"
  }
}
```

## Error Responses

### Standard Error Format
```json
{
  "error": "Error Type",
  "message": "Detailed error message",
  "path": "/api/v1/endpoint",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Common Status Codes

- **200**: Success
- **201**: Created
- **400**: Bad Request (validation error)
- **401**: Unauthorized (invalid/missing token)
- **403**: Forbidden (insufficient permissions)
- **404**: Not Found
- **409**: Conflict (resource already exists)
- **429**: Too Many Requests (rate limit)
- **500**: Internal Server Error
- **503**: Service Unavailable

## Rate Limiting

- **Limit**: 100 requests per 15 minutes per IP
- **Headers**:
  - `X-RateLimit-Limit`: Request limit
  - `X-RateLimit-Remaining`: Requests remaining
  - `X-RateLimit-Reset`: Reset time

## Multi-Tenancy

The API automatically scopes data access based on the tenant ID in the JWT token. All operations are automatically filtered by tenant unless you're a super admin.

### Tenant Isolation

- Each tenant's data is completely isolated
- JWT tokens include tenant ID
- All database queries are tenant-scoped
- Cross-tenant access is prevented

## Examples

### cURL Examples

```bash
# Register new user/tenant
curl -X POST http://localhost:3001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@company.com",
    "password": "securepassword123",
    "tenantName": "My Company",
    "firstName": "John",
    "lastName": "Doe"
  }'

# Login
curl -X POST http://localhost:3001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@company.com",
    "password": "securepassword123"
  }'

# Get current user (with token)
curl -X GET http://localhost:3001/api/v1/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."

# Health check
curl -X GET http://localhost:3001/api/v1/health
```