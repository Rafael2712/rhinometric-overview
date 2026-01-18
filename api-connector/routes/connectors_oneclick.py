"""
RHINOMETRIC v2.5.0 - ONE-CLICK Connector Endpoint
==================================================

Universal endpoint for creating fully-automated data connectors.
Generates code, deploys services, configures monitoring, and creates dashboards.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
import asyncio
import logging
import os
import subprocess
from datetime import datetime

from services.code_generator import CodeGenerator, ServiceDeployer, DockerComposeManager, PrometheusConfigManager
from services.dashboard_generator import DashboardGenerator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/connectors", tags=["connectors"])

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class ConnectorConfigBase(BaseModel):
    name: str = Field(..., description="Connection name")
    enabled: bool = Field(True, description="Enable connector")
    tags: List[str] = Field(default=[], description="Tags for organization")

class RESTConnectorConfig(ConnectorConfigBase):
    connector_type: str = "rest"
    url: str = Field(..., description="API base URL")
    endpoint: str = Field(..., description="API endpoint path")
    method: str = Field("GET", description="HTTP method")
    token: Optional[str] = Field(None, description="Bearer token")
    headers: Dict[str, str] = Field(default={}, description="Custom headers")
    fetch_interval: int = Field(60, description="Fetch interval in seconds")

class MQTTConnectorConfig(ConnectorConfigBase):
    connector_type: str = "mqtt"
    broker_host: str = Field(..., description="MQTT broker hostname")
    broker_port: int = Field(1883, description="MQTT broker port")
    topics: List[str] = Field(..., description="Topics to subscribe (e.g., sensor/#)")
    username: Optional[str] = Field(None, description="MQTT username")
    password: Optional[str] = Field(None, description="MQTT password")
    client_id: str = Field("rhinometric-collector", description="MQTT client ID")
    use_tls: bool = Field(False, description="Use TLS/SSL")
    enable_demo_mode: bool = Field(False, description="Allow public brokers for demo")

class DatabaseConnectorConfig(ConnectorConfigBase):
    connector_type: str = "database"
    db_type: str = Field(..., description="Database type (postgresql, mysql)")
    db_host: str = Field(..., description="Database hostname")
    db_port: int = Field(..., description="Database port")
    db_name: str = Field(..., description="Database name")
    db_user: str = Field(..., description="Database user")
    db_password: str = Field(..., description="Database password")
    query_sql: str = Field(..., description="SQL query to execute")
    query_interval: int = Field(60, description="Query interval in seconds")

class WebhookConnectorConfig(ConnectorConfigBase):
    connector_type: str = "webhook"
    webhook_port: int = Field(8080, description="Webhook listening port")
    webhook_path: str = Field("/webhook", description="Webhook endpoint path")
    webhook_secret: Optional[str] = Field(None, description="Webhook secret for validation")

class DeploymentResult(BaseModel):
    success: bool
    message: str
    connector_name: str
    connector_type: str
    service_name: str
    dashboard_url: Optional[str]
    metrics_url: Optional[str]
    deployment_time_seconds: float
    services_deployed: List[str]
    configuration: Dict[str, Any]

# ============================================================================
# DEPLOYMENT ORCHESTRATOR
# ============================================================================

class ConnectorDeployer:
    """
    Orchestrates full connector deployment.
    """
    
    def __init__(self, project_root: str):
        self.project_root = project_root
        
        # Use environment variables for mounted paths
        compose_file = os.getenv("COMPOSE_FILE", os.path.join(project_root, "../../docker-compose-v2.5.0.yml"))
        prometheus_config = os.getenv("PROMETHEUS_CONFIG", os.path.join(project_root, "../../prometheus/prometheus.yml"))
        workspace_dir = os.getenv("WORKSPACE_DIR", os.path.join(project_root, "../.."))
        
        logger.info(f"Initializing ConnectorDeployer:")
        logger.info(f"  project_root: {project_root}")
        logger.info(f"  compose_file: {compose_file}")
        logger.info(f"  prometheus_config: {prometheus_config}")
        logger.info(f"  workspace_dir: {workspace_dir}")
        
        self.code_gen = CodeGenerator(templates_dir=os.path.join(project_root, "templates/collectors"))
        self.deployer = ServiceDeployer(project_root=workspace_dir)
        self.compose_manager = DockerComposeManager(compose_file=compose_file)
        self.prom_manager = PrometheusConfigManager(prometheus_config=prometheus_config)
        self.dashboard_gen = DashboardGenerator(
            templates_dir=os.path.join(project_root, "templates/dashboards")
        )
    
    async def deploy_connector(
        self,
        config: ConnectorConfigBase,
        db: Session
    ) -> DeploymentResult:
        """
        Full ONE-CLICK deployment of connector.
        
        Steps:
        1. Validate configuration
        2. Generate collector code
        3. Create service structure
        4. Update docker-compose.yml
        5. Configure Prometheus scraping
        6. Generate Grafana dashboard
        7. Deploy services
        8. Wait for health checks
        9. Return result
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"🚀 Starting deployment: {config.name} ({config.connector_type})")
            
            # Step 1: Validate
            self._validate_config(config)
            
            # Step 2: Get next available port (BEFORE code generation)
            metrics_port = self.deployer.get_next_available_port()
            logger.info(f"🔌 Allocated port: {metrics_port}")
            
            # Step 3: Add metrics_port to config
            config_dict = config.dict()
            config_dict['metrics_port'] = metrics_port
            
            # Step 4: Generate code with port
            logger.info("📝 Generating collector code...")
            files = self.code_gen.generate_collector(
                connector_type=config.connector_type,
                config=config_dict
            )

            # Step 5: Create service structure
            logger.info("📂 Creating service directory...")
            # Sanitize service name: only lowercase alphanumeric and hyphens (Docker Compose compatible)
            import re
            sanitized_service_name = re.sub(r'[^a-z0-9-]', '-', config.name.lower())
            sanitized_service_name = re.sub(r'-+', '-', sanitized_service_name).strip('-')
            service_name = f"{config.connector_type}-collector-{sanitized_service_name}"
            service_dir = self.deployer.create_service_structure(
                service_name=service_name,
                files=files
            )
            
            # Step 6: Update docker-compose.yml
            logger.info("🐳 Updating docker-compose.yml...")
            # Map metrics port (always) + additional ports (connector-specific)
            ports_to_map = [f"{metrics_port}:{metrics_port}"]
            logger.info(f"DEBUG: connector_type = {config.connector_type}")
            
            if config.connector_type == "webhook":
                # Webhooks need HTTP port for receiving events
                webhook_port = config.webhook_port
                ports_to_map.insert(0, f"{webhook_port}:{webhook_port}")
                logger.info(f"🪝 Webhook will listen on port {webhook_port} (ports: {ports_to_map})")
            elif config.connector_type == "database":
                # Database collectors only expose metrics (no inbound connections)
                logger.info(f"🗄️  Database collector will expose metrics on port {metrics_port}")
            
            self.compose_manager.add_service(
                service_name=service_name,
                build_path=f"./{service_name}",
                ports=ports_to_map,
                environment=self._get_env_vars(config, metrics_port),
                depends_on=["prometheus", "grafana"]
            )
            
            # Step 7: Configure Prometheus
            logger.info("📊 Configuring Prometheus scraping...")
            self.prom_manager.add_scrape_target(
                job_name=f"{config.connector_type}-{config.name}",
                target=f"{service_name}:{metrics_port}",
                scrape_interval="15s"
            )
            
            # Restart Prometheus to load new target
            logger.info("🔄 Restarting Prometheus to load new target...")
            try:
                import docker
                client = docker.from_env()
                prom_container = client.containers.get("rhinometric-prometheus")
                prom_container.restart()
                logger.info("✅ Prometheus restarted successfully")
                client.close()
                await asyncio.sleep(5)  # Wait for Prometheus to reload config
            except Exception as e:
                logger.warning(f"⚠️  Failed to restart Prometheus: {e}")
            
            # Step 8: Generate and create dashboard in Grafana via API
            logger.info("📈 Generating Grafana dashboard...")
            # Sanitize UID: only alphanumeric, hyphens, underscores
            import re
            sanitized_name = re.sub(r'[^a-z0-9-]', '-', config.name.lower())
            sanitized_name = re.sub(r'-+', '-', sanitized_name).strip('-')  # Remove duplicate hyphens
            dashboard_uid = f"{config.connector_type}-{sanitized_name}"
            # Grafana UID limit: 40 characters
            if len(dashboard_uid) > 40:
                # Truncate keeping prefix and suffix: "database-rhino...-connections" -> "db-postgres-connections"
                if config.connector_type == "database":
                    # Short prefix for database collectors
                    short_name = sanitized_name.replace('rhinometric-postgres-', '')
                    dashboard_uid = f"db-{short_name}"[:40]
                else:
                    dashboard_uid = dashboard_uid[:40].rstrip('-')
                logger.info(f"📏 UID truncated to {len(dashboard_uid)} chars: {dashboard_uid}")
            dashboard = self.dashboard_gen.generate_dashboard(
                connector_type=config.connector_type,
                datasource_name=config.name,
                datasource_uid=dashboard_uid,
                config=config.dict()
            )
            
            # Validate and fix dashboard queries (especially response time histogram)
            import json
            dashboard_str = json.dumps(dashboard)
            # Fix incorrect histogram query if present
            if 'avg(api_response_time_seconds)' in dashboard_str:
                logger.warning("⚠️  Fixing incorrect histogram query in dashboard")
                dashboard_str = dashboard_str.replace(
                    'avg(api_response_time_seconds) * 1000',
                    'rate(api_response_time_seconds_sum[5m]) / rate(api_response_time_seconds_count[5m]) * 1000'
                )
                dashboard = json.loads(dashboard_str)
            
            # Create dashboard via Grafana API instead of provisioning (so it's editable)
            logger.info("📊 Creating dashboard in Grafana via API...")
            try:
                import requests
                grafana_url = os.getenv("GRAFANA_URL", "http://grafana:3000")
                grafana_user = os.getenv("GRAFANA_USER", "admin")
                grafana_password = os.getenv("GRAFANA_PASSWORD", "demo123")
                
                # Wrap dashboard in API format
                dashboard_payload = {
                    "dashboard": dashboard,
                    "overwrite": True,
                    "message": f"Created by API Connector for {config.name}"
                }
                
                response = requests.post(
                    f"{grafana_url}/api/dashboards/db",
                    json=dashboard_payload,
                    auth=(grafana_user, grafana_password),
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                
                if response.status_code in [200, 201]:
                    logger.info(f"✅ Dashboard created successfully: {dashboard_uid}")
                else:
                    logger.warning(f"⚠️  Dashboard creation returned {response.status_code}: {response.text}")
            except Exception as e:
                logger.warning(f"⚠️  Failed to create dashboard via API: {e}. Dashboard will not be available.")
            
            # Step 9: Deploy services
            logger.info("🚀 Deploying services...")
            await self._deploy_docker_services([service_name, "prometheus", "grafana"])
            
            # Step 10: Wait for health
            logger.info("⏳ Waiting for services to be healthy...")
            await self._wait_for_healthy([service_name], timeout=60)
            
            duration = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"✅ Deployment successful in {duration:.2f}s")
            
            return DeploymentResult(
                success=True,
                message=f"{config.connector_type.upper()} connector deployed successfully",
                connector_name=config.name,
                connector_type=config.connector_type,
                service_name=service_name,
                dashboard_url=f"http://localhost:3000/d/{dashboard_uid}",
                metrics_url=f"http://localhost:{metrics_port}/metrics",
                deployment_time_seconds=duration,
                services_deployed=[service_name],
                configuration=config.dict()
            )
            
        except Exception as e:
            import traceback
            logger.error(f"❌ Deployment failed: {e}")
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Deployment failed: {str(e)}")
    
    def _validate_config(self, config: ConnectorConfigBase):
        """Validate connector configuration"""
        # TODO: Add specific validations per connector type
        if not config.name:
            raise ValueError("Connector name is required")
    
    def _get_env_vars(self, config: ConnectorConfigBase, metrics_port: int) -> Dict[str, str]:
        """Generate environment variables for container"""
        env = {"METRICS_PORT": str(metrics_port)}
        
        if config.connector_type == "rest":
            env.update({
                "API_URL": config.url,
                "API_ENDPOINT": config.endpoint,
                "API_METHOD": config.method,
                "API_TOKEN": config.token or ""
            })
        elif config.connector_type == "mqtt":
            env.update({
                "MQTT_BROKER": config.broker_host,
                "MQTT_PORT": str(config.broker_port),
                "MQTT_TOPICS": ",".join(config.topics) if config.topics else "",
                "MQTT_CLIENT_ID": config.client_id or "rhinometric-collector"
            })
            if config.username:
                env["MQTT_USERNAME"] = config.username
            if config.password:
                env["MQTT_PASSWORD"] = config.password
        elif config.connector_type == "database":
            env.update({
                "DB_TYPE": config.db_type,
                "DB_HOST": config.db_host,
                "DB_PORT": str(config.db_port),
                "DB_NAME": config.db_name,
                "DB_USER": config.db_user,
                "DB_PASSWORD": config.db_password,
                "QUERY_SQL": config.query_sql,
                "QUERY_INTERVAL": str(config.query_interval)
            })
        elif config.connector_type == "webhook":
            env.update({
                "WEBHOOK_PORT": str(config.webhook_port),
                "WEBHOOK_PATH": config.webhook_path,
                "WEBHOOK_SECRET": config.webhook_secret or ""
            })
        
        return env
    
    async def _deploy_docker_services(self, services: List[str]):
        """
        Deploy Docker services using Docker SDK for Python (professional approach)
        
        This uses the Docker API directly instead of shell commands,
        providing better error handling and cross-platform compatibility.
        """
        try:
            import docker
            from docker.errors import DockerException, APIError
            
            # Initialize Docker client
            # The client will automatically handle socket permissions
            # through the mounted /var/run/docker.sock
            client = docker.from_env()
            
            logger.info(f"🐳 Docker client initialized successfully")
            logger.info(f"   Docker version: {client.version()['Version']}")
            
            # Load docker-compose configuration
            compose_file = "/config/docker-compose-v2.5.0.yml"
            project_name = "mi-proyecto"
            project_dir = "/workspace"  # Services are created here
            
            logger.info(f"📋 Loading compose file: {compose_file}")
            logger.info(f"📁 Project directory: {project_dir}")
            
            # Use docker-compose with explicit project directory
            # This ensures build contexts are resolved relative to project_dir
            import subprocess
            
            cmd = [
                "docker", "compose",
                "-f", compose_file,
                "--project-directory", project_dir,
                "-p", project_name,
                "up", "-d",
                "--no-recreate"  # Don't recreate existing containers
            ] + services
            
            logger.info(f"🚀 Executing: {' '.join(cmd)}")
            
            # Run with proper error handling
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                # Filter out the version warning
                error_lines = [line for line in stderr.split('\n') 
                              if 'version' not in line.lower() and 'obsolete' not in line.lower() and line.strip()]
                
                if error_lines:
                    error_msg = '\n'.join(error_lines)
                    raise Exception(f"Docker deployment failed:\n{error_msg}")
            
            logger.info(f"✅ Services deployed successfully: {', '.join(services)}")
            
            # Verify containers are created
            for service in services:
                container_name = f"{project_name}-{service}" if service not in ["prometheus", "grafana"] else f"rhinometric-{service}"
                try:
                    container = client.containers.get(container_name)
                    logger.info(f"   ✓ {container_name}: {container.status}")
                except docker.errors.NotFound:
                    logger.warning(f"   ⚠ Container {container_name} not found after deployment")
            
            client.close()
            
        except DockerException as e:
            logger.error(f"Docker API error: {e}")
            raise Exception(f"Failed to deploy services: Docker API error: {str(e)}")
        except Exception as e:
            logger.error(f"Deployment error: {e}")
            raise Exception(f"Failed to deploy services: {e}")
    
    async def _wait_for_healthy(self, services: List[str], timeout: int = 90):
        """
        Wait for services to be healthy or running using Docker SDK
        
        Professional implementation with proper status checking
        """
        import time
        import docker
        from docker.errors import NotFound, APIError
        
        client = docker.from_env()
        project_name = "mi-proyecto"
        start = time.time()
        
        healthy_services = set()
        
        logger.info(f"⏳ Waiting for {len(services)} services to be healthy...")
        
        while time.time() - start < timeout:
            try:
                for service in services:
                    if service in healthy_services:
                        continue
                    
                    # Determine full container name
                    if service in ["prometheus", "grafana", "loki"]:
                        container_name = f"rhinometric-{service}"
                    else:
                        container_name = f"rhinometric-{service}"
                    
                    try:
                        container = client.containers.get(container_name)
                        status = container.status
                        
                        # Check if container is running
                        if status == "running":
                            # Check health if healthcheck is defined
                            health = container.attrs.get('State', {}).get('Health', {})
                            health_status = health.get('Status', 'none')
                            
                            if health_status == 'healthy' or health_status == 'none':
                                logger.info(f"   ✓ {container_name}: {status} (health: {health_status})")
                                healthy_services.add(service)
                            else:
                                logger.debug(f"   ⏳ {container_name}: {status} (health: {health_status})")
                        else:
                            logger.debug(f"   ⏳ {container_name}: {status}")
                            
                    except NotFound:
                        logger.debug(f"   ⏳ {container_name}: not found yet")
                    except APIError as e:
                        logger.warning(f"   ⚠ {container_name}: API error: {e}")
                
                # All services healthy?
                if len(healthy_services) == len(services):
                    elapsed = time.time() - start
                    logger.info(f"✅ All services healthy in {elapsed:.1f}s")
                    client.close()
                    return
                
                await asyncio.sleep(3)
                
            except Exception as e:
                logger.warning(f"Health check error: {e}")
                await asyncio.sleep(3)
        
        # Timeout handling
        client.close()
        elapsed = time.time() - start
        
        if len(healthy_services) == len(services):
            logger.info(f"✅ All services ready (took {elapsed:.1f}s)")
            return
        
        missing = set(services) - healthy_services
        logger.warning(f"⚠️  Health check timeout after {elapsed:.1f}s. Missing: {missing}")
        logger.warning(f"   Services will continue starting in background")
        # Don't fail deployment, services might still be starting
        return

