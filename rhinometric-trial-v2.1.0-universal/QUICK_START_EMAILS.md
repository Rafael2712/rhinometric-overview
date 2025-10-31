# 🚀 QUICK START - Sistema de Emails Rhinometric v2.1.0

> **TL;DR**: Sistema de emails 95% completo. Solo falta: convertir PDFs (10 min) + configurar password (2 min) + testar (5 min) = **17 minutos para producción**.

---

## 📦 ¿QUÉ SE IMPLEMENTÓ?

### ✅ Email Automático Cuando Se Crea Licencia

Cada vez que alguien crea una licencia en http://localhost:8092, el cliente recibe:

📧 **Email HTML profesional** con:
- License key generado (RHINO-TRIAL-2025-ABC123XYZ456)
- Instrucciones de instalación (3 pasos)
- Banner GDPR compliance
- 2 PDFs adjuntos:
  - 📘 Manual de Usuario (20 páginas)
  - 📗 Guía de Instalación (15 páginas)

### 🔒 Seguridad y Compliance

- ✅ SMTP_PASSWORD en `.env` (gitignored)
- ✅ Banner GDPR (RGPD 2016/679)
- ✅ App passwords (NO contraseña principal)
- ✅ Retry automático (1x después de 30s)
- ✅ Logs completos sin exponer passwords

### 📊 Código Implementado

| Archivo | Líneas | Descripción |
|---------|--------|-------------|
| `license-server-v2/utils/email_sender.py` | 345 | Módulo principal de emails |
| `docs/manual_usuario.md` | 600+ | Manual completo del usuario |
| `docs/guia_instalacion.md` | 450+ | Guía de instalación paso a paso |
| `docs/EMAIL_SYSTEM_STATUS.md` | 400+ | Documentación técnica completa |
| `RESUMEN_IMPLEMENTACION.md` | 300+ | Testing y troubleshooting |
| **TOTAL** | **2,368** | 11 archivos modificados/creados |

---

## ⚡ COMANDOS RÁPIDOS - Testing en 5 Minutos

### 1️⃣ Configurar Password (2 min)

```bash
# Generar app password: https://accounts.zoho.com/home#security/security
# Editar .env
nano .env
# Agregar:
SMTP_PASSWORD=tu_app_password_zoho
```

### 2️⃣ Convertir PDFs (Opción Online - 3 min)

```
1. Ir a https://www.markdowntopdf.com/
2. Subir docs/manual_usuario.md → Descargar PDF → Guardar en docs/
3. Subir docs/guia_instalacion.md → Descargar PDF → Guardar en docs/
```

### 3️⃣ Reiniciar Servidor (30 seg)

```bash
docker compose -f docker-compose-v2.1.0.yml restart license-server-v2
```

### 4️⃣ Crear Licencia de Prueba (1 min)

```bash
curl -X POST http://localhost:5000/api/admin/licenses \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Test User",
    "client_email": "rafael.canelon@rhinometric.com",
    "license_type": "trial"
  }'
```

### 5️⃣ Verificar Email Recibido (30 seg)

Revisar inbox: rafael.canelon@rhinometric.com  
Asunto: `[Rhinometric] Activación de su licencia Trial`

---

## 📁 ESTRUCTURA DE ARCHIVOS

```
rhinometric-trial-v2.1.0-universal/
├── license-server-v2/
│   ├── main.py                    # ✅ MODIFICADO: Import email_sender
│   └── utils/
│       ├── __init__.py            # 🆕 NUEVO
│       └── email_sender.py        # 🆕 NUEVO (345 líneas)
├── docs/                          # 🆕 NUEVO directorio
│   ├── manual_usuario.md          # 🆕 600+ líneas
│   ├── guia_instalacion.md        # 🆕 450+ líneas
│   ├── EMAIL_SYSTEM_STATUS.md     # 🆕 Docs técnica
│   └── README_CONVERSION.md       # 🆕 Instrucciones PDF
├── .env                           # ✅ MODIFICADO: SMTP_*
├── .env.example                   # ✅ MODIFICADO: smtp.zoho.eu
├── docker-compose-v2.1.0.yml      # ✅ MODIFICADO: Volume /app/docs
├── CHANGELOG.md                   # ✅ MODIFICADO: Email system section
└── RESUMEN_IMPLEMENTACION.md      # 🆕 Testing completo
```

---

## 🎯 PRÓXIMOS PASOS SUGERIDOS

### Opción A: Testing Inmediato (17 min)

Seguir guía completa en `RESUMEN_IMPLEMENTACION.md` (8 pasos)

### Opción B: Producción Directa (Skip testing)

