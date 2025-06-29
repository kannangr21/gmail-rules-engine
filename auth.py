import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

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
    creds = None

    # Load token if exists
    if os.path.exists(token_file):
        try:
            creds = Credentials.from_authorized_user_file(token_file, scopes)
        except Exception as e:
            print(f"Error loading token: {e}")
            creds = None

    # If no valid token, log in and save one
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Error refreshing token: {e}")
                creds = None
        
        if not creds:
            # Check if credentials file exists
            if not os.path.exists(creds_file):
                raise FileNotFoundError(f"Credentials file '{creds_file}' not found. Please download from Google Cloud Console.")
            
            # Start OAuth flow
            flow = InstalledAppFlow.from_client_secrets_file(creds_file, scopes)
            creds = flow.run_local_server(port=0)

        # Save the credentials for future use
        try:
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
        except Exception as e:
            print(f"Error saving token: {e}")

    return build(service_name, version, credentials=creds)
