# SaaS Monitoring Platform - Oracle Cloud Edition

Complete observability and monitoring platform optimized for Oracle Cloud Free Tier with multi-tenancy support.

## 🚀 Quick Start

### Prerequisites

- Oracle Cloud Account with Free Tier access
- Terraform >= 1.0
- SSH key pair
- OCI CLI (recommended but optional)

### 1-Minute Deployment

```bash
cd terraform
./deploy.sh --auto
```

Follow the prompts to configure your Oracle Cloud credentials and deploy!

## 📋 Architecture Overview

### Services Deployed

| Service | Purpose | Port | Resource Limits |
|---------|---------|------|-----------------|
| **PostgreSQL** | Multi-tenant database | 5432 | 2GB RAM |
| **PgBouncer** | Connection pooling | 6432 | 256MB RAM |
| **Prometheus** | Metrics collection | 9090 | 3GB RAM |
| **Grafana** | Visualization & dashboards | 3000 | 2GB RAM |
| **Loki** | Log aggregation | 3100 | 2GB RAM |
| **Alertmanager** | Alert routing | 9093 | 512MB RAM |
| **Redis** | Caching & sessions | 6379 | 1GB RAM |
| **License Server** | SaaS licensing | 8080 | 512MB RAM |
| **Nginx** | Reverse proxy & SSL | 80/443 | 256MB RAM |

### Infrastructure

- **Oracle Cloud Free Tier**: VM.Standard.A1.Flex (4 vCPUs, 24GB RAM)
- **Storage**: 50GB block volume + 47GB boot volume
- **Network**: VCN with public subnet and internet gateway
- **Security**: Firewall rules for required ports only

## 🔧 Configuration

### Oracle Cloud Setup

1. **Create API Key**:
   ```bash
   openssl genrsa -out ~/.oci/oci_api_key.pem 2048
   openssl rsa -pubout -in ~/.oci/oci_api_key.pem -out ~/.oci/oci_api_key_public.pem
   ```

2. **Add Public Key** to OCI Console → User Profile → API Keys

3. **Get Required OCIDs**:
   - Tenancy OCID: Console → Administration → Tenancy Details
   - User OCID: Console → Identity → Users → Your Profile
   - Compartment OCID: Console → Identity → Compartments

### SSH Key Setup

```bash
ssh-keygen -t rsa -b 4096 -f ~/.ssh/oci_key
```

### Configuration Files

The deployment uses these configuration files:

- `terraform.tfvars` - Oracle Cloud credentials and settings
- `docker-compose-saas-minimal.yml` - Optimized service stack
- `.env.saas` - Environment variables for services
- `cloud-init.yaml` - Automated server setup script

## 📦 Deployment Options

### Interactive Deployment

```bash
cd terraform
./deploy.sh
```

Choose from menu options:
1. **Full deployment** - Complete setup from scratch
2. **Initialize only** - Setup Terraform
3. **Validate** - Check configuration
4. **Plan** - Preview changes
5. **Deploy** - Apply infrastructure
6. **Status** - Check current state
7. **Destroy** - Remove all resources

### Manual Deployment

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your OCI settings

terraform init
terraform validate
terraform plan -out=tfplan
terraform apply tfplan
```

## 🌐 Multi-Tenancy Features

### Database Isolation

- **Schema-based tenancy**: Each tenant gets dedicated PostgreSQL schema
- **Connection pooling**: PgBouncer manages connections per tenant
- **Data isolation**: Complete separation of tenant data

### Grafana Organizations

- **Tenant organizations**: Automatic org creation for new tenants
- **Isolated dashboards**: Tenant-specific dashboard sets
- **User management**: Per-tenant user access control

### License Management

Built-in licensing system with:
- **Tenant registration**: API-based tenant onboarding
- **Usage tracking**: Monitor resource consumption per tenant
- **License validation**: Enforce tenant limits and features

## 🔍 Monitoring & Observability

### Default Dashboards

Pre-configured Grafana dashboards for:
- **Infrastructure metrics**: CPU, memory, disk, network
- **Application performance**: Response times, error rates
- **Multi-tenant analytics**: Per-tenant resource usage
- **System health**: Service status and availability

### Alerting

Alertmanager configured with:
- **Resource alerts**: High CPU/memory usage
- **Service alerts**: Container failures
- **Tenant alerts**: Per-tenant thresholds
- **Escalation policies**: Multi-channel notifications

### Log Management

Loki integration provides:
- **Centralized logging**: All service logs in one place
- **Log correlation**: Link logs to metrics and traces
- **Tenant filtering**: View logs by tenant ID
- **Query capabilities**: Advanced log search and analysis

## 🔒 Security Features

### Network Security

- **Firewall rules**: Only required ports exposed (22, 80, 443, 3000, 9090-9093)
- **VPC isolation**: Private network for internal communication
- **SSH access**: Key-based authentication only

### Application Security

- **Database security**: Password-protected with connection pooling
- **Grafana auth**: Secure admin credentials with org isolation
- **License validation**: API key authentication for tenant operations
- **SSL/TLS ready**: Nginx configured for certificate deployment

## 📊 Performance Optimization

### Resource Allocation

Optimized for Oracle Cloud Free Tier:
- **CPU limits**: Prevents resource exhaustion
- **Memory limits**: Ensures stable operation within 24GB
- **Storage optimization**: Efficient disk usage patterns

### Caching Strategy

- **Redis caching**: Session and query result caching
- **Prometheus retention**: Optimized metrics storage
- **Log rotation**: Automatic cleanup of old logs

## 🛠 Operations & Maintenance

### Health Checks

Monitor deployment health:

```bash
# SSH to server
ssh opc@YOUR_PUBLIC_IP

