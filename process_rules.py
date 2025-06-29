import json
import sqlite3
from datetime import datetime, timedelta
from fetch_emails import authenticate_gmail

def load_rules():
    """
    Load email processing rules from rules.json file
    Returns: Dictionary containing rules configuration
    """
    try:
        with open("rules.json") as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: rules.json file not found")
        raise
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in rules.json: {e}")
        raise
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
        print(f"Fetched {len(results)} emails from database")
        return results
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        raise
    except Exception as e:
        print(f"Error fetching emails: {e}")
        raise

def evaluate_condition(field_value, predicate, rule_value):
    """
    Evaluate if an email field matches a rule condition
    Args:
        field_value: The email field value to check
        predicate: The comparison operator (contains, equals, etc.)
        rule_value: The value to compare against
    Returns: Boolean indicating if condition is met
    """
    # Handle None/empty values
    field_value = field_value or ""
    rule_value = rule_value or ""

    # String comparison predicates
    if predicate == "contains":
        return rule_value.lower() in field_value.lower()
    if predicate == "does_not_contain":
        return rule_value.lower() not in field_value.lower()
    if predicate == "equals":
        return field_value.lower() == rule_value.lower()
    if predicate == "does_not_equal":
        return field_value.lower() != rule_value.lower()
    
    # Date comparison predicates
    if "received_at" in field_value:
        try:
            # Parse the date string from email header
            date_obj = datetime.strptime(field_value, "%a, %d %b %Y %H:%M:%S %z")
        except ValueError:
            print(f"Warning: Could not parse date: {field_value}")
            return False

        # Calculate days difference
        today = datetime.now(date_obj.tzinfo)
        days_diff = (today - date_obj).days

        if predicate == "less_than_days":
            return days_diff < int(rule_value)
        if predicate == "greater_than_days":
            return days_diff > int(rule_value)

    return False

def apply_actions(email, actions, service):
    """
    Apply specified actions to an email
    Args:
        email: Email dictionary containing email data
        actions: List of actions to perform
        service: Authenticated Gmail API service
    """
    msg_id = email['id']

    for action in actions:
        try:
            if action == "mark_as_read":
                # Remove UNREAD label to mark as read
                service.users().messages().modify(
                    userId='me',
                    id=msg_id,
                    body={"removeLabelIds": ["UNREAD"]}
                ).execute()
                print(f"Marked as READ: {email['subject']}")

            elif action == "mark_as_unread":
                # Add UNREAD label to mark as unread
                service.users().messages().modify(
                    userId='me',
                    id=msg_id,
                    body={"addLabelIds": ["UNREAD"]}
                ).execute()
                print(f"Marked as UNREAD: {email['subject']}")

            elif action.startswith("move_to_label:"):
                # Extract label name from action
                label_name = action.split(":")[1]
                
                # Get existing labels to check if label already exists
                existing_labels = service.users().labels().list(userId='me').execute().get('labels', [])
                label_id = None
                
                # Find existing label by name (case-insensitive)
                for label in existing_labels:
                    if label['name'].lower() == label_name.lower():
                        label_id = label['id']
                        break

                # Create label if it doesn't exist
                if not label_id:
                    try:
                        created_label = service.users().labels().create(
                            userId='me',
                            body={"name": label_name, "labelListVisibility": "labelShow", "messageListVisibility": "show"}
                        ).execute()
                        label_id = created_label['id']
                        print(f"Created new label: {label_name}")
                    except Exception as e:
                        print(f"Error creating label '{label_name}': {e}")
                        continue

                # Apply the label to the email
                service.users().messages().modify(
                    userId='me',
                    id=msg_id,
                    body={"addLabelIds": [label_id]}
                ).execute()
                print(f"Moved to label '{label_name}': {email['subject']}")
                
            else:
                print(f"Warning: Unknown action '{action}'")
                
        except Exception as e:
            print(f"Error applying action '{action}' to email {email['subject']}: {e}")

def process_emails():
    """
    Main function to process emails according to rules
    """
    try:
        # Load rules configuration
        rules_config = load_rules()

        # Fetch emails from database
        emails = fetch_emails()
        
        # Authenticate with Gmail API
        service = authenticate_gmail()

        # Extract configuration parameters
        predicate_mode = rules_config.get("predicate", "all")
        rule_blocks = rules_config.get("rules", [])
        actions = rules_config.get("actions", [])

        print(f"Processing {len(emails)} emails with {len(rule_blocks)} rules")
        print(f"Predicate mode: {predicate_mode}")
        print(f"Actions: {actions}")

        processed_count = 0
        
        # Process each email
        for email in emails:
            try:
                conditions = []

                # Evaluate each rule against the email
                for rule in rule_blocks:
                    field = rule['field']
                    predicate = rule['predicate']
                    value = rule['value']
                    email_value = email.get(field, "")
                    conditions.append(evaluate_condition(email_value, predicate, value))

                # Determine if email matches rules based on predicate mode
                match = all(conditions) if predicate_mode == "all" else any(conditions)

                # Apply actions if email matches rules
                if match:
                    print(f"Processing email: {email['subject']}")
                    apply_actions(email, actions, service)
                    processed_count += 1
                    
            except Exception as e:
                print(f"Error processing email {email.get('subject', 'Unknown')}: {e}")
                continue

        print(f"Processing complete. {processed_count} emails processed.")
        
    except Exception as e:
        print(f"Error in process_emails: {e}")
        raise

if __name__ == "__main__":
    try:
        process_emails()
    except Exception as e:
        print(f"Script failed: {e}")
        exit(1)
