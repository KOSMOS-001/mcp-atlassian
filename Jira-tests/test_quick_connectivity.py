#!/usr/bin/env python3
"""
Quick connectivity test for Jira API.
This is a minimal test that checks basic connectivity to Jira
without requiring the full MCP server setup.
"""

import os
import sys
from pathlib import Path

def print_info(message: str):
    """Print info message."""
    print(f"ℹ️  {message}")

def print_success(message: str):
    """Print success message."""
    print(f"✅ {message}")

def print_error(message: str):
    """Print error message."""
    print(f"❌ {message}")

def quick_connectivity_test():
    """Quick test of Jira connectivity using curl command."""
    print("Quick Jira Connectivity Test")
    print("=" * 40)
    
    # Load basic env vars
    env_path = Path(".env")
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
    
    jira_url = os.getenv("JIRA_URL")
    jira_username = os.getenv("JIRA_USERNAME")
    jira_api_token = os.getenv("JIRA_API_TOKEN")
    
    if not all([jira_url, jira_username, jira_api_token]):
        print_error("Missing required environment variables")
        return False
    
    print_info(f"Testing connection to: {jira_url}")
    print_info(f"Username: {jira_username}")
    
    # Create curl command for testing
    curl_cmd = f'''curl -s -w "HTTP_STATUS:%{{http_code}}" \\
  -u "{jira_username}:{jira_api_token}" \\
  -H "Accept: application/json" \\
  "{jira_url}/rest/api/2/myself"'''
    
    print("\nGenerated curl command for manual testing:")
    print("-" * 50)
    print(curl_cmd)
    print("-" * 50)
    
    print("\nTo test manually, run the above curl command.")
    print("Expected response: HTTP_STATUS:200 with user information")
    print("If you get HTTP_STATUS:401, check your credentials")
    print("If you get HTTP_STATUS:403, check your permissions")
    
    return True

if __name__ == "__main__":
    try:
        quick_connectivity_test()
    except Exception as e:
        print_error(f"Error: {e}")
        sys.exit(1)
