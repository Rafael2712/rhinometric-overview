#!/bin/bash
# ==========================================
# RHINOMETRIC Docker Wrapper
# ==========================================
# Secure wrapper for Docker operations
# Escalates to root only for Docker commands

# Check if running as root
if [ "$(id -u)" = "0" ]; then
    # Already root, execute docker command directly
    exec docker "$@"
else
    # Not root, check if docker socket is accessible
    if docker ps >/dev/null 2>&1; then
        # Socket accessible, execute directly
        exec docker "$@"
    else
        # Socket not accessible, need to use sudo/su
        # This shouldn't happen in production if permissions are correct
        echo "ERROR: Docker socket not accessible and no root privileges" >&2
        echo "This indicates a configuration issue with Docker socket permissions" >&2
        exit 1
    fi
fi
