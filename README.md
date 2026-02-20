# Health Appointment Tracker Template

Unix-style health appointment reminder system with pluggable backends.

**Default:** ANC tracking via WhatsApp on Tailscale
**Customizable:** Any schedule, any messaging, any hosting

## Quick Start
```bash
git clone https://github.com/yourusername/health-tracker
cd health-tracker
./scripts/setup.sh
```

## Requirements
- Python 3.7+
- SQLite3
- pip3

## Features
- Config-driven visit schedules (swap ANC -> vaccination -> diabetes)
- Plugin messaging (WhatsApp/Telegram/Email/SMS)
- Flexible hosting (Tailscale/Cloudflare/public IP)
- Encrypted patient data
- Unix pipeline architecture

## Documentation
- [Architecture](docs/ARCHITECTURE.md)
- [Plugin Guide](docs/PLUGIN_GUIDE.md)
- [Deployment](docs/DEPLOYMENT.md)
