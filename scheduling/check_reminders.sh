#!/bin/bash
# Cron job: check for due reminders and send them
# Run every hour: 0 * * * * /path/to/check_reminders.sh

set -e

# Load encryption key and any other env vars from .env if present
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
[ -f "$SCRIPT_DIR/.env" ] && source "$SCRIPT_DIR/.env"

DB_PATH="${DB_PATH:-$HOME/anc/data/tracker.db}"
MESSAGING_PLUGIN="${MESSAGING_PLUGIN:-plugins/messaging/whatsapp_send.py}"
LOG_DIR="${LOG_DIR:-$HOME/anc/logs}"

mkdir -p "$LOG_DIR"
LOGFILE="$LOG_DIR/reminders_$(date +%Y%m%d).log"

echo "[$(date)] Starting reminder check" >> "$LOGFILE"

sqlite3 "$DB_PATH" << EOF | while IFS='|' read reminder_id patient_id phone reminder_type message; do
SELECT r.reminder_id, p.patient_id, p.phone_encrypted, r.reminder_type,
    'Reminder: Visit ' || v.visit_name || ' on ' || v.scheduled_date
FROM reminders r
JOIN visits v ON r.visit_id = v.visit_id
JOIN patients p ON v.patient_id = p.patient_id
WHERE r.status = 'pending'
  AND r.scheduled_time <= datetime('now', '+1 hour')
  AND r.scheduled_time > datetime('now', '-1 hour');
EOF

    # Decrypt phone number using pysodium secretbox
    phone_decrypted=$(python3 "$SCRIPT_DIR/core/crypto.py" decrypt "$phone" 2>> "$LOGFILE")
    if [ $? -ne 0 ] || [ -z "$phone_decrypted" ]; then
        echo "[$(date)] Failed to decrypt phone for reminder $reminder_id — skipping" >> "$LOGFILE"
        sqlite3 "$DB_PATH" "UPDATE reminders SET status='failed', error_message='decryption_failed' WHERE reminder_id=?" "$reminder_id"
        continue
    fi

    payload=$(jq -n \
      --arg phone "$phone_decrypted" \
      --arg message "$message" \
      --arg patient_id "$patient_id" \
      --arg reminder_type "$reminder_type" \
      '{phone: $phone, message: $message, patient_id: $patient_id, reminder_type: $reminder_type}')

    if echo "$payload" | python3 "$MESSAGING_PLUGIN" >> "$LOGFILE" 2>&1; then
        sqlite3 "$DB_PATH" "UPDATE reminders SET status='sent', sent_time=CURRENT_TIMESTAMP WHERE reminder_id=?" "$reminder_id"
        echo "[$(date)] Sent reminder $reminder_id to $patient_id" >> "$LOGFILE"
    else
        echo "[$(date)] Failed to send reminder $reminder_id" >> "$LOGFILE"
        sqlite3 "$DB_PATH" "UPDATE reminders SET status='failed', error_message='plugin_error' WHERE reminder_id=?" "$reminder_id"
    fi
done

echo "[$(date)] Reminder check complete" >> "$LOGFILE"
