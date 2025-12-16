"""
MCP Authentication Handler
Manages OAuth flows and API key authentication for all MCP servers
"""

import os
import json
import hashlib
import base64
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
import requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle

class MCPAuthHandler:
    """Centralized authentication handler for all MCP integrations"""

    def __init__(self, config_path: str = "mcp-config.json"):
        self.config_path = Path(config_path)
        self.token_cache_path = Path("cache/tokens.pkl")
        self.config = self._load_config()
        self._ensure_cache_dir()

    def _load_config(self) -> Dict[str, Any]:
        """Load MCP configuration"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config not found: {self.config_path}")
        with open(self.config_path, 'r') as f:
            return json.load(f)

    def _ensure_cache_dir(self):
        """Ensure cache directory exists"""
        self.token_cache_path.parent.mkdir(parents=True, exist_ok=True)

    def _load_cached_tokens(self) -> Dict[str, Any]:
        """Load cached OAuth tokens"""
        if self.token_cache_path.exists():
            with open(self.token_cache_path, 'rb') as f:
                return pickle.load(f)
        return {}

    def _save_cached_tokens(self, tokens: Dict[str, Any]):
        """Save OAuth tokens to cache"""
        with open(self.token_cache_path, 'wb') as f:
            pickle.dump(tokens, f)

    def get_westlaw_credentials(self) -> Dict[str, str]:
        """Get Westlaw API credentials"""
        api_key = os.getenv('WESTLAW_API_KEY')
        if not api_key:
            raise ValueError("WESTLAW_API_KEY not set in environment")
        return {
            'api_key': api_key,
            'base_url': 'https://api.westlaw.com/v1'
        }

    def get_lexisnexis_credentials(self) -> Dict[str, str]:
        """Get LexisNexis Protégé API credentials"""
        api_key = os.getenv('LEXISNEXIS_API_KEY')
        api_secret = os.getenv('LEXISNEXIS_API_SECRET')
        if not api_key or not api_secret:
            raise ValueError("LexisNexis credentials not set in environment")
        return {
            'api_key': api_key,
            'api_secret': api_secret,
            'base_url': 'https://api.lexisnexis.com/protégé/v1'
        }

    def get_gmail_credentials(self) -> Credentials:
        """Get Gmail OAuth credentials with proper scopes"""
        SCOPES = [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/gmail.metadata'
        ]

        creds = None
        cache = self._load_cached_tokens()

        # Check for cached credentials
        if 'gmail' in cache:
            creds = cache['gmail']

        # Refresh or create new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                credentials_path = os.getenv('GMAIL_CREDENTIALS_PATH', 'credentials.json')
                if not os.path.exists(credentials_path):
                    raise FileNotFoundError(f"Gmail credentials not found: {credentials_path}")

                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)

            # Save credentials
            cache['gmail'] = creds
            self._save_cached_tokens(cache)

        return creds

    def get_slack_credentials(self) -> Dict[str, str]:
        """Get Slack OAuth credentials"""
        oauth_token = os.getenv('SLACK_OAUTH_TOKEN')
        if not oauth_token:
            raise ValueError("SLACK_OAUTH_TOKEN not set in environment")
        return {
            'oauth_token': oauth_token,
            'base_url': 'https://slack.com/api'
        }

    def get_supabase_credentials(self) -> Dict[str, str]:
        """Get Supabase credentials"""
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_SERVICE_KEY')
        if not url or not key:
            raise ValueError("Supabase credentials not set in environment")
        return {
            'url': url,
            'service_key': key
        }

    def get_github_credentials(self) -> Dict[str, str]:
        """Get GitHub personal access token"""
        token = os.getenv('GITHUB_TOKEN')
        if not token:
            raise ValueError("GITHUB_TOKEN not set in environment")
        return {
            'token': token,
            'base_url': 'https://api.github.com'
        }

    def validate_api_key(self, service: str, api_key: str) -> bool:
        """Validate API key format"""
        min_lengths = {
            'westlaw': 32,
            'lexisnexis': 32,
            'slack': 40,
            'github': 40
        }
        return len(api_key) >= min_lengths.get(service, 20)

    def hash_credentials(self, credentials: str) -> str:
        """Hash credentials for secure logging"""
        return hashlib.sha256(credentials.encode()).hexdigest()[:16]

    def refresh_token_if_needed(self, service: str) -> Optional[Dict[str, Any]]:
        """Refresh OAuth token if expired"""
        cache = self._load_cached_tokens()

        if service not in cache:
            return None

        token_data = cache[service]

        # Check if token needs refresh
        if isinstance(token_data, Credentials):
            if token_data.expired and token_data.refresh_token:
                token_data.refresh(Request())
                cache[service] = token_data
                self._save_cached_tokens(cache)
                return {'status': 'refreshed', 'credentials': token_data}

        return {'status': 'valid', 'credentials': token_data}


# Singleton instance
_auth_handler = None

def get_auth_handler() -> MCPAuthHandler:
    """Get singleton auth handler instance"""
    global _auth_handler
    if _auth_handler is None:
        _auth_handler = MCPAuthHandler()
    return _auth_handler
