#!/usr/bin/env python3
"""SMS messaging plugin - implements same interface as WhatsApp."""
import sys
import json
import os
from datetime import datetime


def send_sms(config, data):
    """Send via SMS gateway"""
    if os.getenv('DRY_RUN') == '1':
        return {
            'status': 'sent',
            'message_id': 'dry_run',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }

    # TODO: implement actual SMS sending
    raise NotImplementedError("SMS plugin not yet implemented")


if __name__ == '__main__':
    try:
        config_path = os.getenv('MESSAGING_CONFIG', 'config/messaging/sms.json')
        with open(config_path) as f:
            config = json.load(f)

        data = json.load(sys.stdin)
        result = send_sms(config, data)
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
