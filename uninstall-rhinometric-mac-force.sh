#!/bin/bash

echo "======================================================================"
echo "  RHINOMETRIC FORCE UNINSTALL FOR macOS"
echo "======================================================================"
echo ""
echo "NUCLEAR OPTION: This will remove EVERYTHING including Docker Desktop"
echo ""
read -p "Are you ABSOLUTELY sure? Type 'YES' to continue: " confirm
if [ "$confirm" != "YES" ]; then
    echo "Aborted."
    exit 0
fi
echo ""

echo "[1/12] Force stopping Docker Desktop..."
osascript -e 'quit app "Docker"' 2>/dev/null
killall Docker 2>/dev/null
killall com.docker.backend 2>/dev/null
killall com.docker.vpnkit 2>/dev/null
sleep 5
echo "✓ Docker stopped"
echo ""

echo "[2/12] Removing all Docker containers..."
docker rm -f $(docker ps -aq) 2>/dev/null
echo "✓ All containers removed"
echo ""

echo "[3/12] Removing all Docker images..."
docker rmi -f $(docker images -aq) 2>/dev/null
echo "✓ All images removed"
echo ""

echo "[4/12] Removing all Docker volumes..."
docker volume rm -f $(docker volume ls -q) 2>/dev/null
echo "✓ All volumes removed"
echo ""

echo "[5/12] Removing all Docker networks..."
docker network rm $(docker network ls -q) 2>/dev/null
echo "✓ All networks removed"
echo ""

echo "[6/12] Nuclear Docker cleanup..."
docker system prune -af --volumes 2>/dev/null
echo "✓ Docker pruned"
echo ""

echo "[7/12] Removing RHINOMETRIC data directories..."
rm -rf "$HOME/rhinometric_data" 2>/dev/null
rm -rf "$HOME/rhinometric_data_v2.2" 2>/dev/null
rm -rf "$HOME/rhinometric_data_trial" 2>/dev/null
rm -rf "$HOME/.rhinometric" 2>/dev/null
rm -rf /tmp/rhinometric* 2>/dev/null
rm -rf "$HOME/Downloads/rhinometric"* 2>/dev/null
echo "✓ Data directories removed"
echo ""

echo "[8/12] Removing Docker Desktop application..."
if [ -d "/Applications/Docker.app" ]; then
    rm -rf "/Applications/Docker.app"
    echo "✓ Docker.app removed"
else
    echo "⊘ Docker.app not found"
fi
echo ""

echo "[9/12] Removing Docker Desktop data and caches..."
rm -rf "$HOME/Library/Application Support/Docker Desktop" 2>/dev/null
rm -rf "$HOME/Library/Containers/com.docker.docker" 2>/dev/null
rm -rf "$HOME/Library/Containers/com.docker.helper" 2>/dev/null
rm -rf "$HOME/Library/Group Containers/group.com.docker" 2>/dev/null
rm -rf "$HOME/Library/Preferences/com.docker.docker.plist" 2>/dev/null
rm -rf "$HOME/Library/Saved Application State/com.electron.docker-frontend.savedState" 2>/dev/null
rm -rf "$HOME/Library/Logs/Docker Desktop" 2>/dev/null
rm -rf "$HOME/Library/Caches/com.docker.docker" 2>/dev/null
rm -rf "/Library/PrivilegedHelperTools/com.docker.vmnetd" 2>/dev/null
rm -rf "/Library/LaunchDaemons/com.docker.vmnetd.plist" 2>/dev/null
echo "✓ Docker Desktop data removed"
echo ""

echo "[10/12] Removing Docker CLI tools..."
rm -f /usr/local/bin/docker 2>/dev/null
rm -f /usr/local/bin/docker-compose 2>/dev/null
rm -f /usr/local/bin/docker-credential-desktop 2>/dev/null
rm -f /usr/local/bin/docker-credential-ecr-login 2>/dev/null
rm -f /usr/local/bin/docker-credential-osxkeychain 2>/dev/null
rm -f /usr/local/bin/hub-tool 2>/dev/null
rm -f /usr/local/bin/kubectl 2>/dev/null
rm -f /usr/local/bin/kubectl.docker 2>/dev/null
echo "✓ Docker CLI removed"
echo ""

echo "[11/12] Cleaning shell configuration files..."
if [ -f "$HOME/.zshrc" ]; then
    cp "$HOME/.zshrc" "$HOME/.zshrc.backup"
    grep -v -i 'docker\|rhinometric\|RHINOMETRIC' "$HOME/.zshrc.backup" > "$HOME/.zshrc"
    echo "✓ .zshrc cleaned (backup: .zshrc.backup)"
fi

if [ -f "$HOME/.bash_profile" ]; then
    cp "$HOME/.bash_profile" "$HOME/.bash_profile.backup"
    grep -v -i 'docker\|rhinometric\|RHINOMETRIC' "$HOME/.bash_profile.backup" > "$HOME/.bash_profile"
    echo "✓ .bash_profile cleaned (backup: .bash_profile.backup)"
fi

if [ -f "$HOME/.bashrc" ]; then
    cp "$HOME/.bashrc" "$HOME/.bashrc.backup"
    grep -v -i 'docker\|rhinometric\|RHINOMETRIC' "$HOME/.bashrc.backup" > "$HOME/.bashrc"
    echo "✓ .bashrc cleaned (backup: .bashrc.backup)"
fi
echo ""

echo "[12/12] Final cleanup..."
rm -rf /var/run/docker.sock 2>/dev/null
rm -rf ~/.docker 2>/dev/null
echo "✓ Final cleanup complete"
echo ""

echo "======================================================================"
echo "  FORCE UNINSTALL COMPLETE"
echo "======================================================================"
echo ""
echo "✓ EVERYTHING has been removed:"
echo "  - All Docker containers"
echo "  - All Docker images"
echo "  - All Docker volumes"
echo "  - All Docker networks"
echo "  - Docker Desktop application"
echo "  - Docker Desktop data and virtual disks"
echo "  - Docker CLI tools"
echo "  - RHINOMETRIC data directories"
echo "  - Configuration files (backups created)"
echo ""
echo "Your Mac is now completely clean of Docker and RHINOMETRIC"
echo ""
echo "To reinstall Docker Desktop, download from:"
echo "  https://www.docker.com/products/docker-desktop"
echo ""
echo "======================================================================"
