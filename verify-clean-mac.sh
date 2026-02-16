#!/bin/bash

echo "======================================================================"
echo "  RHINOMETRIC CLEANUP VERIFICATION"
echo "======================================================================"
echo ""

echo "Checking for RHINOMETRIC containers..."
containers=$(docker ps -a 2>/dev/null | grep -i rhinometric | wc -l)
if [ "$containers" -eq 0 ]; then
    echo "✓ No RHINOMETRIC containers found"
else
    echo "✗ Found $containers RHINOMETRIC containers:"
    docker ps -a | grep -i rhinometric
fi
echo ""

echo "Checking for RHINOMETRIC images..."
images=$(docker images 2>/dev/null | grep -i rhinometric | wc -l)
if [ "$images" -eq 0 ]; then
    echo "✓ No RHINOMETRIC images found"
else
    echo "✗ Found $images RHINOMETRIC images:"
    docker images | grep -i rhinometric
fi
echo ""

echo "Checking for RHINOMETRIC volumes..."
volumes=$(docker volume ls 2>/dev/null | grep -i rhinometric | wc -l)
if [ "$volumes" -eq 0 ]; then
    echo "✓ No RHINOMETRIC volumes found"
else
    echo "✗ Found $volumes RHINOMETRIC volumes:"
    docker volume ls | grep -i rhinometric
fi
echo ""

echo "Checking for RHINOMETRIC networks..."
networks=$(docker network ls 2>/dev/null | grep -i rhinometric | wc -l)
if [ "$networks" -eq 0 ]; then
    echo "✓ No RHINOMETRIC networks found"
else
    echo "✗ Found $networks RHINOMETRIC networks:"
    docker network ls | grep -i rhinometric
fi
echo ""

echo "Checking for RHINOMETRIC data directories..."
found_dirs=0
if [ -d "$HOME/rhinometric_data" ]; then
    echo "✗ Found: $HOME/rhinometric_data"
    found_dirs=$((found_dirs + 1))
fi
if [ -d "$HOME/rhinometric_data_v2.2" ]; then
    echo "✗ Found: $HOME/rhinometric_data_v2.2"
    found_dirs=$((found_dirs + 1))
fi
if [ -d "$HOME/rhinometric_data_trial" ]; then
    echo "✗ Found: $HOME/rhinometric_data_trial"
    found_dirs=$((found_dirs + 1))
fi
if [ -d "$HOME/.rhinometric" ]; then
    echo "✗ Found: $HOME/.rhinometric"
    found_dirs=$((found_dirs + 1))
fi
if [ "$found_dirs" -eq 0 ]; then
    echo "✓ No RHINOMETRIC data directories found"
fi
echo ""

echo "Checking Docker disk usage..."
if command -v docker &> /dev/null; then
    docker system df 2>/dev/null
else
    echo "⊘ Docker not installed or not running"
fi
echo ""

echo "Checking shell configuration files..."
config_clean=0
if [ -f "$HOME/.zshrc" ]; then
    zsh_lines=$(grep -i rhinometric "$HOME/.zshrc" 2>/dev/null | wc -l)
    if [ "$zsh_lines" -gt 0 ]; then
        echo "✗ Found $zsh_lines RHINOMETRIC references in .zshrc"
        config_clean=1
    fi
fi
if [ -f "$HOME/.bash_profile" ]; then
    bash_lines=$(grep -i rhinometric "$HOME/.bash_profile" 2>/dev/null | wc -l)
    if [ "$bash_lines" -gt 0 ]; then
        echo "✗ Found $bash_lines RHINOMETRIC references in .bash_profile"
        config_clean=1
    fi
fi
if [ -f "$HOME/.bashrc" ]; then
    bashrc_lines=$(grep -i rhinometric "$HOME/.bashrc" 2>/dev/null | wc -l)
    if [ "$bashrc_lines" -gt 0 ]; then
        echo "✗ Found $bashrc_lines RHINOMETRIC references in .bashrc"
        config_clean=1
    fi
fi
if [ "$config_clean" -eq 0 ]; then
    echo "✓ Shell configuration files are clean"
fi
echo ""

echo "======================================================================"
total_issues=$((containers + images + volumes + networks + found_dirs + config_clean))
if [ "$total_issues" -eq 0 ]; then
    echo "  ✓ VERIFICATION PASSED"
    echo "  Your Mac is completely clean of RHINOMETRIC"
else
    echo "  ✗ VERIFICATION FAILED"
    echo "  Found $total_issues issue(s)"
    echo "  Run uninstall-rhinometric-mac-force.sh to force cleanup"
fi
echo "======================================================================"
