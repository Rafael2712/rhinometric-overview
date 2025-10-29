# 🦏 Rhinometric v2.1.0 - Oracle Cloud Deployment

Infraestructura como código (IaC) con Terraform para desplegar Rhinometric en **Oracle Cloud Infrastructure (OCI)**.

---

## 📋 Requisitos Previos

### 1. Cuenta de Oracle Cloud

- ✅ **Free Tier**: Suficiente para trial (incluye 2 VMs E4.Flex con 4 OCPU cada una GRATIS)
- ✅ **Paid Account**: Para producción con más recursos

**Crear cuenta**: https://www.oracle.com/cloud/free/

### 2. Software Requerido

```bash
# Terraform (ya instalado)
terraform --version  # v1.12.2+

# Oracle Cloud CLI (opcional, pero recomendado)
# Windows: https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/cliinstall.htm
bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)"

# Verificar instalación
oci --version
```

### 3. SSH Key

```bash
# Generar SSH key si no tienes una
ssh-keygen -t rsa -b 4096 -C "rhinometric@oracle" -f ~/.ssh/oci_rsa

# Verificar
ls ~/.ssh/oci_rsa*
# Debes ver: oci_rsa (private) y oci_rsa.pub (public)
```

---

## 🔑 Configuración de Oracle Cloud

### Paso 1: Crear API Key

1. Login en Oracle Cloud: https://cloud.oracle.com/
2. Click en **Profile** (esquina superior derecha)
3. Click en **User Settings**
4. En el menú izquierdo, click **API Keys**
5. Click **Add API Key**
6. Select **Generate API Key Pair**
7. Click **Download Private Key** (guardar como `~/.oci/oci_api_key.pem`)
8. Click **Download Public Key** (opcional, para backup)
9. Click **Add**
10. **Copiar el fingerprint** que se muestra (ejemplo: `aa:bb:cc:dd:...`)

### Paso 2: Obtener OCIDs

**Tenancy OCID**:
1. Profile → **Tenancy: <nombre>**
2. Copiar **OCID** (comienza con `ocid1.tenancy.oc1..`)

**User OCID**:
1. Profile → **User Settings**
2. Copiar **OCID** (comienza con `ocid1.user.oc1..`)

**Región**:
1. Verificar región actual en la esquina superior derecha
2. Ejemplo: `US East (Ashburn)` = `us-ashburn-1`

---

## 🚀 Despliegue

### Paso 1: Configurar Variables

```bash
# Navegar al directorio
cd terraform/oracle-cloud

# Copiar ejemplo de variables
cp terraform.tfvars.example terraform.tfvars

# Editar con tus credenciales
nano terraform.tfvars
# O: code terraform.tfvars
```

**Completar con tus valores**:

```hcl
tenancy_ocid     = "ocid1.tenancy.oc1..aaaaaa..."  # Del Paso 2
user_ocid        = "ocid1.user.oc1..aaaaaa..."     # Del Paso 2
fingerprint      = "aa:bb:cc:dd:ee:ff:..."         # Del Paso 1
private_key_path = "~/.oci/oci_api_key.pem"        # Ruta a private key
region           = "us-ashburn-1"                  # Tu región

ssh_public_key_path = "~/.ssh/oci_rsa.pub"        # Tu SSH public key

# CAMBIAR passwords por valores seguros
grafana_admin_password = "YourSecurePasswordHere"  # Change this to a strong password
postgres_password      = "PostgresSeguro456!"
redis_password         = "RedisSeguro789!"
```

**IMPORTANTE**: `terraform.tfvars` está en `.gitignore`. NUNCA hacer commit de este archivo.

### Paso 2: Inicializar Terraform

```bash
# Descargar provider de Oracle Cloud
terraform init

# Verificar sintaxis
terraform validate
```

### Paso 3: Planificar Deployment

