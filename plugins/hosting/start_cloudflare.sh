#!/bin/bash
# Start dashboard with Cloudflare Tunnel
set -e

CONFIG="${1:-config/hosting/cloudflare.conf}"
TUNNEL_NAME=$(grep "^tunnel_name" "$CONFIG" | cut -d= -f2 | tr -d ' ')
DOMAIN=$(grep "^domain" "$CONFIG" | cut -d= -f2 | tr -d ' ')
PORT=$(grep "^port" "$CONFIG" | cut -d= -f2 | tr -d ' ')

echo "Starting dashboard via Cloudflare Tunnel..."
echo "Access at: https://${DOMAIN}"

cd dashboard
python3 -m http.server "$PORT" --bind localhost &

cloudflared tunnel run "$TUNNEL_NAME"
