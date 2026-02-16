# 📋 Comandos Git para v2.5.3 Auth Enhancement

## Archivos a Incluir en el Commit

### Backend
- `rhinometric-console/backend/.env.example` (NUEVO)
- `rhinometric-console/backend/config.py`
- `rhinometric-console/backend/requirements.txt`
- `rhinometric-console/backend/routers/auth.py`
- `rhinometric-console/backend/services/email_service.py` (NUEVO)
- `rhinometric-console/backend/models/__init__.py`
- `rhinometric-console/backend/models/user.py`
- `rhinometric-console/backend/models/password_reset.py` (NUEVO)
- `rhinometric-console/backend/alembic/env.py`
- `rhinometric-console/backend/alembic/versions/4a7b3c8d9e2f_password_reset_tokens.py` (NUEVO)
- `rhinometric-console/backend/test_smtp.py` (NUEVO)
- `rhinometric-console/backend/test_forgot_password.py` (NUEVO)

### Frontend
- `rhinometric-console/frontend/src/pages/Login.tsx`
- `rhinometric-console/frontend/src/pages/ResetPassword.tsx` (NUEVO)
- `rhinometric-console/frontend/src/App.tsx`

### Documentación
- `CHANGELOG_V253_ADDITION.md` (NUEVO)
- `README_AUTH.md` (NUEVO)
- `ADMIN_QUICK_GUIDE.md` (NUEVO)
- `BUG_FIX_REPORT_V254.md` (NUEVO)

### Scripts de Test
- `test_password_reset_flow_v254.sh` (NUEVO)

---

## Comandos a Ejecutar

