#!/bin/bash
# Generate visit schedule for a patient
# Usage: ./generate_schedule.sh <config> <start-date> <patient-id>

set -e

CONFIG="${1:?Usage: $0 <config_file> <start_date> <patient_id>}"
START_DATE="${2:?Missing start date}"
PATIENT_ID="${3:?Missing patient ID}"

python3 core/calc_visits.py \
    --config "$CONFIG" \
    --start-date "$START_DATE" \
    --patient-id "$PATIENT_ID"