```bash
# Ver qué recursos se crearán
terraform plan

# Salida esperada:
# Plan: 7 to add, 0 to change, 0 to destroy.
#
# Recursos a crear:
# - oci_core_vcn.rhinometric_vcn
# - oci_core_internet_gateway.rhinometric_igw
# - oci_core_route_table.rhinometric_route_table
# - oci_core_security_list.rhinometric_security_list
# - oci_core_subnet.rhinometric_subnet
# - oci_core_instance.rhinometric_instance
```

### Paso 4: Aplicar (Crear Recursos)

```bash
# Crear infraestructura
terraform apply

# Confirmar con: yes

# Tiempo estimado: 3-5 minutos
```

**Salida al finalizar**:

```
Apply complete! Resources: 7 added, 0 changed, 0 destroyed.

Outputs:

grafana_url = "http://XXX.XXX.XXX.XXX:3000"
public_ip = "XXX.XXX.XXX.XXX"
ssh_command = "ssh ubuntu@XXX.XXX.XXX.XXX"
installation_instructions = <<EOT

========================================
🦏 RHINOMETRIC v2.1.0 - DEPLOYMENT INFO
========================================

📍 Región: us-ashburn-1
💻 Instance: VM.Standard.E4.Flex (4 OCPU, 16 GB RAM)
🌐 IP Pública: XXX.XXX.XXX.XXX

⏳ La instalación automática toma ~15 minutos.

...
EOT
```

### Paso 5: Monitorear Instalación

La VM ejecuta automáticamente el script `user-data.sh` que:
1. Actualiza el sistema
2. Instala Docker
3. Clona el repositorio
4. Configura `.env`
5. Descarga imágenes Docker (2.5 GB)
6. Levanta los 17 contenedores

```bash
# Conectarse por SSH
ssh ubuntu@<PUBLIC_IP>

# Ver progreso de instalación
tail -f /var/log/cloud-init-output.log

# Esperar hasta ver:
# "🦏 RHINOMETRIC v2.1.0 - LISTO!"
```

### Paso 6: Verificar Deployment

```bash
# Dentro de la VM (via SSH)

# Ver contenedores
docker ps | grep rhinometric
# Debe mostrar 17 contenedores "Up" o "Up (healthy)"

# Ver logs
cd /home/ubuntu/mi-proyecto/infrastructure/mi-proyecto/rhinometric-trial-v2.1.0-universal
docker compose -f docker-compose-v2.1.0.yml logs -f grafana

# Health checks
curl http://localhost:3000/api/health
# {"database":"ok","version":"10.4.0"}

curl http://localhost:9090/-/healthy
# Prometheus is Healthy.
```

### Paso 7: Acceder a Grafana

1. Abrir navegador
2. Ir a: `http://<PUBLIC_IP>:3000`
3. Login:
   - **Usuario**: `admin`
   - **Password**: (el que pusiste en `terraform.tfvars`)
4. Explorar dashboards en **Dashboards** → **Browse**
5. Ver **System Overview**, **External APIs**, etc.

---

## 🔧 Gestión de Recursos

### Ver Estado

```bash
# Ver recursos creados
terraform show

# Ver outputs
terraform output

# Ver IP pública
terraform output public_ip

# Ver URL de Grafana
terraform output grafana_url
```

### Modificar Recursos

```bash
# Editar variables (ej: aumentar RAM)
nano terraform.tfvars
# Cambiar: instance_memory_in_gbs = 32

# Aplicar cambios
terraform apply
```

### Detener Instancia (sin destruir)

```bash
# Detener VM (para ahorrar costos de CPU, el disco sigue cobrando)
oci compute instance action --instance-id <INSTANCE_OCID> --action STOP

# Iniciar nuevamente
oci compute instance action --instance-id <INSTANCE_OCID> --action START
```

### Destruir TODOS los Recursos

```bash
# ⚠️ IMPORTANTE: Esto elimina TODO (VM, VCN, discos)
terraform destroy

# Confirmar con: yes

# Tiempo: 2-3 minutos
```

---

## 💰 Costos Estimados

### Oracle Cloud Free Tier

