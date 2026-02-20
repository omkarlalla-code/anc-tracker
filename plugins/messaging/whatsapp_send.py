#!/usr/bin/env python3
"""WhatsApp messaging plugin."""
import sys
import json
import os
from datetime import datetime
import requests


def send_whatsapp(config, data):
    """Send via WhatsApp Business API"""
    if os.getenv('DRY_RUN') == '1':
        return {
            'status': 'sent',
            'message_id': 'dry_run',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }

    url = f"{config['api_url']}"
    headers = {
        'Authorization': f"Bearer {config['access_token']}",
        'Content-Type': 'application/json'
    }

    payload = {
        'messaging_product': 'whatsapp',
        'to': data['phone'],
        'type': 'template',
        'template': {
            'name': config['templates'][data['reminder_type']],
            'language': {'code': 'en'}
        }
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        return {
            'status': 'sent',
            'message_id': response.json().get('messages', [{}])[0].get('id'),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    else:
        raise Exception(f"API error: {response.text}")


if __name__ == '__main__':
    try:
        # Load config
        config_path = os.getenv('MESSAGING_CONFIG', 'config/messaging/whatsapp.json')
        with open(config_path) as f:
            config = json.load(f)

        # Read input from stdin
        data = json.load(sys.stdin)

        # Send message
        result = send_whatsapp(config, data)
        print(json.dumps(result))
        sys.exit(0)

    except Exception as e:
        error = {
            'status': 'failed',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        print(json.dumps(error))
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)
