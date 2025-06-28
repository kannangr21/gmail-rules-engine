import os.path
import base64
import json
import sqlite3
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from utils import parse_header, extract_body

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

# If modifying scopes, delete token.json
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def authenticate_gmail():
    """
    Authenticate with Gmail API using OAuth 2.0
    Returns authenticated Gmail service object
    """
    try:
        creds = None

        # Load token if exists in cache
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)

        # If no valid token, log in and save one
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                # Refresh the token if it's expired
                creds.refresh(Request())
            else:
                # Start OAuth flow
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for future use in cache
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        # Return authorized Gmail API client
        service = build('gmail', 'v1', credentials=creds)
        return service
    except FileNotFoundError:
        print("credentials.json not found. Please download from Google Cloud Console")
        raise
    except Exception as e:
        print(f"Authentication error: {e}")
        raise

def list_messages(service):
    """
    Fetch and display list of recent Gmail messages
    """
    try:
        # Get list of messages from Gmail API
        results = service.users().messages().list(userId='me', maxResults=10).execute()
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


if __name__ == '__main__':
    try:
        # Authenticate and get Gmail service
        service = authenticate_gmail()
        # List recent messages
        list_messages(service)
    except Exception as e:
        print(f"Script failed: {e}")
        exit(1)
