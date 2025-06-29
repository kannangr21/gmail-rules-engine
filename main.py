from fetch_emails import fetch_and_store_emails
from database.db import init_db
from rules_engine.process_rules import process_emails

import sys

def main():
    """
    Main function that orchestrates the Gmail Rules Engine workflow.
    """
    try:
        
        if len(sys.argv) > 1:
            emails_count = sys.argv[1]
        else:
            emails_count = 10                # Fetch 10 emails by default
        init_db()                            # Setup database if not exists
        fetch_and_store_emails(emails_count) # Fetch and store emails from Gmail
        process_emails()                     # Run rules engine and update emails as per actions 
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Entry point when script is run directly
    main()
    
