#!/bin/bash
# Hot-swap messaging or hosting backend
set -e

echo "Switch backend:"
echo "1) Messaging"
echo "2) Hosting"
read -p "Choice: " choice

case $choice in
    1)
        echo "Available messaging backends:"
        ls plugins/messaging/*_send.py | sed 's/.*\//  /' | sed 's/_send.py//'
        read -p "Backend: " backend
        export MESSAGING_PLUGIN="plugins/messaging/${backend}_send.py"
        echo "Switched to: $MESSAGING_PLUGIN"
        ;;
    2)
        echo "Available hosting backends:"
        ls plugins/hosting/start_*.sh | sed 's/.*start_/  /' | sed 's/.sh//'
        read -p "Backend: " backend
        echo "Run: ./plugins/hosting/start_${backend}.sh"
        ;;
esac
