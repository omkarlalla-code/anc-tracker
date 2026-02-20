#!/bin/bash
# Start dashboard with Tailscale VPN access
set -e

CONFIG="${1:-config/hosting/tailscale.conf}"
PORT=$(grep "^port" "$CONFIG" | cut -d= -f2 | tr -d ' ')
BIND=$(grep "^bind" "$CONFIG" | cut -d= -f2 | tr -d ' ')

echo "Starting dashboard on Tailscale network..."
echo "Access at: http://$(hostname).tailnet-name.ts.net:${PORT}"

cd dashboard
python3 -m http.server "$PORT" --bind "$BIND"
