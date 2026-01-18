"""
RHINOMETRIC v2.5.0 - Code Generator Service
============================================

Generates collector services dynamically from templates.
Supports: REST, MQTT, Database, Webhook
"""

import os
import re
from typing import Dict, Any
from jinja2 import Template
import logging

logger = logging.getLogger(__name__)


class CodeGenerator:
    """
    Generates Python code for data collectors from templates.
    """
    
    def __init__(self, templates_dir: str = None):
        if templates_dir is None:
            # Use absolute path from project root
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            templates_dir = os.path.join(base_dir, "templates", "collectors")
        self.templates_dir = templates_dir
        logger.info(f"CodeGenerator initialized with templates_dir: {self.templates_dir}")
    
    def generate_collector(
        self,
        connector_type: str,
        config: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Generate collector code, Dockerfile, and requirements.txt
        
        Args:
            connector_type: "rest", "mqtt", "database", "webhook"
            config: Configuration dictionary
        
        Returns:
            {
                'collector.py': '...',
                'Dockerfile': '...',
                'requirements.txt': '...'
            }
        """
        template_file = f"{connector_type}_collector_template.py"
        template_path = os.path.join(self.templates_dir, template_file)
        
        if not os.path.exists(template_path):
            raise ValueError(f"Template not found: {template_path}")
        
        # Load template
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Generate code
        template = Template(template_content)
        collector_code = template.render(**config)
        
        # Generate Dockerfile
        dockerfile = self._generate_dockerfile(connector_type, config)
        
        # Generate requirements.txt
        requirements = self._generate_requirements(connector_type, config)
        
        return {
            'collector.py': collector_code,
            'Dockerfile': dockerfile,
            'requirements.txt': requirements
        }
    
    def _generate_dockerfile(self, connector_type: str, config: Dict[str, Any]) -> str:
        """Generate Dockerfile for collector"""
        return f"""FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy collector code
COPY collector.py .

# Expose metrics port
EXPOSE {config.get('metrics_port', 9300)}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:{config.get('metrics_port', 9300)}/metrics')" || exit 1

# Run collector
CMD ["python", "-u", "collector.py"]
"""
    
    def _generate_requirements(self, connector_type: str, config: Dict[str, Any]) -> str:
        """Generate requirements.txt based on connector type"""
        base_requirements = [
            "prometheus-client==0.19.0",
            "opentelemetry-api==1.22.0",
            "opentelemetry-sdk==1.22.0",
            "opentelemetry-exporter-otlp-proto-grpc==1.22.0"
        ]
        
        connector_requirements = {
            'rest': [
                "requests==2.31.0",
                "aiohttp==3.9.1"
            ],
            'mqtt': [
                "aiomqtt==2.0.1"
            ],
            'database': [
                "psycopg2-binary==2.9.9",
                "sqlalchemy==2.0.23",
                "pymysql==1.1.0",
                "opentelemetry-instrumentation-sqlalchemy==0.43b0"
            ],
            'webhook': [
                "fastapi==0.109.0",
                "uvicorn==0.27.0",
                "opentelemetry-instrumentation-fastapi==0.43b0"
            ]
        }
        
        requirements = base_requirements + connector_requirements.get(connector_type, [])
        return '\n'.join(requirements)


class ServiceDeployer:
    """
    Deploys generated collectors to Docker infrastructure.
    """
    
    def __init__(self, project_root: str):
        self.project_root = project_root
    
    def create_service_structure(
        self,
        service_name: str,
        files: Dict[str, str]
    ) -> str:
        """
        Create service directory with generated files.
        
        Args:
            service_name: Name of the service (e.g., "mqtt-collector-hivemq")
            files: Dictionary of filename -> content
        
        Returns:
            Path to created service directory
        """
        # Sanitize service name
        safe_name = re.sub(r'[^a-z0-9\-]', '-', service_name.lower())
        service_dir = os.path.join(self.project_root, safe_name)
        
        # Create directory
        os.makedirs(service_dir, exist_ok=True)
        logger.info(f"Created service directory: {service_dir}")
        
        # Write files
        for filename, content in files.items():
            file_path = os.path.join(service_dir, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Created file: {file_path}")
        
        return service_dir
    
    def get_next_available_port(self) -> int:
        """
        Find next available port for metrics endpoint.
        Scans docker-compose.yml to find used ports and returns the next available one.
        """
        import yaml
        import docker
        
        base_port = 9300
        max_port = 9400
        used_ports = set()
        
        # Method 1: Parse docker-compose.yml to find declared ports
        compose_file = os.getenv("COMPOSE_FILE", "/config/docker-compose-v2.5.0.yml")
        try:
            with open(compose_file, 'r', encoding='utf-8') as f:
                compose_data = yaml.safe_load(f)
            
            if compose_data and 'services' in compose_data:
                for service_name, service_config in compose_data['services'].items():
                    if 'ports' in service_config:
                        for port_mapping in service_config['ports']:
                            # Handle "9310:9310" or 9310 format
                            port_str = str(port_mapping).split(':')[0]
                            try:
                                port = int(port_str)
                                if base_port <= port < max_port:
                                    used_ports.add(port)
                            except ValueError:
                                continue
        except Exception as e:
            logger.warning(f"Could not parse compose file: {e}")
        
        # Method 2: Check running containers
        try:
            client = docker.from_env()
            containers = client.containers.list()
            for container in containers:
                if container.ports:
                    for port_info in container.ports.values():
                        if port_info:
                            for binding in port_info:
                                if 'HostPort' in binding:
                                    try:
                                        port = int(binding['HostPort'])
                                        if base_port <= port < max_port:
                                            used_ports.add(port)
                                    except (ValueError, KeyError):
                                        continue
            client.close()
        except Exception as e:
            logger.warning(f"Could not check running containers: {e}")
        
        # Find first available port
        for port in range(base_port, max_port):
            if port not in used_ports:
                logger.info(f"🔌 Assigned available port: {port}")
                return port
        
        # Fallback
        logger.warning(f"All ports {base_port}-{max_port} appear to be in use, using {max_port}")
        return max_port


class DockerComposeManager:
    """
    Manages docker-compose.yml dynamically.
    """
    
    def __init__(self, compose_file: str):
        self.compose_file = compose_file
    
    def add_service(
        self,
        service_name: str,
        build_path: str,
        ports: list,
        environment: Dict[str, str],
        depends_on: list = None
    ) -> bool:
        """
        Add service to docker-compose.yml using APPEND (not YAML dump)
        to avoid corrupting existing structure.
        
        Args:
            service_name: Name of the service
            build_path: Path to build context (relative)
            ports: List of port mappings ["9310:9310"]
            environment: Environment variables
            depends_on: List of service dependencies
        
        Returns:
            True if successful
        """
        import yaml
        
        # Check if service already exists
        with open(self.compose_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if f"  {service_name}:" in content:
                logger.warning(f"Service '{service_name}' already exists in docker-compose.yml")
                return False
        
        # Build service YAML manually to preserve formatting
        service_yaml = f"\n  {service_name}:\n"
        service_yaml += f"    build: {build_path}\n"
        service_yaml += f"    container_name: rhinometric-{service_name}\n"
        service_yaml += f"    ports:\n"
        for port in ports:
            service_yaml += f"      - {port}\n"
        service_yaml += f"    environment:\n"
        for key, value in environment.items():
            # Escape quotes in values
            value_escaped = str(value).replace('"', '\\"')
            service_yaml += f"      {key}: \"{value_escaped}\"\n"
        service_yaml += f"    restart: unless-stopped\n"
        service_yaml += f"    networks:\n"
        service_yaml += f"      - rhinometric_network_v22\n"
        if depends_on:
            service_yaml += f"    depends_on:\n"
            for dep in depends_on:
                service_yaml += f"      - {dep}\n"
        
        # Append to file (before networks section if it exists)
        with open(self.compose_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Find insertion point (before 'networks:' section at root level)
        insert_idx = len(lines)
        for i, line in enumerate(lines):
            # Match 'networks:' at START of line (no indentation)
            if line.strip() and not line.startswith(' ') and line.startswith('networks:'):
                insert_idx = i
                break
        
        # Insert service
        lines.insert(insert_idx, service_yaml)
        
        with open(self.compose_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        logger.info(f"✅ Added service '{service_name}' to {self.compose_file}")
        return True


class PrometheusConfigManager:
    """
    Manages Prometheus configuration dynamically.
    """
    
    def __init__(self, prometheus_config: str):
        self.prometheus_config = prometheus_config
    
    def add_scrape_target(
        self,
        job_name: str,
        target: str,
        scrape_interval: str = "15s"
    ) -> bool:
        """
        Add scrape target to prometheus.yml
        
        Args:
            job_name: Name of the job (e.g., "mqtt-hivemq")
            target: Target address (e.g., "mqtt-collector-hivemq:9310")
            scrape_interval: Scrape interval
        
        Returns:
            True if successful
        """
        import yaml
        
        # Load existing config
        with open(self.prometheus_config, 'r', encoding='utf-8') as f:
            prom_config = yaml.safe_load(f)
        
        # Create scrape config
        scrape_config = {
            'job_name': job_name,
            'scrape_interval': scrape_interval,
            'static_configs': [
                {'targets': [target]}
            ]
        }
        
        # Add to scrape_configs
        if 'scrape_configs' not in prom_config:
            prom_config['scrape_configs'] = []
        
        # Check if job already exists
        existing_jobs = [sc['job_name'] for sc in prom_config['scrape_configs']]
        if job_name in existing_jobs:
            logger.warning(f"Job '{job_name}' already exists in Prometheus config")
            return False
        
        prom_config['scrape_configs'].append(scrape_config)
        
        # Write back
        with open(self.prometheus_config, 'w', encoding='utf-8') as f:
            yaml.dump(prom_config, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Added scrape target '{job_name}' to Prometheus config")
        return True
