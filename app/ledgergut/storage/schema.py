"""SQLite schema for Ledgergut receipt persistence."""

from __future__ import annotations

RECEIPTS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS receipts (
    record_id TEXT PRIMARY KEY,
    submitted_by TEXT NOT NULL,
    submitted_at TEXT,
    description TEXT NOT NULL,
    project_name TEXT,
    expense_category TEXT,
    currency TEXT,
    paid_by TEXT NOT NULL,
    reimbursement_status TEXT NOT NULL,
    billable_status TEXT,
    invoice_id TEXT,
    payment_notes TEXT,
    assignment_confidence REAL,
    needs_user_review INTEGER NOT NULL,
    review_notes TEXT,
    status TEXT NOT NULL,
    created_at TEXT,
    receipt_payload_json TEXT NOT NULL
)
"""

VALIDATION_FINDINGS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS validation_findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receipt_record_id TEXT NOT NULL,
    rule_id TEXT NOT NULL,
    fields_json TEXT NOT NULL,
    severity TEXT NOT NULL,
    message TEXT NOT NULL,
    requires_human_review INTEGER NOT NULL,
    FOREIGN KEY(receipt_record_id) REFERENCES receipts(record_id) ON DELETE CASCADE
)
"""

CREATE_INDEXES_SQL = (
    "CREATE INDEX IF NOT EXISTS idx_validation_findings_receipt_record_id "
    "ON validation_findings(receipt_record_id)",
)

SCHEMA_STATEMENTS = (
    RECEIPTS_TABLE_SQL,
    VALIDATION_FINDINGS_TABLE_SQL,
    *CREATE_INDEXES_SQL,
)
