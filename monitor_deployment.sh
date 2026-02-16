#!/bin/bash

# Script para monitorear el estado del deployment de SaaS
# Uso: ./monitor_deployment.sh

SERVER_IP="143.47.63.21"
SSH_KEY="~/.ssh/oci_key"

echo "🚀 Monitoreando deployment de SaaS en Oracle Cloud..."
echo "📍 IP: $SERVER_IP"
echo "🕒 Iniciado: $(date)"
echo ""

# Función para verificar conectividad SSH
check_ssh() {
    ssh -i $SSH_KEY -o StrictHostKeyChecking=no -o ConnectTimeout=5 opc@$SERVER_IP 'echo "SSH OK"' 2>/dev/null
}

# Función para verificar puerto
check_port() {
    local port=$1
    local service=$2
    if nc -zv $SERVER_IP $port 2>&1 | grep -q "succeeded"; then
        echo "✅ $service (puerto $port): DISPONIBLE"
        return 0
    else
        echo "❌ $service (puerto $port): NO disponible"
        return 1
    fi
}

# Función para verificar servicios Docker
check_docker_services() {
    ssh -i $SSH_KEY -o StrictHostKeyChecking=no -o ConnectTimeout=5 opc@$SERVER_IP 'sudo docker ps --format "table {{.Names}}\t{{.Status}}"' 2>/dev/null
}

# Función principal de monitoreo
monitor_loop() {
    local attempt=1
    while [ $attempt -le 20 ]; do
        echo "📊 Intento $attempt/20 - $(date)"
        
        # Verificar SSH
        if check_ssh > /dev/null 2>&1; then
            echo "✅ SSH: Conectado exitosamente"
            
            # Verificar servicios Docker
            echo "🐳 Estado de servicios Docker:"
            docker_status=$(check_docker_services)
            if [ $? -eq 0 ]; then
                echo "$docker_status"
                
                # Verificar puertos de servicios
                echo ""
                echo "🌐 Estado de puertos de servicios:"
                check_port 3000 "Grafana"
                check_port 9090 "Prometheus" 
                check_port 22 "SSH"
                check_port 80 "Nginx"
                
                # Si Grafana está disponible, terminamos
                if check_port 3000 "Grafana" > /dev/null 2>&1; then
                    echo ""
                    echo "🎉 ¡DEPLOYMENT COMPLETADO!"
                    echo "🔗 Acceso a servicios:"
                    echo "   • Grafana: http://$SERVER_IP:3000"
                    echo "   • Prometheus: http://$SERVER_IP:9090"
                    echo "   • SSH: ssh -i $SSH_KEY opc@$SERVER_IP"
                    exit 0
                fi
            else
                echo "⏳ Docker aún no está disponible o servicios iniciando..."
            fi
        else
            ssh_result=$(ssh -i $SSH_KEY -o StrictHostKeyChecking=no -o ConnectTimeout=5 opc@$SERVER_IP 'echo test' 2>&1)
            if [[ "$ssh_result" == *"System is booting up"* ]]; then
                echo "⏳ Sistema iniciando - cloud-init ejecutándose..."
            elif [[ "$ssh_result" == *"Permission denied"* ]]; then
                echo "🔐 Problema de autenticación SSH"
            else
                echo "❌ SSH no disponible: $ssh_result"
            fi
        fi
        
        echo "⏱️  Esperando 60 segundos..."
        echo "----------------------------------------"
        sleep 60
        attempt=$((attempt + 1))
    done
    
    echo "⚠️  Tiempo de espera agotado después de 20 intentos (20 minutos)"
    echo "💡 El sistema puede necesitar más tiempo. Intenta conectar manualmente:"
    echo "   ssh -i $SSH_KEY opc@$SERVER_IP"
}

# Ejecutar monitoreo
monitor_loop