import pytest
import sys
import os
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from process_rules import evaluate_rule

# Sample mock email (matches structure from your DB)
mock_email = {
    "subject": "Urgent Invoice Pending",
    "sender": "billing@company.com",
    "recipient": "you@example.com",
    "message_body": "Please process the invoice",
    "received_at": "2024-06-25 15:00:00",
}

def test_subject_contains():
    rule = {
        "field": "subject",
        "predicate": "contains",
        "value": "invoice"
    }
    assert evaluate_rule(mock_email, rule) is True

def test_sender_equals_fail():
    rule = {
        "field": "sender",
        "predicate": "equals",
        "value": "hr@example.com"
    }
    assert evaluate_rule(mock_email, rule) is False

def test_message_body_does_not_contain():
    rule = {
        "field": "message_body",
        "predicate": "does_not_contain",
        "value": "salary"
    }
    assert evaluate_rule(mock_email, rule) is True

def test_subject_does_not_equal():
    rule = {
        "field": "subject",
        "predicate": "does_not_equal",
        "value": "Meeting Notes"
    }
    assert evaluate_rule(mock_email, rule) is True

def test_invalid_field():
    rule = {
        "field": "invalid_field",
        "predicate": "contains",
        "value": "test"
    }
    assert evaluate_rule(mock_email, rule) is False

def test_invalid_predicate():
    rule = {
        "field": "subject",
        "predicate": "unsupported_predicate",
        "value": "invoice"
    }
    assert evaluate_rule(mock_email, rule) is False

def test_case_insensitive():
    rule = {
        "field": "subject",
        "predicate": "contains",
        "value": "INVOICE"
    }
    assert evaluate_rule(mock_email, rule) is True

def test_received_at_less_than_days():
    # Create a recent date (2 days ago) with timezone
    recent_date = (datetime.now() - timedelta(days=2)).strftime("%a, %d %b %Y %H:%M:%S +0000")
    email_with_recent_date = mock_email.copy()
    email_with_recent_date["received_at"] = recent_date
    
    rule = {
        "field": "received_at",
        "predicate": "less_than_days",
        "value": "7"
    }
    assert evaluate_rule(email_with_recent_date, rule) is True

def test_received_at_greater_than_days():
    # Create an old date (30 days ago) with timezone
    old_date = (datetime.now() - timedelta(days=30)).strftime("%a, %d %b %Y %H:%M:%S +0000")
    email_with_old_date = mock_email.copy()
    email_with_old_date["received_at"] = old_date
    
    rule = {
        "field": "received_at",
        "predicate": "greater_than_days",
        "value": "7"
    }
    assert evaluate_rule(email_with_old_date, rule) is True

def test_received_at_less_than_days_fail():
    # Create an old date (10 days ago) with timezone
    old_date = (datetime.now() - timedelta(days=10)).strftime("%a, %d %b %Y %H:%M:%S +0000")
    email_with_old_date = mock_email.copy()
    email_with_old_date["received_at"] = old_date
    
    rule = {
        "field": "received_at",
        "predicate": "less_than_days",
        "value": "7"
    }
    assert evaluate_rule(email_with_old_date, rule) is False

def test_received_at_invalid_date():
    email_with_invalid_date = mock_email.copy()
    email_with_invalid_date["received_at"] = "invalid-date-format"
    
    rule = {
        "field": "received_at",
        "predicate": "less_than_days",
        "value": "7"
    }
    assert evaluate_rule(email_with_invalid_date, rule) is False

def test_received_at_empty_date():
    email_with_empty_date = mock_email.copy()
    email_with_empty_date["received_at"] = ""
    
    rule = {
        "field": "received_at",
        "predicate": "less_than_days",
        "value": "7"
    }
    assert evaluate_rule(email_with_empty_date, rule) is False
