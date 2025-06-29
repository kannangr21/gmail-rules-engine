from fetch_emails import fetch_and_store_emails
from database.db import init_db
from rules_engine.process_rules import process_emails

def main():
    """
    Main function that orchestrates the Gmail Rules Engine workflow.
    """
    try:
        init_db()                # Setup database if not exists
        fetch_and_store_emails() # Fetch and store emails from Gmail
        process_emails()         # Run rules engine and update emails as per actions 
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Entry point when script is run directly
    main()
    