# Check service status
docker-compose -f /opt/saas-platform/docker-compose.yml ps

# View logs
docker-compose -f /opt/saas-platform/docker-compose.yml logs

# Restart services
docker-compose -f /opt/saas-platform/docker-compose.yml restart
```

### Backup Strategy

Automated backups include:
- **Database dumps**: PostgreSQL automated backups
- **Configuration backup**: All config files preserved
- **Grafana dashboards**: Export/import capability
- **Block storage**: Oracle Cloud automatic snapshots

### Scaling Options

When ready to scale beyond Free Tier:
- **Vertical scaling**: Increase VM size (more CPU/RAM)
- **Horizontal scaling**: Add more VM instances
- **Database scaling**: Move to managed Oracle Database
- **Load balancing**: Add Oracle Load Balancer

## 📈 SaaS Features

### Tenant Management API

```bash
# Register new tenant
curl -X POST http://YOUR_IP:8080/api/tenants \
  -H "Content-Type: application/json" \
  -d '{"name": "acme-corp", "plan": "standard"}'

# Get tenant info
curl http://YOUR_IP:8080/api/tenants/acme-corp

# Update tenant limits
curl -X PUT http://YOUR_IP:8080/api/tenants/acme-corp \
  -H "Content-Type: application/json" \
  -d '{"metrics_retention_days": 30, "max_users": 10}'
```

### Usage Analytics

Built-in analytics for:
- **Resource consumption**: CPU, memory, storage per tenant
- **API usage**: Request counts and patterns
- **User activity**: Login patterns and dashboard usage
- **Cost allocation**: Resource costs per tenant

## 🎯 Use Cases

### Managed Service Provider (MSP)
- Monitor multiple client infrastructures
- Isolated dashboards per client
- Centralized alerting with client-specific rules
- Scalable licensing model

### SaaS Application Monitoring
- Multi-tenant application observability
- Customer-specific dashboards
- Usage-based billing integration
- Self-service analytics portal

### Enterprise Multi-Environment
- Development/staging/production monitoring
- Team-based access control
- Environment-specific alerting
- Compliance reporting

## 🔄 Upgrade Path

### From Local to Cloud

Already running locally? Migrate easily:

1. **Export data**: Backup existing Grafana dashboards and Prometheus data
2. **Deploy cloud**: Use this Oracle Cloud setup
3. **Import data**: Restore dashboards and configure data sources
4. **Update endpoints**: Point applications to new cloud endpoints

### Cost Optimization

- **Start free**: Use Oracle Cloud Free Tier (always free)
- **Scale gradually**: Add paid resources as needed
- **Monitor costs**: Built-in usage tracking
- **Optimize resources**: Right-size based on actual usage

## 📚 Additional Resources

- [Oracle Cloud Free Tier](https://www.oracle.com/cloud/free/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Prometheus Configuration](https://prometheus.io/docs/)
- [Multi-tenancy Best Practices](https://grafana.com/blog/2021/02/09/how-to-configure-grafana-as-code/)

## 🤝 Support

### Troubleshooting

Common issues and solutions:

1. **Services not starting**: Check resource limits and Docker logs
2. **Cannot access Grafana**: Verify firewall rules and service status
3. **Database connection errors**: Check PostgreSQL logs and credentials
4. **High resource usage**: Review per-service resource allocation

### Getting Help

- **Documentation**: Check this README and inline comments
- **Logs**: Always check service logs first
- **Oracle Cloud Support**: For infrastructure issues
- **Community**: Grafana/Prometheus community resources

---

**Ready to deploy your SaaS monitoring platform? Run `./deploy.sh` and get started in minutes!** 🚀