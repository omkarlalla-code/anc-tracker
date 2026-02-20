-- Enable foreign keys
PRAGMA foreign_keys = ON;

-- Patients table (generic, works for pregnancy/children/chronic)
CREATE TABLE patients (
    patient_id TEXT PRIMARY KEY,
    name_encrypted BLOB NOT NULL,
    phone_encrypted BLOB NOT NULL,
    age INTEGER,
    village TEXT,
    registration_date DATE NOT NULL,
    start_date DATE NOT NULL,  -- LMP/birth/diagnosis date
    consent_given BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Visits table
CREATE TABLE visits (
    visit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id TEXT NOT NULL,
    visit_number INTEGER NOT NULL,
    visit_name TEXT NOT NULL,
    scheduled_date DATE NOT NULL,
    completed_date DATE,
    status TEXT CHECK(status IN ('pending', 'completed', 'missed')) DEFAULT 'pending',
    notes TEXT,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE,
    UNIQUE(patient_id, visit_number)
);

-- Reminders table
CREATE TABLE reminders (
    reminder_id INTEGER PRIMARY KEY AUTOINCREMENT,
    visit_id INTEGER NOT NULL,
    reminder_type TEXT NOT NULL,  -- '7day', '2day', 'missed'
    scheduled_time TIMESTAMP NOT NULL,
    sent_time TIMESTAMP,
    status TEXT CHECK(status IN ('pending', 'sent', 'failed')) DEFAULT 'pending',
    error_message TEXT,
    FOREIGN KEY (visit_id) REFERENCES visits(visit_id) ON DELETE CASCADE
);

-- Encryption key metadata (NOT the key itself)
CREATE TABLE encryption_metadata (
    key_id TEXT PRIMARY KEY,
    algorithm TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    rotated_at TIMESTAMP
);

-- Indexes
CREATE INDEX idx_visits_scheduled ON visits(scheduled_date, status);
CREATE INDEX idx_reminders_pending ON reminders(scheduled_time, status);
CREATE INDEX idx_patient_phone ON patients(phone_encrypted);
