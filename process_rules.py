import json
import sqlite3
from datetime import datetime
from fetch_emails import authenticate_gmail

"""
---------- Util functions ----------
"""
def _is_less_than_days(field, value):
    """Check if email was received less than X days ago"""
    if not field:
        return False
    try:
        date_obj = datetime.strptime(field, "%a, %d %b %Y %H:%M:%S %z")
        today = datetime.now(date_obj.tzinfo)
        days_diff = (today - date_obj).days
        return days_diff < int(value)
    except (ValueError, TypeError):
        return False

def _is_greater_than_days(field, value):
    """Check if email was received more than X days ago"""
    if not field:
        return False
    try:
        date_obj = datetime.strptime(field, "%a, %d %b %Y %H:%M:%S %z")
        today = datetime.now(date_obj.tzinfo)
        days_diff = (today - date_obj).days
        return days_diff > int(value)
    except (ValueError, TypeError):
        return False

def load_rules():
    """
    Load email processing rules from rules.json file
    Returns: Dictionary containing rules configuration
    """
    try:
        with open("rules.json") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading rules: {e}")
        raise


"""
---------- Action functionalities ----------
"""
def mark_as_read(email_id, service):
    print(f"Invoked mark as read for: {email_id}")
    service.users().messages().modify(
        userId='me',
        id=email_id,
        body={"removeLabelIds": ["UNREAD"]}
    ).execute()


def mark_as_unread(email_id, service):
    print(f"Invoked mark as unread for: {email_id}")
    service.users().messages().modify(
        userId='me',
        id=email_id,
        body={"addLabelIds": ["UNREAD"]}
    ).execute()

def move_to_label(email_id, service, label_name):
    print(f"Invoked move to label for: {email_id}")
    labels = service.users().labels().list(userId='me').execute().get('labels', [])
    label_id = next((l['id'] for l in labels if l['name'].lower() == label_name.lower()), None)
    if not label_id:
        label = service.users().labels().create(
            userId='me',
            body={"name": label_name, "labelListVisibility": "labelShow", "messageListVisibility": "show"}
        ).execute()
        label_id = label['id']
    service.users().messages().modify(
        userId='me',
        id=email_id,
        body={"addLabelIds": [label_id]}
    ).execute()


"""
---------- RULE PROCESSORS ----------
"""
ACTIONS = {
    "mark_as_read": lambda email, svc, _: mark_as_read(email["id"], svc),
    "mark_as_unread": lambda email, svc, _: mark_as_unread(email["id"], svc),
    "move_to_label": lambda email, svc, val: move_to_label(email["id"], svc, val)
}

PREDICATES = {
    "contains": lambda field, value: value.lower() in (field or "").lower(),
    "does_not_contain": lambda field, value: value.lower() not in (field or "").lower(),
    "equals": lambda field, value: (field or "").lower() == value.lower(),
    "does_not_equal": lambda field, value: (field or "").lower() != value.lower(),
    "starts_with": lambda field, value: (field or "").lower().startswith(value.lower()),
    "ends_with": lambda field, value: (field or "").lower().endswith(value.lower()),
    "less_than_days": lambda field, value: _is_less_than_days(field, value),
    "greater_than_days": lambda field, value: _is_greater_than_days(field, value)
}

FIELD_MAPPERS = {
    "subject": lambda email: email.get("subject", ""),
    "sender": lambda email: email.get("sender", ""),
    "recipient": lambda email: email.get("recipient", ""),
    "message_body": lambda email: email.get("message_body", ""),
    "received_at": lambda email: email.get("received_at", ""),
    "label_ids": lambda email: email.get("label_ids", "")
}


"""
---------- Database function ----------
"""
def fetch_emails():
    """
    Fetch all emails from SQLite database
    """
    try:
        conn = sqlite3.connect("emails.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM emails")
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        return results
    except Exception as e:
        print(f"Error fetching emails: {e}")
        raise


"""
---------- Core rule evaluation functions ----------
"""
def evaluate_rule(email, rule):
    """
    Evaluate if an email field matches a rule condition
    Args:
        field_value: The email field value to check
        rule: The rule to evaluate
    """
    field = rule["field"]
    predicate = rule["predicate"]
    value = rule["value"]

    if field not in FIELD_MAPPERS or predicate not in PREDICATES:
        return False

    field_value = FIELD_MAPPERS[field](email)
    return PREDICATES[predicate](field_value, value)


def process_emails():
    try:
        service = authenticate_gmail()
        rule_master = load_rules()
        predicate_mode = rule_master.get("predicate", "all")
        rules = rule_master.get("rules", [])
        actions = rule_master.get("actions", [])

        emails = fetch_emails()

        for email in emails:
            condition_results = [evaluate_rule(email, r) for r in rules]
            match = all(condition_results) if predicate_mode == "all" else any(condition_results)

            if match:
                print(f"Match: {email['subject']}")
                for action in actions:
                    if isinstance(action, dict):
                        action_type = action["type"]
                        action_value = action.get("value", None)
                    else:
                        action_type = action
                        action_value = None

                    print(f"Attempting to run action: {action_type} with value: {action_value}")

                    if action_type in ACTIONS:
                        try:
                            ACTIONS[action_type](email, service, action_value)
                            print(f"Action '{action_type}' executed.")
                        except Exception as e:
                            print(f"Error executing '{action_type}': {e}")
    except Exception as e:
        print(f"Error in process_emails: {e}")
        raise


"""  
---------- Execution ----------
"""
if __name__ == "__main__":
    process_emails()