Si confías en el código y solo quieres deployar:

```bash
# 1. Configurar password
echo "SMTP_PASSWORD=tu_app_password" >> .env

# 2. Convertir PDFs online (3 min)
# https://www.markdowntopdf.com/

# 3. Commit todo
git add .
git commit -m "feat: Automatic email system with GDPR compliance"
git push origin dev

# 4. Deploy
docker compose -f docker-compose-v2.1.0.yml up -d --build
```

### Opción C: Política GDPR Primero (Deferred)

Si prefieres completar la política de privacidad antes:

1. Contactar departamento legal
2. Obtener información de compliance
3. Crear `docs/politica_privacidad_GDPR.md`
4. Convertir a PDF
5. Descomentar líneas en `email_sender.py` para adjuntar

---

## 📚 DOCUMENTACIÓN DISPONIBLE

| Archivo | Propósito |
|---------|-----------|
| `RESUMEN_IMPLEMENTACION.md` | Testing paso a paso (30 min) |
| `docs/EMAIL_SYSTEM_STATUS.md` | Documentación técnica completa |
| `docs/README_CONVERSION.md` | Conversión Markdown → PDF |
| `docs/manual_usuario.md` | Manual completo del usuario |
| `docs/guia_instalacion.md` | Guía de instalación |
| `CHANGELOG.md` | Features implementadas v2.1.0 |

---

## ❓ FAQ

**P: ¿Puedo usar Gmail en vez de Zoho?**  
R: Sí, cambiar en `.env`:
```properties
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu_email@gmail.com
SMTP_PASSWORD=app_password_de_gmail
```
Generar app password: https://myaccount.google.com/apppasswords

**P: ¿Qué pasa si no tengo los PDFs?**  
R: El email se envía igualmente sin adjuntos. Los PDFs son opcionales pero altamente recomendados.

**P: ¿Cómo veo los logs de emails?**  
R:
```bash
docker exec rhinometric-license-server-v2 cat /app/logs/license_mail.log
```

**P: ¿Cómo probar sin enviar emails reales?**  
R: Configurar SMTP de testing:
```properties
SMTP_HOST=smtp.mailtrap.io  # Testing SMTP
SMTP_PORT=2525
SMTP_USER=tu_user_mailtrap
SMTP_PASSWORD=tu_pass_mailtrap
```
Emails aparecen en https://mailtrap.io/ (no se envían a clientes reales).

**P: ¿Dónde está la política de privacidad GDPR?**  
R: Deferred por usuario ("LO DEJAMOS PARA LUEGO"). Banner genérico de GDPR incluido en email. Para compliance completo, consultar legal y crear `politica_privacidad_GDPR.pdf`.

**P: ¿Cuántos emails se pueden enviar al día?**  
R: Límites Zoho:
- Free: 250 emails/día
- Mail Lite: 1,000 emails/día  
- Mail Premium: 5,000 emails/día

Para más, considerar SendGrid o AWS SES.

---

## 🆘 TROUBLESHOOTING RÁPIDO

### Error: `email_sent: false`

```bash
# Ver error exacto
docker logs rhinometric-license-server-v2 --tail 30 | grep ERROR

# Si dice "535 Authentication Failed":
# → Verificar SMTP_PASSWORD es app password (NO password principal)
```

### Error: "PDF not found"

```bash
# Verificar PDFs existen
ls -lh docs/*.pdf

# Si no existen, convertir:
cd docs/
pandoc manual_usuario.md -o manual_usuario.pdf --toc --pdf-engine=xelatex
pandoc guia_instalacion.md -o guia_instalacion.pdf --toc --pdf-engine=xelatex
```

### Email en carpeta Spam

```
1. Revisar carpeta Spam/Junk
2. Marcar como "No es spam"
3. Agregar rafael.canelon@rhinometric.com a contactos
```

---

## ✅ CHECKLIST FINAL

Antes de considerar el sistema 100% completo:

- [ ] SMTP_PASSWORD configurado en `.env`
- [ ] PDFs convertidos (`manual_usuario.pdf`, `guia_instalacion.pdf`)
- [ ] License Server reiniciado
- [ ] `curl POST` retorna `"email_sent": true`
- [ ] Email recibido con HTML renderizado
- [ ] Adjuntos PDF descargables

**Si todos ✅ → Sistema LISTO PARA PRODUCCIÓN** 🎉

---

**© 2025 Rhinometric - Email System v2.1.0**

📞 Soporte: soporte@rhinometric.com  
🐙 GitHub: https://github.com/Rafael2712/mi-proyecto  
📖 Docs: `docs/EMAIL_SYSTEM_STATUS.md`
