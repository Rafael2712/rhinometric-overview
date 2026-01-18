# 🐛 ISSUES PENDIENTES - Rhinometric v2.6.0

**Fecha creación:** 17 de diciembre de 2025  
**Prioridad:** Alta  
**Estado:** Planificado para próxima release

---

## 🔴 ISSUE #1: Implementar Refresh Token Automático en Console

### **Problema Actual:**
El token JWT del Rhinometric Console expira después de 30 días, forzando logout manual del usuario y reseteo de credenciales.

### **Workaround Temporal (v2.5.0):**
✅ Token extendido a 30 días (suficiente para trial de 14 días)
- **Archivo modificado:** `rhinometric-console/backend/config.py`
- **Cambio:** `ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30`

### **Solución Definitiva Requerida:**

#### **1. Backend Changes:**
```python
# Nuevo endpoint en auth.py
@router.post("/refresh", response_model=Token)
async def refresh_token(current_user: User = Depends(get_current_user)):
    """
    Refresh JWT token before expiration
    Returns new token with extended validity
    """
    access_token = create_access_token(
        data={"sub": current_user.username}
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "must_change_password": False
    }
```

#### **2. Frontend Changes:**
```javascript
// Auto-refresh token 10 minutes before expiration
const TOKEN_REFRESH_INTERVAL = 29 * 24 * 60 - 10; // 29 days 23h 50min

setInterval(async () => {
    const response = await fetch('/api/auth/refresh', {
        headers: {
            'Authorization': `Bearer ${currentToken}`
        }
    });
    
    if (response.ok) {
        const data = await response.json();
        localStorage.setItem('access_token', data.access_token);
        console.log('Token refreshed successfully');
    }
}, TOKEN_REFRESH_INTERVAL * 60 * 1000);
```

#### **3. Docker Rebuild:**
```bash
# Rebuild Console backend
docker compose -f docker-compose-trial.yml build rhinometric-console-backend

# Restart services
docker compose -f docker-compose-trial.yml restart rhinometric-console-backend rhinometric-console-frontend
```

### **Impacto:**
- **Severidad:** Media
- **Afecta a:** Trial (14 días), Demo (4 horas), Annual (1 año)
- **UX:** Logout forzado cada 30 días
- **Seguridad:** Media (token muy longevo = mayor ventana de ataque si se compromete)

### **Testing Checklist:**
- [ ] Token refresh funciona 10 min antes de expiración
- [ ] Frontend actualiza token automáticamente sin logout
- [ ] Si refresh falla, redirige a login limpiamente
- [ ] Múltiples tabs/ventanas sincronizan token
- [ ] Session storage persiste entre reloads

### **Estimación:**
- **Desarrollo:** 2-3 horas
- **Testing:** 1 hora
- **Documentación:** 30 min
- **Total:** 4 horas

---

## 🟠 ISSUE #2: Migrar Autenticación a PostgreSQL

### **Problema Actual:**
Usuarios almacenados en memoria (diccionario Python). Se pierden al reiniciar contenedor.

### **Workaround Temporal:**
Usuario `admin` hardcoded en código.

### **Solución Definitiva:**

#### **1. Crear Tabla Users:**
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'viewer',
    must_change_password BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_username ON users(username);
```

#### **2. Usar bcrypt para passwords:**
```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
```

#### **3. Conectar con PostgreSQL:**
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://rhinometric_user:rhinometric_pass@rhinometric-postgres:5432/rhinometric_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```

### **Impacto:**
- **Severidad:** Alta (seguridad)
- **Afecta a:** Todos los despliegues
- **Ventajas:** Persistencia, multi-usuario, auditoría

### **Estimación:**
- **Desarrollo:** 1 día
- **Migration scripts:** 2 horas
- **Testing:** 3 horas
- **Total:** 2 días

---

## 🟡 ISSUE #3: Implementar Session Management con Redis

### **Objetivo:**
Invalidar tokens activos cuando usuario cambia password o hace logout.

### **Stack:**
- Redis para blacklist de tokens
- TTL automático igual a expiración del token

### **Estimación:** 4 horas

---

## 📋 ROADMAP DE IMPLEMENTACIÓN

### **v2.5.1 (Hotfix - 1 semana):**
- ✅ ISSUE #1: Refresh token automático
- Minimal changes, máxima estabilidad

### **v2.6.0 (Feature Release - 3 semanas):**
- ✅ ISSUE #2: PostgreSQL para usuarios
- ✅ ISSUE #3: Redis session management
- Full testing suite
- Migration guide para upgrades

### **v2.7.0 (Enterprise - 2 meses):**
- SSO/SAML support
- RBAC (Role-Based Access Control)
- Audit logs completos
- API keys para integración

---

## 🔧 NOTAS DE IMPLEMENTACIÓN

### **Compatibilidad hacia atrás:**
- ✅ Licencias `.lic` existentes NO se ven afectadas
- ✅ Instaladores antiguos siguen funcionando (con token 30 días)
- ⚠️ Clientes con v2.5.0 necesitarán update manual para refresh automático

### **Breaking Changes:**
- Ninguno en v2.5.1
- v2.6.0 requiere migration de usuarios (script provisto)

### **Deployment Strategy:**
1. **Trial/Demo:** Update inmediato (low risk)
2. **Annual:** Rolling update coordinado con clientes
3. **Enterprise:** Mantenimiento planificado

---

## 📞 CONTACTO

**Responsable:** Rafael Cañelón  
**Email:** rafael.canelon@rhinometric.com  
**Fecha límite v2.5.1:** 31 de diciembre de 2025  
**Fecha límite v2.6.0:** 31 de enero de 2026
