#!/bin/bash

echo "======================================================================"
echo "  RHINOMETRIC COMPLETE UNINSTALL FOR macOS"
echo "======================================================================"
echo ""
echo "This script will completely remove RHINOMETRIC from your Mac"
echo "including Docker containers, images, volumes, networks, and data"
echo ""
read -p "Press ENTER to continue or CTRL+C to cancel..."
echo ""

echo "Step 1: Stopping all RHINOMETRIC containers..."
docker ps -a | grep rhinometric | awk '{print $1}' | xargs -r docker stop 2>/dev/null
echo "✓ Containers stopped"
echo ""

echo "Step 2: Removing all RHINOMETRIC containers..."
docker ps -a | grep rhinometric | awk '{print $1}' | xargs -r docker rm -f 2>/dev/null
echo "✓ Containers removed"
echo ""

echo "Step 3: Removing RHINOMETRIC images..."
docker images | grep rhinometric | awk '{print $3}' | xargs -r docker rmi -f 2>/dev/null
docker images | grep prom/ | awk '{print $3}' | xargs -r docker rmi -f 2>/dev/null
docker images | grep grafana/ | awk '{print $3}' | xargs -r docker rmi -f 2>/dev/null
docker images | grep postgres | awk '{print $3}' | xargs -r docker rmi -f 2>/dev/null
docker images | grep redis | awk '{print $3}' | xargs -r docker rmi -f 2>/dev/null
docker images | grep nginx | awk '{print $3}' | xargs -r docker rmi -f 2>/dev/null
echo "✓ Images removed"
echo ""

echo "Step 4: Removing RHINOMETRIC volumes..."
docker volume ls | grep rhinometric | awk '{print $2}' | xargs -r docker volume rm -f 2>/dev/null
docker volume ls | grep mi-proyecto | awk '{print $2}' | xargs -r docker volume rm -f 2>/dev/null
echo "✓ Volumes removed"
echo ""

echo "Step 5: Removing RHINOMETRIC networks..."
docker network ls | grep rhinometric | awk '{print $1}' | xargs -r docker network rm 2>/dev/null
docker network ls | grep mi-proyecto | awk '{print $1}' | xargs -r docker network rm 2>/dev/null
echo "✓ Networks removed"
echo ""

echo "Step 6: Removing RHINOMETRIC data directories..."
if [ -d "$HOME/rhinometric_data" ]; then
    rm -rf "$HOME/rhinometric_data"
    echo "✓ Removed $HOME/rhinometric_data"
fi

if [ -d "$HOME/rhinometric_data_v2.2" ]; then
    rm -rf "$HOME/rhinometric_data_v2.2"
    echo "✓ Removed $HOME/rhinometric_data_v2.2"
fi

if [ -d "$HOME/rhinometric_data_trial" ]; then
    rm -rf "$HOME/rhinometric_data_trial"
    echo "✓ Removed $HOME/rhinometric_data_trial"
fi

if [ -d "$HOME/.rhinometric" ]; then
    rm -rf "$HOME/.rhinometric"
    echo "✓ Removed $HOME/.rhinometric"
fi
echo ""

echo "Step 7: Removing RHINOMETRIC installation files..."
if [ -d "/tmp/rhinometric" ]; then
    rm -rf /tmp/rhinometric
    echo "✓ Removed /tmp/rhinometric"
fi

if [ -d "/tmp/rhinometric-trial" ]; then
    rm -rf /tmp/rhinometric-trial
    echo "✓ Removed /tmp/rhinometric-trial"
fi

if [ -d "$HOME/Downloads/rhinometric"* ]; then
    rm -rf "$HOME/Downloads/rhinometric"*
    echo "✓ Removed Download files"
fi
echo ""

echo "Step 8: Cleaning Docker system..."
docker system prune -af --volumes 2>/dev/null
echo "✓ Docker system cleaned"
echo ""

echo "Step 9: Removing Docker virtual disk (optional)..."
echo "WARNING: This will remove ALL Docker data, not just RHINOMETRIC"
read -p "Do you want to remove Docker Desktop virtual disk? (y/N): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    osascript -e 'quit app "Docker"' 2>/dev/null
    sleep 5
    
    if [ -f "$HOME/Library/Containers/com.docker.docker/Data/vms/0/data/Docker.raw" ]; then
        rm -f "$HOME/Library/Containers/com.docker.docker/Data/vms/0/data/Docker.raw"
        echo "✓ Removed Docker.raw"
    fi
    
    if [ -d "$HOME/Library/Containers/com.docker.docker" ]; then
        rm -rf "$HOME/Library/Containers/com.docker.docker"
        echo "✓ Removed Docker Desktop data"
    fi
    
    echo "✓ Docker virtual disk removed"
    echo "NOTE: You will need to restart Docker Desktop"
else
    echo "⊘ Docker virtual disk kept"
fi
echo ""

echo "Step 10: Removing RHINOMETRIC configuration files..."
if [ -f "$HOME/.zshrc" ]; then
    sed -i.backup '/rhinometric/Id' "$HOME/.zshrc" 2>/dev/null
    sed -i.backup '/RHINOMETRIC/Id' "$HOME/.zshrc" 2>/dev/null
    echo "✓ Cleaned .zshrc"
fi

if [ -f "$HOME/.bash_profile" ]; then
    sed -i.backup '/rhinometric/Id' "$HOME/.bash_profile" 2>/dev/null
    sed -i.backup '/RHINOMETRIC/Id' "$HOME/.bash_profile" 2>/dev/null
    echo "✓ Cleaned .bash_profile"
fi

if [ -f "$HOME/.bashrc" ]; then
    sed -i.backup '/rhinometric/Id' "$HOME/.bashrc" 2>/dev/null
    sed -i.backup '/RHINOMETRIC/Id' "$HOME/.bashrc" 2>/dev/null
    echo "✓ Cleaned .bashrc"
fi
echo ""

echo "======================================================================"
echo "  UNINSTALL COMPLETE"
echo "======================================================================"
echo ""
echo "✓ All RHINOMETRIC components have been removed"
echo ""
echo "Summary:"
echo "  - Docker containers: removed"
echo "  - Docker images: removed"
echo "  - Docker volumes: removed"
echo "  - Docker networks: removed"
echo "  - Data directories: removed"
echo "  - Configuration files: cleaned"
echo ""
echo "To verify removal, run:"
echo "  docker ps -a | grep rhinometric"
echo "  docker images | grep rhinometric"
echo "  ls -la ~/rhinometric*"
echo ""
echo "======================================================================"
