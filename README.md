# Gmail Rules Engine

A Python application that integrates with Gmail API to automate email processing based on configurable rules. Designed with maintainability in mind — using token caching, an authentication wrapper, and a config-driven rules engine.

# Description

This project automates Gmail email processing by:
- Fetching and caching emails locally from the Gmail API
- Applying rules (defined in a JSON config file)
- Executing matching actions (e.g. mark as read, move to label)
- Ensuring emails are processed only once per rule group using persistent tracking

# Features

- **Google OAuth 2.0** Integration with token caching
- **Config-driven** Rules Engine
- **Supports multiple rule groups** in a single run
- **Skips already-processed** email-rule combinations
- **Modular** codebase for easy testing and extension
- Includes **unit and integration** tests

# Installation

1. Clone the repositpory
```
git clone https://github.com/kannangr21/gmail-rules-engine.git
cd gmail-rules-engine
```

2. Create a Virtual Environment
```
virtualenv .venv
source .venv/bin/activate 
```

3. Install Dependencies
```
pip install -r requirements.txt
```

4. Setup Gmail API Access
- Go to Google Cloud Console
- Enable the Gmail API
- Create OAuth 2.0 Credentials (App Type: Desktop)
- Download the `credentials.json` and place it in the project root

# Usage
To fetch emails from Gmail, use:
```
python fetch_emails.py
```
This will:
1. Authenticate with Gmail
2. Fetch and cache new emails in emails.db (default: 10 emails)

To specify the number of emails to fetch, pass it as a system argument:
```
python fetch_emails.py 25
```

To process emails according to rules:
```
python process_rules.py
```
This will:
1. Load rules from rules.json
2. Apply rules to cached emails
3. Skip previously processed combinations using tracking  
4. Perform actions on matched emails

# Configuration

`rules.json`
```
[
  {
    "predicate": "any",
    "rules": [
      {
        "field": "subject",
        "predicate": "contains",
        "value": "test"
      },
      {
        "field": "received_at",
        "predicate": "less_than_days",
        "value": "7"
      }
    ],
    "actions": [
      "mark_as_unread",
      { "type": "move_to_label", "value": "Priority" }
    ]
  },
  {
    "predicate": "all",
    "rules": [
      { "field": "subject", "predicate": "contains", "value": "Invoice" }
    ],
    "actions": [
      { "type": "move_to_label", "value": "Finance" }
    ]
  }
]
```
**predicate**: `"any"` or `"all"` — logical grouping of rule conditions

**rules**: 
- field: subject, sender, message_body, received_at, label_ids
- predicate: contains, equals, does_not_equal, starts_with, ends_with, less_than_days, greater_than_days
- value: The value to match

**actions**: mark_as_read, mark_as_unread, move_to_label

### Email–Rule Processing Tracker

- Processed email-rule combinations are stored in a dedicated SQLite table `processed_rules` to prevent repeated actions. 
- Each rule group is hashed using `md5` for consistent tracking. An additional `processed_at` timestamp is recorded.

1. Unprocessed emails getting processed and the actions being executed  

![Unprocessed Email Processing](./screenshots/unprocessed.png)

2. Emails not getting re-processed

![Avoiding reprocessing of emails](./screenshots/processed.png)

3. Emails being tracked in the database to avoid reprocessing

![Process Rules Table](./screenshots/processed_rules.png)

# Testing

- Unit tests (e.g., predicate evaluations)
- Integration tests (e.g., end-to-end rule execution)  
- `pytest tests/ -v` will run the test cases  

![Test cases](./screenshots/tests_screenshot.png)

# Structure
```
.
├── fetch_emails.py          # Email fetching, authentication & SQLite insertion
├── process_rules.py         # Core rules engine logic with predicates & actions
├── credentials.json         # Your OAuth credentials
├── token.json               # Cached access/refresh tokens
├── emails.db                # SQLite database for storing fetched emails
├── rules.json               # Rule configuration file
│
├── tests/
│   ├── test_evaluate.py     # Unit tests for rule evaluation
│   └── test_process_rules.py# Integration tests
│
├── requirements.txt         # All dependencies
└── README.md
```
