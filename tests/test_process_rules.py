import pytest
import sys
import os

from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rules_engine import process_rules

def test_matching_rule_triggers_action():
    mock_email = {
        "id": "abc123",
        "subject": "Urgent: Something happened",
        "sender": "sender@example.com",
        "recipient": "me@example.com",
        "message_body": "Hello",
        "received_at": "2024-06-26 12:00:00",
        "label_ids": [],
        "is_read": 0
    }

    mock_rules = {
        "predicate": "any",
        "rules": [{
            "field": "subject",
            "predicate": "contains",
            "value": "urgent"
        }],
        "actions": ["mark_as_read"]
    }

    with patch("rules_engine.process_rules.fetch_emails", return_value=[mock_email]), \
         patch("rules_engine.process_rules.load_rules", return_value=mock_rules), \
         patch("rules_engine.process_rules.authenticate_gmail", return_value=MagicMock()), \
         patch.dict("rules_engine.process_rules.ACTIONS", {}, clear=True) as mock_actions:

        called = {"fired": False}

        def fake_action(email, svc, val):
            if email["id"] == "abc123":
                called["fired"] = True

        mock_actions["mark_as_read"] = fake_action

        process_rules.process_emails()
        assert called["fired"] is True
