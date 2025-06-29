import os
import json
import sqlite3
import base64
import sys

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build


"""
---------- Util functions ----------
"""
def parse_header(headers, name):
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""

def extract_body(payload):
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
    elif 'body' in payload and 'data' in payload['body']:
        return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
    return ""


"""
---------- Google Authentication Call methods ----------
"""
def authenticate_google_api(service_name, version, scopes, token_file="token.json", creds_file="credentials.json"):
    """
    Generic Google API authentication handler.
    Args:
        service_name (str): The name of the Google API (e.g., 'gmail', 'drive')
        version (str): The version of the API (e.g., 'v1')
        scopes (list): List of OAuth scopes required
        token_file (str): Path to the local token cache
        creds_file (str): Path to your OAuth client secrets file
    Returns:
        Authorized service object
    """
    try:
        creds = None

        # Load token if exists
        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file, scopes)

        # If no valid token, log in and save one
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                # Check if credentials file exists
                if not os.path.exists(creds_file):
                    raise FileNotFoundError(f"Credentials file '{creds_file}' not found. Please download from Google Cloud Console.")
                
                # Start OAuth flow
                flow = InstalledAppFlow.from_client_secrets_file(creds_file, scopes)
                creds = flow.run_local_server(port=0)

            # Save the credentials for future use
            with open(token_file, 'w') as token:
                token.write(creds.to_json())

        # Build and return the service
        return build(service_name, version, credentials=creds)
        
    except Exception as e:
        print(f"Authentication error: {e}")
        raise

def authenticate_gmail():
    """
    Gmail specific authentication call with Gmail scope
    """
    SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
    service = authenticate_google_api("gmail", "v1", SCOPES)
    return service

"""
---------- Database handler methods ----------
"""
def init_db():
    """
    Initialize the SQLite database and create the emails table if it doesn't exist.
    """
    conn = sqlite3.connect("emails.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS emails (
                    id TEXT PRIMARY KEY,
                    thread_id TEXT,
                    sender TEXT,
                    recipient TEXT,
                    subject TEXT,
                    snippet TEXT,
                    message_body TEXT,
                    received_at TEXT,
                    is_read INTEGER,
                    label_ids TEXT
                )''')
    conn.commit()
    conn.close()

def save_to_db(data):
    """
    Save email data to SQLite database
    """
    try:
        conn = sqlite3.connect("emails.db")
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO emails (id, thread_id, sender, recipient, subject, snippet, message_body, received_at, is_read, label_ids)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', data)
        conn.commit()
        conn.close()
        print(f"Saved to database: {data[4][:40]}...")  # data[4] is subject
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error saving to database: {e}")


"""
---------- Get & store emails core functionality ----------
"""
def fetch_emails(service, email_count):
    """
    Fetch and display list of recent Gmail messages
    """
    try:
        # Get list of messages from Gmail API
        results = service.users().messages().list(userId='me', maxResults=email_count).execute()
        messages = results.get('messages', [])

        print(f"\nTotal fetched: {len(messages)}")

        for msg in messages:
            try:
                # Get full message details
                full_msg = service.users().messages().get(userId='me', id=msg['id']).execute()

                payload = full_msg.get('payload', {})
                headers = payload.get('headers', [])

                # Extract email data from message
                email_id = full_msg['id']
                thread_id = full_msg['threadId']
                sender = parse_header(headers, 'From')
                recipient = parse_header(headers, 'To')
                subject = parse_header(headers, 'Subject')
                snippet = full_msg.get('snippet', '')
                message_body = extract_body(payload)
                received_at = parse_header(headers, 'Date')
                label_ids = ','.join(full_msg.get('labelIds', []))
                is_read = 'UNREAD' not in full_msg.get('labelIds', [])

                # Prepare data tuple for database
                data = (
                    email_id,
                    thread_id,
                    sender,
                    recipient,
                    subject,
                    snippet,
                    message_body,
                    received_at,
                    is_read,
                    label_ids
                )

                # Save to database
                save_to_db(data)
                
            except Exception as e:
                print(f"Error processing message {msg['id']}: {e}")
                continue
                
    except Exception as e:
        print(f"Error fetching messages: {e}")
        raise


"""
---------- Execution ----------
"""
if __name__ == '__main__':
    if len(sys.argv) > 1:
        emails_count = sys.argv[1]
    else:
        emails_count = 10    
    init_db()
    service = authenticate_gmail()
    fetch_emails(service, emails_count)
