#!/usr/bin/env python3
"""Telegram messaging plugin - same interface as whatsapp_send.py."""
import sys
import json
import os
from datetime import datetime
import requests


def send_telegram(config, data):
    if os.getenv("DRY_RUN") == "1":
        return {
            "status": "sent",
            "message_id": "dry_run",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    bot_token = config["bot_token"]
    chat_id   = data["phone"]  # for Telegram: phone field carries the chat_id
    text      = data["message"]

    url = f"{config['api_url']}{bot_token}/sendMessage"
    resp = requests.post(url, json={"chat_id": chat_id, "text": text})

    if resp.status_code == 200:
        result = resp.json().get("result", {})
        return {
            "status": "sent",
            "message_id": str(result.get("message_id", "")),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    else:
        raise Exception(f"Telegram API error {resp.status_code}: {resp.text}")


if __name__ == "__main__":
    try:
        config_path = os.getenv("MESSAGING_CONFIG", "config/messaging/telegram.json")
        with open(config_path) as f:
            config = json.load(f)
        data = json.load(sys.stdin)
        result = send_telegram(config, data)
        print(json.dumps(result))
        sys.exit(0)
    except Exception as e:
        error = {
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        print(json.dumps(error))
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)
