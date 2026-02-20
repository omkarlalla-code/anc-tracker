#!/bin/bash
# Cron job: check for due reminders and send them
# Run every hour: 0 * * * * /path/to/check_reminders.sh

set -e

DB_PATH="${DB_PATH:-$HOME/anc/data/tracker.db}"
MESSAGING_PLUGIN="${MESSAGING_PLUGIN:-plugins/messaging/whatsapp_send.py}"
LOG_DIR="${LOG_DIR:-$HOME/anc/logs}"

mkdir -p "$LOG_DIR"
LOGFILE="$LOG_DIR/reminders_$(date +%Y%m%d).log"

echo "[$(date)] Starting reminder check" >> "$LOGFILE"

# Find reminders due in next hour
sqlite3 "$DB_PATH" << EOF | while IFS='|' read reminder_id patient_id phone message; do
SELECT r.reminder_id, p.patient_id, p.phone_encrypted,
    'Reminder: Visit ' || v.visit_name || ' on ' || v.scheduled_date
FROM reminders r
JOIN visits v ON r.visit_id = v.visit_id
JOIN patients p ON v.patient_id = p.patient_id
WHERE r.status = 'pending'
  AND r.scheduled_time <= datetime('now', '+1 hour')
  AND r.scheduled_time > datetime('now', '-1 hour');
EOF

    # Decrypt phone (TODO: implement decryption)
    phone_decrypted="$phone"  # Placeholder

    # Create JSON payload
    payload=$(jq -n \
      --arg phone "$phone_decrypted" \
      --arg message "$message" \
      --arg patient_id "$patient_id" \
      '{phone: $phone, message: $message, patient_id: $patient_id}')

    # Send via plugin
    if echo "$payload" | python3 "$MESSAGING_PLUGIN" >> "$LOGFILE" 2>&1; then
        # Mark as sent
        sqlite3 "$DB_PATH" "UPDATE reminders SET status='sent', sent_time=CURRENT_TIMESTAMP WHERE reminder_id=$reminder_id"
        echo "[$(date)] Sent reminder $reminder_id to $patient_id" >> "$LOGFILE"
    else
        echo "[$(date)] Failed to send reminder $reminder_id" >> "$LOGFILE"
    fi
done

echo "[$(date)] Reminder check complete" >> "$LOGFILE"
