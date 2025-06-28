import sqlite3

def init_db():
    """
    Initialize SQLite database for storing email data
    Creates emails table if it doesn't exist
    """
    # Connect to SQLite database (creates it if doesn't exist)
    conn = sqlite3.connect("emails.db")
    cursor = conn.cursor()
    
    # Create emails table with all required fields
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS emails (
            id TEXT PRIMARY KEY,          -- Gmail message ID
            thread_id TEXT,               -- Gmail thread ID
            sender TEXT,                  -- Email sender address
            recipient TEXT,               -- Email recipient address
            subject TEXT,                 -- Email subject line
            snippet TEXT,                 -- Email preview text
            message_body TEXT,            -- Full email body content
            received_at TEXT,             -- Email received timestamp
            is_read BOOLEAN,              -- Flag to mark the read status
            label_ids TEXT                -- Comma-separated Gmail label IDs
        )
    ''')
    
    # Commit changes and close connection
    conn.commit()
    conn.close()

if __name__ == '__main__':
    # Run database initialization when script is executed directly
    init_db()
