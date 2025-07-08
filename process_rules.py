import json
import sqlite3
from datetime import datetime
from fetch_emails import authenticate_gmail
import hashlib

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
def init_tracking_table():
    """
    Initialize table to track processed rules if not exists
    """
    conn = sqlite3.connect("emails.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS processed_rules (
            email_id TEXT,
            rule_hash TEXT,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (email_id, rule_hash)
        )
    """)
    conn.commit()
    conn.close()

def already_processed(email_id, rule_hash):
    """
    Function to return the status of the rule processed on a specific email
    """
    conn = sqlite3.connect("emails.db")
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM processed_rules WHERE email_id = ? AND rule_hash = ?", (email_id, rule_hash))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def mark_processed(email_id, rule_hash):
    """
    Insert an entry for rule processed on the email. Ignore if the rule has been already processed on an email
    """
    conn = sqlite3.connect("emails.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO processed_rules (email_id, rule_hash) VALUES (?, ?)", (email_id, rule_hash))
    conn.commit()
    conn.close()


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
        rule_blocks = load_rules()  # returns a list of rule group dicts
        emails = fetch_emails()

        for rule_config in rule_blocks:
            predicate_mode = rule_config.get("predicate", "all")
            rules = rule_config.get("rules", [])
            actions = rule_config.get("actions", [])

            # Generate the hash for the rule to uniquely map it with the email
            rule_hash = hashlib.md5(json.dumps(rule_config, sort_keys=True).encode()).hexdigest()

            for email in emails:
                # Continue with the action processing logic if the event is not processed already
                if already_processed(email["id"], rule_hash):
                    print(f"Email already processed: {email['subject']}")
                    continue

                condition_results = [evaluate_rule(email, r) for r in rules]
                match = all(condition_results) if predicate_mode == "all" else any(condition_results)

                if match:
                    print(f"Matched (Rule): {email['subject']}")
                    for action in actions:
                        if isinstance(action, dict):
                            action_type = action["type"]
                            action_value = action.get("value")
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
                    # Store the rule processed status in the table
                    mark_processed(email["id"], rule_hash)
                else:
                    print(f"{email['subject']} - rules not matched")

    except Exception as e:
        print(f"Error in process_emails: {e}")
        raise


"""  
---------- Execution ----------
"""
if __name__ == "__main__":
    init_tracking_table()
    process_emails()
