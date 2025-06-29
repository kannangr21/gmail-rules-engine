import os.path
import base64
import json
import sqlite3

from utils import parse_header, extract_body
from auth import authenticate_google_api
from database.db import save_to_db


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

def authenticate_gmail():
    """
    Authenticate and get Gmail service
    """
    SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
    service = authenticate_google_api("gmail", "v1", SCOPES)
    return service

def fetch_and_store_emails():
    service = authenticate_gmail()
    # List recent messages
    list_messages(service)
