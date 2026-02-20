# Deployment Guide

## Raspberry Pi + Tailscale (Default)

### 1. Install Tailscale
```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

### 2. Clone & Setup
```bash
git clone https://github.com/you/health-tracker
cd health-tracker
./scripts/setup.sh
```

### 3. Configure Messaging
Edit `config/messaging/whatsapp.json` with your WhatsApp Business API credentials.

### 4. Start Dashboard
```bash
./plugins/hosting/start_tailscale.sh
```
Access at: `http://your-pi.tailnet-name.ts.net:8080`

### 5. Setup Cron
```bash
crontab -e
# Add:
0 * * * * /home/pi/health-tracker/scheduling/check_reminders.sh
```

## Alternative: Cloud VPS

Same steps, but use:
```bash
./plugins/hosting/start_cloudflare.sh
# or
./plugins/hosting/start_public.sh
```