# ============================================================================
# API ENDPOINTS
# ============================================================================

# Initialize deployer - PROJECT_ROOT should be /app not /app/routes
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
logger.info(f"Initializing deployer with PROJECT_ROOT: {PROJECT_ROOT}")
deployer = ConnectorDeployer(project_root=PROJECT_ROOT)

@router.post("/create-full", response_model=DeploymentResult)
async def create_full_connector(
    config: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """
    🚀 ONE-CLICK CONNECTOR DEPLOYMENT
    
    Creates and deploys a complete connector asynchronously.
    Returns immediately with deployment initiated.
    
    Supported connectors: REST, MQTT, Database, Webhook
    """
    
    connector_type = config.get("connector_type")
    
    # Flatten config: merge top-level fields with nested 'config' dict
    flat_config = {**config}
    if "config" in flat_config:
        nested_config = flat_config.pop("config")
        flat_config.update(nested_config)
    
    if connector_type == "rest":
        connector_config = RESTConnectorConfig(**flat_config)
    elif connector_type == "mqtt":
        connector_config = MQTTConnectorConfig(**flat_config)
    elif connector_type == "database":
        connector_config = DatabaseConnectorConfig(**flat_config)
    elif connector_type == "webhook":
        connector_config = WebhookConnectorConfig(**flat_config)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported connector type: {connector_type}"
        )
    
    # Quick validation
    import re
    sanitized_name = re.sub(r'[^a-z0-9-]', '-', connector_config.name.lower())
    sanitized_name = re.sub(r'-+', '-', sanitized_name).strip('-')
    service_name = f"{connector_config.connector_type}-collector-{sanitized_name}"
    metrics_port = deployer.deployer.get_next_available_port()
    dashboard_uid = f"{connector_config.connector_type}-{sanitized_name}"
    
    # Start deployment in background
    background_tasks.add_task(
        deployer.deploy_connector,
        config=connector_config,
        db=None
    )
    
    # Return immediate response
    return DeploymentResult(
        success=True,
        message=f"{connector_config.connector_type.upper()} connector deployment initiated",
        connector_name=connector_config.name,
        connector_type=connector_config.connector_type,
        service_name=service_name,
        dashboard_url=f"http://localhost:3000/d/{dashboard_uid}",
        metrics_url=f"http://localhost:{metrics_port}/metrics",
        deployment_time_seconds=0.0,
        services_deployed=[service_name],
        configuration=connector_config.dict()
    )

@router.get("/status/{service_name}")
async def get_connector_status(service_name: str):
    """
    Get status of deployed connector.
    """
    try:
        cmd = f"docker ps --filter name={service_name} --format '{{{{json .}}}}'"
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await process.communicate()
        
        if stdout:
            import json
            container_info = json.loads(stdout.decode())
            return {
                "status": "running",
                "service_name": service_name,
                "container": container_info
            }
        else:
            return {
                "status": "not_found",
                "service_name": service_name
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
