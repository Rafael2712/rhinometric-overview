# 🚀 RHINOMETRIC TEST SERVER - DESPLEGADO EXITOSAMENTE

**Fecha de Despliegue:** 22 de Diciembre, 2025  
**Versión:** v2.5.0  
**Estado:** ✅ OPERATIVO

---

## 📊 INFORMACIÓN DE LA INSTANCIA

| Parámetro | Valor |
|-----------|-------|
| **Instance ID** | i-093a9c12ca99bf4d7 |
| **IP Pública (EIP)** | 100.51.216.214 |
| **DNS Público** | ec2-100-51-216-214.compute-1.amazonaws.com |
| **Tipo** | EC2 t3.xlarge **Spot** |
| **vCPUs** | 4 |
| **RAM** | 16 GB |
| **Región** | us-east-1 (Virginia) |
| **Zona** | us-east-1b |
| **AMI** | Ubuntu 22.04 LTS (ami-0c7217cdde317cfec) |
| **Key Pair** | rhinometric-test-key |

---

## 💾 ALMACENAMIENTO

| Volumen | Tipo | Tamaño | IOPS | Throughput | Montaje |
|---------|------|--------|------|------------|---------|
| **Root** | gp3 | 30 GB | 3000 | 125 MB/s | / |
| **Data** | gp3 | 150 GB | 3000 | 125 MB/s | /mnt/rhinometric-data |

**Volume ID:** vol-0e2c635d8d072512a

---

## 🔐 SEGURIDAD

**Security Group:** sg-04ce3cdd00dd4d171

### Puertos Abiertos:

| Puerto | Servicio | Propósito |
|--------|----------|-----------|
| 22 | SSH | Acceso administrativo |
| 80 | HTTP | Nginx (entrada principal) |
| 443 | HTTPS | Nginx HTTPS |
| 3000 | Grafana | Acceso directo para pruebas |
| 3002 | Console Frontend | **UI Principal de Rhinometric** |
| 9090 | Prometheus | Métricas y queries |
| 16686 | Jaeger UI | Distributed tracing |

---

## 🌐 URLs DE ACCESO

| Servicio | URL |
|----------|-----|
| **Console UI (Principal)** | http://100.51.216.214:3002 |
| **Nginx** | http://100.51.216.214 |
| **Grafana** | http://100.51.216.214:3000 |
| **Prometheus** | http://100.51.216.214:9090 |
| **Jaeger** | http://100.51.216.214:16686 |

---

## 💰 COSTOS ESTIMADOS

| Concepto | Precio/hora | Precio/mes | Ahorro |
|----------|-------------|------------|--------|
| **Spot (actual)** | $0.08 | **~$35-45** | 52% |
| On-Demand | $0.17 | ~$132 | - |

**Costo para 3 semanas de pruebas:** ~$26-34 USD

---

## 🔑 ACCESO SSH

```bash
ssh -i ~/.ssh/rhinometric-test-key.pem ubuntu@100.51.216.214
```

**Ubicación de la clave:** `~/.ssh/rhinometric-test-key.pem`

---

## ⚙️ SOFTWARE INSTALADO

✅ **Docker** - v29.1.3  
✅ **Docker Compose** - v5.0.0  
✅ **Git, Curl, Wget, Htop, Vim, Jq** - Herramientas básicas  

### Optimizaciones Aplicadas:

- **vm.max_map_count=262144** (requerido para Grafana/Elasticsearch)
- **fs.file-max=65536** (límite de archivos abiertos)
- **Docker logging:** JSON driver, max 10MB x 3 archivos
- **Storage driver:** overlay2

---

## 📂 ESTRUCTURA DE DATOS

```
/home/ubuntu/
├── rhinometric_data_v2.2/          # Datos persistentes
│   ├── postgres/                    # Base de datos
│   ├── redis/                       # Cache
│   ├── loki/                        # Logs
│   ├── jaeger/                      # Traces
│   ├── prometheus/                  # Métricas
│   ├── grafana/                     # Dashboards
│   ├── ai-anomaly/                  # Modelos IA
│   └── ...
└── rhinometric_backups/            # Backups automáticos
```

---

## 📋 PRÓXIMOS PASOS (FASE 1.1)

### 1. Transferir Archivos del Proyecto

