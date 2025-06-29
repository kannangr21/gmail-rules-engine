import json
import sqlite3
from fetch_emails import authenticate_gmail
from rules_engine.predicates import PREDICATES
from rules_engine.fields import FIELD_MAPPERS
from rules_engine.actions import ACTIONS

def load_rules():
    """
    Load email processing rules from rules.json file
    Returns: Dictionary containing rules configuration
    """
    try:
        with open("rules_engine/rules.json") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading rules: {e}")
        raise

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
