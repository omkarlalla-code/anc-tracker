#!/usr/bin/env python3
"""Generate visit schedule from config file.

Usage: ./calc_visits.py --config anc.conf --start-date 2024-01-15
Output: JSON with visit dates
"""
import sys
import argparse
import configparser
from datetime import datetime, timedelta
import json


def parse_schedule_config(config_path):
    """Parse schedule .conf file"""
    config = configparser.ConfigParser()
    config.read(config_path)

    visits = []
    for section in config.sections():
        if section.startswith('visit_'):
            visits.append({
                'number': section.split('_')[1],
                'name': config[section]['name'],
                'offset_weeks': int(config[section]['offset_weeks']),
                'window_start': int(config[section].get('window_start', 0)),
                'window_end': int(config[section].get('window_end', 999)),
                'description': config[section].get('description', ''),
                'reminder_days': [int(x) for x in config[section].get('reminder_days', '7,2').split(',') if x.strip().isdigit()]
            })

    return visits


def calculate_visit_dates(start_date, visits):
    """Calculate actual dates for each visit"""
    start = datetime.strptime(start_date, "%Y-%m-%d")

    schedule = []
    for visit in visits:
        visit_date = start + timedelta(weeks=visit['offset_weeks'])
        schedule.append({
            'visit_number': visit['number'],
            'visit_name': visit['name'],
            'scheduled_date': visit_date.strftime("%Y-%m-%d"),
            'window_start': (start + timedelta(weeks=visit['window_start'])).strftime("%Y-%m-%d"),
            'window_end': (start + timedelta(weeks=visit['window_end'])).strftime("%Y-%m-%d"),
            'description': visit['description'],
            'reminder_days': visit['reminder_days']
        })

    return schedule


def main():
    parser = argparse.ArgumentParser(description='Generate visit schedule')
    parser.add_argument('--config', required=True, help='Schedule config file')
    parser.add_argument('--start-date', required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--patient-id', help='Patient ID')

    args = parser.parse_args()

    try:
        visits = parse_schedule_config(args.config)
        schedule = calculate_visit_dates(args.start_date, visits)

        output = {
            'patient_id': args.patient_id,
            'start_date': args.start_date,
            'visits': schedule
        }

        print(json.dumps(output, indent=2))
        return 0

    except Exception as e:
        sys.stderr.write(f"Error: {e}\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