**Opción A: Rsync (recomendado)**
```bash
rsync -avz --progress \
  -e "ssh -i ~/.ssh/rhinometric-test-key.pem" \
  --exclude='node_modules' \
  --exclude='__pycache__' \
  --exclude='.git' \
  /c/Users/canel/mi-proyecto/infrastructure/mi-proyecto/ \
  ubuntu@100.51.216.214:~/rhinometric-v2.5.0/
```

**Opción B: Tar + SCP**
```bash
cd /c/Users/canel/mi-proyecto/infrastructure/mi-proyecto
tar czf rhinometric-v2.5.0.tar.gz \
  --exclude='node_modules' \
  --exclude='__pycache__' \
  --exclude='.git' \
  --exclude='terraform/.terraform' \
  .

scp -i ~/.ssh/rhinometric-test-key.pem \
  rhinometric-v2.5.0.tar.gz \
  ubuntu@100.51.216.214:~/

# En el servidor:
ssh -i ~/.ssh/rhinometric-test-key.pem ubuntu@100.51.216.214
tar xzf rhinometric-v2.5.0.tar.gz
mv mi-proyecto rhinometric-v2.5.0
```

### 2. Crear Archivo .env

```bash
ssh -i ~/.ssh/rhinometric-test-key.pem ubuntu@100.51.216.214

cd ~/rhinometric-v2.5.0
cat > .env <<'EOF'
# Database Credentials
POSTGRES_PASSWORD=rhinometric_secure_2024
REDIS_PASSWORD=redis_secure_2024

# Grafana Credentials
GRAFANA_USER=admin
GRAFANA_PASSWORD=RhinoAdmin2024!

# Console Credentials
ADMIN_USERNAME=admin
ADMIN_PASSWORD=ConsoleAdmin2024!
SECRET_KEY=$(openssl rand -base64 32)

# SMTP Configuration
SMTP_HOST=smtp.zoho.eu
SMTP_PORT=587
SMTP_USER=rafael.canelon@rhinometric.com
SMTP_PASSWORD=<TU_PASSWORD_SMTP>
SMTP_FROM=rafael.canelon@rhinometric.com
ALERT_EMAIL_TO=rafael.canelon@rhinometric.com

# JWT Secret
JWT_SECRET=$(openssl rand -base64 32)

# Timezone
TZ=Europe/Madrid
EOF
```

### 3. Desplegar Stack Core

```bash
cd ~/rhinometric-v2.5.0
docker compose -f docker-compose-v2.5.0-core.yml pull
docker compose -f docker-compose-v2.5.0-core.yml build
docker compose -f docker-compose-v2.5.0-core.yml up -d
```

### 4. Monitorear Logs

```bash
docker compose -f docker-compose-v2.5.0-core.yml logs -f
```

---

## 🛠️ COMANDOS ÚTILES

### Verificar estado de servicios
```bash
docker compose -f docker-compose-v2.5.0-core.yml ps
```

### Ver logs de un servicio específico
```bash
docker logs -f rhinometric-console-frontend
docker logs -f rhinometric-grafana
```

### Verificar recursos del servidor
```bash
htop              # CPU y RAM
df -h             # Disco
docker stats      # Recursos de containers
```

### Reiniciar servicios
```bash
docker compose -f docker-compose-v2.5.0-core.yml restart
```

### Detener todo
```bash
docker compose -f docker-compose-v2.5.0-core.yml down
```

---

## 🧹 LIMPIEZA (Cuando termines las pruebas)

```bash
# Desde tu máquina local
cd /c/Users/canel/mi-proyecto/infrastructure/mi-proyecto/terraform
terraform destroy -auto-approve
```

Esto eliminará:
- ✅ Instancia EC2 Spot
- ✅ Elastic IP
- ✅ Volumen EBS (⚠️ perderás datos)
- ✅ Security Group
- ✅ Spot Request

---

## 📝 NOTAS IMPORTANTES

1. **Spot Instance:** Puede ser interrumpida por AWS con 2 min de aviso (probabilidad baja ~10%)
2. **IP Elástica:** Mantiene la misma IP aunque se recree la instancia
3. **Volumen EBS:** Los datos persisten aunque se detenga la instancia
4. **Costos:** ~$0.08/hora = ~$1.92/día = ~$35-45/mes
5. **Terraform State:** Guardado localmente en `terraform/terraform.tfstate`

---

**Generado por:** Terraform  
**Timestamp:** 2025-12-22 10:39:14 UTC  
**Stack Version:** Rhinometric v2.5.0 Core (17 servicios)
