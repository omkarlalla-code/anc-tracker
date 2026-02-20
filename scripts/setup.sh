#!/bin/bash
# Interactive setup script

set -e

echo "=== Health Tracker Setup ==="
echo

# Check dependencies
echo "Checking dependencies..."
command -v python3 >/dev/null 2>&1 || { echo "Error: python3 not found"; exit 1; }
command -v sqlite3 >/dev/null 2>&1 || { echo "Error: sqlite3 not found"; exit 1; }
command -v pip3 >/dev/null 2>&1 || { echo "Error: pip3 not found"; exit 1; }

# Choose messaging backend
echo "Select messaging backend:"
echo "1) WhatsApp Business API"
echo "2) Telegram"
echo "3) Email"
read -p "Choice [1]: " messaging_choice
messaging_choice=${messaging_choice:-1}

case $messaging_choice in
    1) MESSAGING=whatsapp ;;
    2) MESSAGING=telegram ;;
    3) MESSAGING=email ;;
    *) echo "Invalid choice"; exit 1 ;;
esac

# Choose hosting
echo
echo "Select hosting method:"
echo "1) Tailscale VPN (recommended for Pi)"
echo "2) Cloudflare Tunnel"
echo "3) Public IP with nginx"
read -p "Choice [1]: " hosting_choice
hosting_choice=${hosting_choice:-1}

case $hosting_choice in
    1) HOSTING=tailscale ;;
    2) HOSTING=cloudflare ;;
    3) HOSTING=public ;;
    *) echo "Invalid choice"; exit 1 ;;
esac

# Create config files
echo
echo "Creating configuration files..."
cp "config/messaging/${MESSAGING}.example.json" "config/messaging/${MESSAGING}.json"
cp "config/hosting/${HOSTING}.example.conf" "config/hosting/${HOSTING}.conf"

echo "Edit these files with your credentials:"
echo "  - config/messaging/${MESSAGING}.json"
echo "  - config/hosting/${HOSTING}.conf"

# Make Python scripts executable
echo
echo "Making scripts executable..."
chmod +x core/*.py
chmod +x plugins/messaging/*.py
chmod +x scheduling/*.sh

# Initialize database
echo
echo "Initializing database..."
mkdir -p data
sqlite3 data/tracker.db < schema/init.sql

# Install Python dependencies
echo
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

echo
echo "Setup complete!"
echo
echo "Next steps:"
echo "1. Edit config files with your credentials"
echo "2. Run: ./plugins/hosting/start_${HOSTING}.sh"
echo "3. Set up cron: crontab -e"
echo "   Add: 0 * * * * /path/to/scheduling/check_reminders.sh"
