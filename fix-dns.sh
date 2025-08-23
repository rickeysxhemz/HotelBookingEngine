#!/bin/bash
# Network DNS fix script for Podman DNS conflicts

echo "🌐 Fixing Podman DNS and networking issues..."

# Create containers config directory
mkdir -p ~/.config/containers

# Configure Podman networking to avoid DNS conflicts
cat > ~/.config/containers/containers.conf << EOF
[network]
dns_bind_port = 0

[engine]
network_cmd_options = ["enable_ipv6=false"]
EOF

echo "✅ Networking configuration updated"

# Clean up all existing containers and networks
echo "🧹 Cleaning up all containers and networks..."
podman-compose -f docker-compose.prod.yml down --volumes 2>/dev/null || true
podman container prune -f 2>/dev/null || true
podman network prune -f 2>/dev/null || true

# Check if port 53 is in use and show what's using it
echo "🔍 Checking DNS port usage..."
if sudo netstat -tulpn | grep :53 > /dev/null 2>&1; then
    echo "⚠️  Port 53 is in use by:"
    sudo netstat -tulpn | grep :53
    echo ""
    echo "💡 Options to resolve this:"
    echo "1. Run: sudo systemctl stop systemd-resolved"
    echo "2. Or continue with deployment (network config should handle this)"
    echo ""
fi

echo "✅ Network cleanup complete!"
echo ""
echo "🚀 You can now run:"
echo "   ./deploy.sh"
echo ""
echo "If deployment still fails, try:"
echo "   sudo systemctl stop systemd-resolved"
echo "   ./deploy.sh"
echo "   sudo systemctl start systemd-resolved"
