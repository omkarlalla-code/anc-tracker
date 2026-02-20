# Messaging Plugin Interface

All messaging plugins MUST accept this standard input format on stdin:

```json
{
  "phone": "+919876543210",
  "message": "Reminder: ANC visit tomorrow at 10am",
  "patient_id": "P001",
  "visit_number": 2,
  "reminder_type": "2day"
}
```

## Output Format

**Success:**
```json
{"status": "sent", "message_id": "abc123", "timestamp": "2024-01-15T10:30:00Z"}
```

**Failure:**
```json
{"status": "failed", "error": "Invalid phone number", "timestamp": "2024-01-15T10:30:00Z"}
```

## Error Handling
- Exit code 0 = success
- Exit code 1 = failure
- All errors to stderr

## Environment Variables
- `MESSAGING_CONFIG`: Path to config JSON
- `DRY_RUN`: If set to "1", don't actually send
