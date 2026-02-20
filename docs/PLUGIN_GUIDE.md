# Writing Plugins

## Messaging Plugin

Create `plugins/messaging/your_backend_send.py`:

```python
#!/usr/bin/env python3
import sys, json, os

# 1. Read config from MESSAGING_CONFIG env var
# 2. Read JSON from stdin
# 3. Send message via your API
# 4. Print JSON result to stdout
# 5. Exit 0 on success, 1 on failure
```

Test it:
```bash
echo '{"phone":"+1234","message":"test"}' | python3 plugins/messaging/your_backend_send.py
```

## Schedule Config

Create `config/schedules/your_protocol.conf`:
```ini
[metadata]
name = Your Protocol Name
registration_field = start_date

[visit_1]
name = First Visit
offset_weeks = 0
window_start = 0
window_end = 4
reminder_days = 7,2
```

Test it:
```bash
python3 core/calc_visits.py --config config/schedules/your_protocol.conf --start-date 2024-01-15
```

## Success Criteria
- Works with existing pipeline
- No changes to core Python code
- Passes interface tests
