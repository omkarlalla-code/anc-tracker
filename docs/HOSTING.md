# Hosting Options

## Tailscale VPN (Default/Recommended)
- No port forwarding needed
- Works behind rural NAT/firewalls
- Encrypted mesh network
- Free for up to 100 devices

## Cloudflare Tunnel
- Public URL without opening ports
- Built-in DDoS protection
- Free tier available

## ngrok
- Quick temporary public URLs
- Good for demos/testing

## Public IP + nginx
- Traditional hosting
- Requires static IP
- Let's Encrypt SSL

## Cloud VPS
- Deploy to AWS/Digital Ocean
- Use cloud SQLite or migrate to Postgres
- Scales beyond Pi capacity

All options require changing only deployment scripts, not core code.
