# Architecture

## Pipeline Design

```
Registration -> calc_visits.py -> DB -> cron -> list_due_today.py -> format_message -> send_plugin
```

## Components

- **core/**: Pure Python, no side effects, reads config
- **plugins/messaging/**: Swappable message senders (stdin/stdout)
- **plugins/hosting/**: Swappable deployment scripts
- **config/schedules/**: INI files defining visit schedules
- **scheduling/**: Cron-based orchestration scripts
- **dashboard/**: Static HTML + JS frontend

## Data Flow

1. Patient registered with start_date (LMP, birth, diagnosis)
2. `calc_visits.py` reads schedule config, generates visit dates
3. Visit records inserted into SQLite
4. Cron runs `check_reminders.sh` hourly
5. Due reminders piped through messaging plugin
6. Dashboard queries SQLite for live stats
