#!/usr/bin/env python3
"""
Register a new patient with encrypted PII.

Encrypts name and phone at entry time using core/crypto.py so raw PII
never touches the database. Generates visit schedule via calc_visits.py
and inserts pending reminders automatically — no manual SQL required.

Usage:
  python3 core/register_patient.py \
    --patient-id P004 \
    --name "Jane Doe" \
    --phone "+91XXXXXXXXXX" \
    --age 26 \
    --village "Pune Rural" \
    --lmp 2026-01-15

Environment:
  TRACKER_ENCRYPTION_KEY   32-byte key as hex (source .env)
  DB_PATH                  path to tracker.db (default: data/tracker.db)
  SCHEDULE_CONFIG          path to schedule config (default: config/schedules/anc_who2016.conf)
"""

import argparse
import json
import os
import sqlite3
import subprocess
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from crypto import encrypt


def parse_args():
    p = argparse.ArgumentParser(description='Register a patient with encrypted PII')
    p.add_argument('--patient-id', required=True)
    p.add_argument('--name',       required=True)
    p.add_argument('--phone',      required=True, help='International format: +91XXXXXXXXXX')
    p.add_argument('--age',        type=int, required=True)
    p.add_argument('--village',    required=True)
    p.add_argument('--lmp',        required=True, help='Last menstrual period: YYYY-MM-DD')
    return p.parse_args()


def generate_visits(lmp: str, schedule_config: str) -> list:
    result = subprocess.run(
        ['python3', 'core/calc_visits.py', '--config', schedule_config, '--start-date', lmp],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"calc_visits.py failed: {result.stderr}")
    return json.loads(result.stdout)["visits"]


def insert_patient(conn, patient_id, name_enc, phone_enc, age, village, lmp):
    conn.execute(
        """INSERT INTO patients
           (patient_id, name_encrypted, phone_encrypted, age, village,
            registration_date, start_date, consent_given)
           VALUES (?, ?, ?, ?, ?, date('now'), ?, 1)""",
        (patient_id, name_enc, phone_enc, age, village, lmp)
    )


def insert_visits_and_reminders(conn, patient_id, visits: list):
    for v in visits:
        conn.execute(
            """INSERT INTO visits
               (patient_id, visit_number, visit_name, scheduled_date, status)
               VALUES (?, ?, ?, ?, 'pending')""",
            (patient_id, v['visit_number'], v['visit_name'], v['scheduled_date'])
        )
        visit_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        scheduled_date = datetime.strptime(v['scheduled_date'], '%Y-%m-%d')

        # 7-day reminder
        conn.execute(
            "INSERT INTO reminders (visit_id, reminder_type, scheduled_time, status) VALUES (?, '7day', ?, 'pending')",
            (visit_id, (scheduled_date - timedelta(days=7)).strftime('%Y-%m-%d %H:00:00'))
        )
        # 2-day reminder
        conn.execute(
            "INSERT INTO reminders (visit_id, reminder_type, scheduled_time, status) VALUES (?, '2day', ?, 'pending')",
            (visit_id, (scheduled_date - timedelta(days=2)).strftime('%Y-%m-%d %H:00:00'))
        )
        # Missed visit reminder (fires 1 day after scheduled date if visit not completed)
        conn.execute(
            "INSERT INTO reminders (visit_id, reminder_type, scheduled_time, status) VALUES (?, 'missed', ?, 'pending')",
            (visit_id, (scheduled_date + timedelta(days=1)).strftime('%Y-%m-%d %H:00:00'))
        )


def main():
    args = parse_args()

    db_path = os.environ.get('DB_PATH', 'data/tracker.db')
    schedule_config = os.environ.get('SCHEDULE_CONFIG', 'config/schedules/anc_who2016.conf')

    name_enc = encrypt(args.name)
    phone_enc = encrypt(args.phone)

    visits = generate_visits(args.lmp, schedule_config)

    conn = sqlite3.connect(db_path)
    try:
        insert_patient(conn, args.patient_id, name_enc, phone_enc,
                       args.age, args.village, args.lmp)
        insert_visits_and_reminders(conn, args.patient_id, visits)
        conn.commit()
        print(f"Registered {args.patient_id} with {len(visits)} visits and {len(visits) * 3} reminders.")
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
