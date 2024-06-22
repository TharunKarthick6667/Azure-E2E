import msal
import requests

# Azure AD Config
CLIENT_ID = "fc6356e5-1a6c-424c-99c1-4222b2561105"
CLIENT_SECRET = "0vk8Q~u6MhwKoZrqCZos3Lly9-ToL.fT2rfElbrP"
TENANT_ID = "8a9e0ff9-3d79-4e15-aeef-e7b050814935"
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
REDIRECT_URI = "http://localhost:8501"
SCOPE = ["User.Read", "GroupMember.Read.All"]

# MSAL configuration
msal_app = msal.ConfidentialClientApplication(
    CLIENT_ID,
    authority=AUTHORITY,
    client_credential=CLIENT_SECRET,
)

def get_auth_url():
    auth_url = msal_app.get_authorization_request_url(SCOPE, redirect_uri=REDIRECT_URI)
    return auth_url

def get_token_from_code(auth_code):
    result = msal_app.acquire_token_by_authorization_code(auth_code, scopes=SCOPE, redirect_uri=REDIRECT_URI)
    return result

def get_user_groups(access_token):
    headers = {'Authorization': f'Bearer {access_token}'}
    graph_url = 'https://graph.microsoft.com/v1.0/me/memberOf'
    response = requests.get(graph_url, headers=headers)
    response.raise_for_status()
    return response.json()
