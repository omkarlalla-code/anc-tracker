#!/usr/bin/env python3
"""List patients with visits due today.

Usage: ./list_due_today.py /path/to/database.db
Output: JSON lines with patient_id, visit info
"""
import sys
import sqlite3
import json
from datetime import date


def main():
    if len(sys.argv) != 2:
        sys.stderr.write(f"Usage: {sys.argv[0]} <database_path>\n")
        return 1

    db_path = sys.argv[1]

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        today = date.today().isoformat()

        sql = """
            SELECT patient_id, visit_number, visit_name, scheduled_date
            FROM visits
            WHERE DATE(scheduled_date) = ? AND status = 'pending'
        """

        cursor.execute(sql, (today,))

        for row in cursor.fetchall():
            result = {
                'patient_id': row[0],
                'visit_number': row[1],
                'visit_name': row[2],
                'date': row[3]
            }
            print(json.dumps(result))

        conn.close()
        return 0

    except sqlite3.Error as e:
        sys.stderr.write(f"Database error: {e}\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
