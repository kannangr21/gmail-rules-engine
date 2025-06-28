import os.path
import base64
import json

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# If modifying scopes, delete token.json
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def authenticate_gmail():
    """
    Authenticate with Gmail API using OAuth 2.0
    Returns authenticated Gmail service object
    """
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

def list_messages(service):
    """
    Fetch and display list of recent Gmail messages
    """
    # Get list of messages from Gmail API
    results = service.users().messages().list(userId='me', maxResults=10).execute()
    messages = results.get('messages', [])
    
    print(f"\nTotal fetched: {len(messages)}")
    # Display each message ID
    for msg in messages:
        print(f"- Message ID: {msg['id']}")

if __name__ == '__main__':
    # Authenticate and get Gmail service
    service = authenticate_gmail()
    # List recent messages
    list_messages(service)