**GRATIS durante 12 meses**:
- ✅ 2 VMs **VM.Standard.E4.Flex** (4 OCPU, 24 GB RAM cada una)
- ✅ 200 GB Block Storage
- ✅ 10 TB/mes tráfico saliente

**Para Rhinometric**:
- ✅ **1 VM** (4 OCPU, 16 GB RAM) = **GRATIS** ✅
- ✅ **100 GB disco** = **GRATIS** ✅
- ✅ Tráfico normal < 10 TB = **GRATIS** ✅

### Oracle Cloud Paid (después de Free Tier)

**Costos aproximados** (región us-ashburn-1):

| Recurso | Especificación | Costo/mes |
|---------|---------------|-----------|
| Compute | VM.Standard.E4.Flex (4 OCPU, 16 GB) | ~$60 |
| Storage | 100 GB Block Storage | ~$2.5 |
| Network | Tráfico saliente (primeros 10 TB gratis) | $0 |
| **TOTAL** | | **~$62/mes** |

**Comparación con otras clouds**:

| Cloud Provider | Instancia | RAM | Disco | Costo/mes |
|---------------|-----------|-----|-------|-----------|
| Oracle Cloud | E4.Flex (4 OCPU) | 16 GB | 100 GB | **~$62** |
| AWS EC2 | t3.xlarge (4 vCPU) | 16 GB | 100 GB | ~$120 |
| Azure | D4s_v3 (4 vCPU) | 16 GB | 100 GB | ~$140 |
| Google Cloud | n2-standard-4 (4 vCPU) | 16 GB | 100 GB | ~$110 |

**Oracle Cloud es ~50% más barato** que AWS/Azure/GCP.

---

## 🐛 Troubleshooting

### Error: "Service error: NotAuthorizedOrNotFound"

**Causa**: Credenciales incorrectas o permisos insuficientes.

**Solución**:
```bash
# Verificar configuración OCI CLI
cat ~/.oci/config

# Verificar que el fingerprint coincida
oci iam user api-key list --user-id <USER_OCID>

# Re-configurar si es necesario
oci setup config
```

### Error: "Out of host capacity"

**Causa**: No hay capacidad disponible en la Availability Domain.

**Solución**:
```hcl
# Cambiar a otra Availability Domain
# En variables.tf, cambiar:
availability_domain = "AD-2"  # o AD-3
```

### Error: "LimitExceeded"

**Causa**: Has alcanzado el límite de recursos de Free Tier.

**Solución**:
1. Ir a: https://cloud.oracle.com/ → **Governance** → **Limits, Quotas and Usage**
2. Verificar límites de Compute y Storage
3. Solicitar aumento de límite o upgrade a Paid Account

### Instalación automática falla

**Verificar**:
```bash
# SSH a la VM
ssh ubuntu@<PUBLIC_IP>

# Ver logs completos
sudo cat /var/log/cloud-init-output.log

# Ver logs de Docker pull
cat /var/log/rhinometric-pull.log

# Ver logs de inicio
cat /var/log/rhinometric-start.log

# Re-ejecutar instalación manualmente
cd /home/ubuntu/mi-proyecto/infrastructure/mi-proyecto/rhinometric-trial-v2.1.0-universal
docker compose -f docker-compose-v2.1.0.yml up -d
```

### No puedo acceder a Grafana

**Verificar**:

1. **Security List** permite puerto 3000:
   ```bash
   # En Oracle Cloud Console:
   # Networking → Virtual Cloud Networks → rhinometric-vcn
   # → Security Lists → rhinometric-security-list
   # → Ingress Rules → Debe haber regla para TCP 3000
   ```

2. **Firewall de la VM**:
   ```bash
   # Dentro de la VM
   sudo ufw status
   # Si está activo, agregar regla:
   sudo ufw allow 3000/tcp
   ```

3. **Grafana está corriendo**:
   ```bash
   docker ps | grep grafana
   curl http://localhost:3000/api/health
   ```

---

## 📊 Arquitectura Desplegada

