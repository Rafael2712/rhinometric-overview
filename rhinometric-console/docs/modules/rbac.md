# Module: RBAC (Role-Based Access Control)

**Version:** 2.7.0  
**Classification:** Internal  
**Maintained by:** Rhinometric Team — info@rhinometric.com

---

## Purpose

Control user access to platform features based on assigned roles. Enforced at both the API (backend middleware) and UI (frontend route guards and component visibility) levels.

## What It Does

- **Authentication**: JWT-based authentication with token issued on login. Tokens contain user ID, role, and expiry.
- **4 Predefined Roles**:
  - **Owner**: Full access including user management, license operations, and system configuration.
  - **Admin**: Full access to monitoring and incident management features. Cannot manage users or licenses.
  - **Operator**: Can view all data, create/modify alert rules, manage incidents. Cannot modify system settings.
  - **Viewer**: Read-only access to dashboards, anomalies, incidents. Cannot create or modify any resources.
- **API Enforcement**: FastAPI dependency injection checks the JWT role claim against route-level permission requirements.
- **UI Enforcement**: React route guards check user role from auth store. Restricted components/buttons are hidden or disabled based on role.
- **User Management**: Owner can create, edit, deactivate, and assign roles to users.
- **Session**: JWT tokens expire after a configurable period (default: 24 hours). Refresh flow is available.

## What It Does Not Do

- Does not support custom roles (only the 4 predefined roles).
- Does not support resource-level permissions (e.g., per-service access).
- Does not support organizational units or team-based access.
- Does not provide a complete audit trail of all user actions.
- Does not integrate with external identity providers (LDAP, SAML, OIDC).
- Does not support API key authentication for programmatic access.
- Does not enforce concurrent session limits.

## Role Permission Matrix

| Permission | Owner | Admin | Operator | Viewer |
|-----------|:----------:|:-----:|:--------:|:------:|
| View dashboards | ✓ | ✓ | ✓ | ✓ |
| View anomalies | ✓ | ✓ | ✓ | ✓ |
| View incidents | ✓ | ✓ | ✓ | ✓ |
| View alerts | ✓ | ✓ | ✓ | ✓ |
| Create alert rules | ✓ | ✓ | ✓ | ✗ |
| Manage incidents | ✓ | ✓ | ✓ | ✗ |
| Manage services | ✓ | ✓ | ✗ | ✗ |
| Manage notification channels | ✓ | ✓ | ✗ | ✗ |
| Configure SLO/SLA | ✓ | ✓ | ✗ | ✗ |
| Manage users | ✓ | ✗ | ✗ | ✗ |
| Manage licenses | ✓ | ✗ | ✗ | ✗ |
| System configuration | ✓ | ✗ | ✗ | ✗ |

## Data Model

### User

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `username` | String | Login identifier |
| `email` | String | User email |
| `password_hash` | String | Bcrypt hash |
| `role` | Enum | superadmin, admin, operator, viewer |
| `is_active` | Boolean | Whether user can log in |
| `created_at` | DateTime | Account creation |
| `last_login` | DateTime | Last successful login |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/login` | Authenticate and receive JWT |
| POST | `/api/auth/refresh` | Refresh JWT token |
| GET | `/api/users/` | List users (Owner only) |
| POST | `/api/users/` | Create user (Owner only) |
| PUT | `/api/users/{id}` | Update user (Owner only) |
| DELETE | `/api/users/{id}` | Deactivate user (Owner only) |
| GET | `/api/users/me` | Current user profile |

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_SECRET` | — | Secret key for token signing |
| `JWT_EXPIRY_HOURS` | `24` | Token lifetime in hours |
| `JWT_ALGORITHM` | `HS256` | Signing algorithm |
| `DEFAULT_ADMIN_USER` | `admin` | Initial admin username |
| `DEFAULT_ADMIN_PASSWORD` | — | Initial admin password |

## Dependencies

- **PostgreSQL**: Stores user accounts.
- **Redis**: Can be used for token blacklisting (optional).
- **Frontend**: Zustand auth store holds current user/role.

## Frontend

- **Routes:** `/users` (Owner), `/profile`
- **Key Features:** User list with role assignment, user creation form, profile editor.
- **Guards:** React `ProtectedRoute` component checks role before rendering. Insufficient role redirects to dashboard.

## Known Limitations

1. Only 4 predefined roles — no custom roles.
2. No resource-level permissions.
3. No audit trail.
4. No external IdP integration.
5. No API key authentication.
6. No concurrent session limits.

---

*Rhinometric Team — info@rhinometric.com*
