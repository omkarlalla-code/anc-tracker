#!/bin/bash
# Start dashboard on public IP with nginx
set -e

PORT="${1:-8080}"

echo "Starting dashboard on public IP..."
echo "Ensure nginx is configured to proxy to port ${PORT}"

cd dashboard
python3 -m http.server "$PORT" --bind 0.0.0.0