```
┌──────────────────────────────────────────────────────────┐
│                   ORACLE CLOUD (OCI)                     │
│                                                           │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Virtual Cloud Network (VCN)                       │  │
│  │  CIDR: 10.0.0.0/16                                 │  │
│  │                                                     │  │
│  │  ┌──────────────────────────────────────────────┐  │  │
│  │  │  Public Subnet (10.0.1.0/24)                 │  │  │
│  │  │                                               │  │  │
│  │  │  ┌─────────────────────────────────────────┐ │  │  │
│  │  │  │  VM.Standard.E4.Flex                    │ │  │  │
│  │  │  │  - 4 OCPU (vCPU)                        │ │  │  │
│  │  │  │  - 16 GB RAM                             │ │  │  │
│  │  │  │  - 100 GB SSD                            │ │  │  │
│  │  │  │  - Ubuntu 22.04 LTS                      │ │  │  │
│  │  │  │                                          │ │  │  │
│  │  │  │  🦏 Rhinometric v2.1.0                   │ │  │  │
│  │  │  │  └─ 17 Docker containers                │ │  │  │
│  │  │  │     ├─ Grafana :3000                    │ │  │  │
│  │  │  │     ├─ Prometheus :9090                 │ │  │  │
│  │  │  │     ├─ API Connector :8091              │ │  │  │
│  │  │  │     └─ ... (14 más)                     │ │  │  │
│  │  │  └─────────────────────────────────────────┘ │  │  │
│  │  │                                               │  │  │
│  │  └───────────────────────┬───────────────────────┘  │  │
│  │                          │                           │  │
│  │                ┌─────────▼──────────┐                │  │
│  │                │  Internet Gateway  │                │  │
│  │                └─────────┬──────────┘                │  │
│  └──────────────────────────┼────────────────────────────┘  │
│                             │                              │
└─────────────────────────────┼──────────────────────────────┘
                              │
                              ▼
                         INTERNET
                              │
                              ▼
                    👤 TÚ (http://PUBLIC_IP:3000)
```

---

## ✅ Checklist Post-Deployment

- [ ] VM creada exitosamente
- [ ] SSH funciona: `ssh ubuntu@<PUBLIC_IP>`
- [ ] 17 contenedores corriendo: `docker ps | grep rhinometric`
- [ ] Grafana accesible: `http://<PUBLIC_IP>:3000`
- [ ] Prometheus accesible: `http://<PUBLIC_IP>:9090`
- [ ] API Connector accesible: `http://<PUBLIC_IP>:8091`
- [ ] Dashboards visibles en Grafana
- [ ] Métricas aparecen en Prometheus: `up{job="prometheus"}`
- [ ] Logs aparecen en Loki (Grafana → Explore → Loki)
- [ ] **CRÍTICO**: Ejecutar `terraform destroy` cuando termines para evitar costos

---

## 📚 Próximos Pasos

1. **Configurar dominio** (opcional):
   - Apuntar `monitoring.tudominio.com` a la IP pública
   - Configurar SSL con Let's Encrypt (ver nginx.conf)

2. **Agregar APIs externas**:
   - Acceder a `http://<PUBLIC_IP>:8091`
   - Click en **"+ Add API"**
   - Agregar Stripe, AWS, OpenAI, etc.

3. **Configurar alertas**:
   - Grafana → Alerting → Contact Points
   - Agregar Slack, Email, PagerDuty

4. **Backup**:
   - Configurar snapshot automático de Boot Volume
   - Exportar dashboards: Grafana → Settings → JSON Model

5. **Monitoreo**:
   - Revisar dashboards diariamente
   - Configurar alertas críticas (CPU, disco, latencia)

---

## 🆘 Soporte

- 📖 **Docs**: Carpeta `../../docs/`
- 🐙 **Issues**: https://github.com/Rafael2712/mi-proyecto/issues
- 📧 **Email**: support@rhinometric.io

---

**✅ Rhinometric v2.1.0 - Oracle Cloud Ready!**

**Creado**: Terraform v1.12.2 | **OS**: Ubuntu 22.04 LTS | **Cloud**: Oracle Cloud Infrastructure
