#!/usr/bin/env python3
"""
Jira API Key Validation Test Script

This script tests if your Jira API key is valid and has the necessary permissions
for reading and writing to Jira projects. It uses environment variables from .env file.

Usage:
    python test_jira_api_key.py

Requirements for API Token (Atlassian Cloud):
- Read access: View issues, projects, users
- Write access: Create/edit issues, add comments, manage attachments
"""

import os
import sys
from datetime import datetime
from typing import Dict, Any, List
import requests
import base64
from dotenv import load_dotenv

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_success(message: str):
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_error(message: str):
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def print_warning(message: str):
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")

def print_info(message: str):
    print(f"{Colors.BLUE}ℹ {message}{Colors.END}")

def print_header(message: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}")
    print(f"{message}")
    print(f"{'='*60}{Colors.END}")

class JiraApiTester:
    """Test Jira API key validity and permissions."""
    
    def __init__(self):
        """Initialize with environment variables."""
        # Load environment variables from .env file
        load_dotenv()
        
        self.jira_url = os.getenv("JIRA_URL")
        self.username = os.getenv("JIRA_USERNAME") 
        self.api_token = os.getenv("JIRA_API_TOKEN")
        self.projects_filter = os.getenv("JIRA_PROJECTS_FILTER")
        
        # Validate required environment variables
        if not self.jira_url:
            print_error("JIRA_URL not found in environment variables")
            sys.exit(1)
        if not self.username:
            print_error("JIRA_USERNAME not found in environment variables")
            sys.exit(1)
        if not self.api_token:
            print_error("JIRA_API_TOKEN not found in environment variables")
            sys.exit(1)
            
        # Setup authentication
        self.auth = base64.b64encode(f"{self.username}:{self.api_token}".encode()).decode()
        self.headers = {
            "Authorization": f"Basic {self.auth}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        # Remove trailing slashes and ensure proper API base URL
        self.api_base = self.jira_url.rstrip('/') + "/rest/api/3"
        
        print_info(f"Testing Jira instance: {self.jira_url}")
        print_info(f"Username: {self.username}")
        if self.projects_filter:
            print_info(f"Project filter: {self.projects_filter}")

    def make_request(self, endpoint: str, method: str = "GET", data: Dict[Any, Any] = None) -> requests.Response:
        """Make authenticated request to Jira API."""
        url = f"{self.api_base}{endpoint}"
        
        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers, timeout=30)
            elif method == "POST":
                response = requests.post(url, headers=self.headers, json=data, timeout=30)
            elif method == "PUT":
                response = requests.put(url, headers=self.headers, json=data, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            return response
        except requests.exceptions.RequestException as e:
            print_error(f"Request failed: {e}")
            return None

    def test_authentication(self) -> bool:
        """Test basic authentication."""
        print_header("Testing Authentication")
        
        response = self.make_request("/myself")
        
        if response is None:
            return False
            
        if response.status_code == 200:
            user_data = response.json()
            print_success("Authentication successful")
            print_info(f"Logged in as: {user_data.get('displayName', 'Unknown')} ({user_data.get('emailAddress', 'No email')})")
            print_info(f"Account ID: {user_data.get('accountId', 'Unknown')}")
            return True
        elif response.status_code == 401:
            print_error("Authentication failed - Invalid credentials")
            print_error("Check your JIRA_USERNAME and JIRA_API_TOKEN")
        elif response.status_code == 403:
            print_error("Authentication failed - Access forbidden")
            print_error("Your API token may not have sufficient permissions")
        else:
            print_error(f"Authentication failed - HTTP {response.status_code}: {response.text}")
            
        return False

    def test_projects_access(self) -> List[str]:
        """Test access to projects."""
        print_header("Testing Project Access")
        
        response = self.make_request("/project")
        
        if response is None or response.status_code != 200:
            print_error(f"Failed to retrieve projects - HTTP {response.status_code if response else 'N/A'}")
            return []
            
        projects = response.json()
        accessible_projects = []
        
        print_success(f"Found {len(projects)} accessible projects:")
        
        for project in projects:
            project_key = project.get('key', 'Unknown')
            project_name = project.get('name', 'Unknown')
            accessible_projects.append(project_key)
            
            # Check if project matches filter
            if self.projects_filter:
                filter_keys = [key.strip() for key in self.projects_filter.split(',')]
                if project_key in filter_keys:
                    print_info(f"  • {project_key}: {project_name} ✓ (matches filter)")
                else:
                    print_info(f"  • {project_key}: {project_name} (filtered out)")
            else:
                print_info(f"  • {project_key}: {project_name}")
                
        return accessible_projects

    def test_read_permissions(self, project_keys: List[str]) -> bool:
        """Test read permissions on issues."""
        print_header("Testing Read Permissions")
        
        # Test searching for issues
        search_jql = "ORDER BY created DESC"
        if self.projects_filter:
            filter_keys = [key.strip() for key in self.projects_filter.split(',')]
            search_jql = f"project in ({','.join(filter_keys)}) {search_jql}"
            
        response = self.make_request(f"/search?jql={search_jql}&maxResults=5")
        
        if response is None or response.status_code != 200:
            print_error(f"Failed to search issues - HTTP {response.status_code if response else 'N/A'}")
            return False
            
        search_results = response.json()
        issues = search_results.get('issues', [])
        
        if not issues:
            print_warning("No issues found - this might indicate limited read access or empty projects")
            return True
            
        print_success(f"Successfully retrieved {len(issues)} recent issues")
        
        # Test reading a specific issue
        first_issue = issues[0]
        issue_key = first_issue.get('key')
        
        response = self.make_request(f"/issue/{issue_key}")
        
        if response and response.status_code == 200:
            issue_data = response.json()
            print_success(f"Successfully read issue details for {issue_key}")
            print_info(f"  Summary: {issue_data.get('fields', {}).get('summary', 'No summary')}")
            print_info(f"  Status: {issue_data.get('fields', {}).get('status', {}).get('name', 'Unknown')}")
            return True
        else:
            print_error(f"Failed to read issue {issue_key} - HTTP {response.status_code if response else 'N/A'}")
            return False

    def test_write_permissions(self, project_keys: List[str]) -> bool:
        """Test write permissions (safely)."""
        print_header("Testing Write Permissions")
        
        # Check read-only mode
        read_only_mode = os.getenv("READ_ONLY_MODE", "false").lower() in ("true", "1", "yes")
        if read_only_mode:
            print_warning("READ_ONLY_MODE is enabled - skipping write permission tests")
            return True
            
        if not project_keys:
            print_warning("No accessible projects found - cannot test write permissions")
            return False
            
        # Use the first accessible project or filtered project
        test_project = None
        if self.projects_filter:
            filter_keys = [key.strip() for key in self.projects_filter.split(',')]
            for key in filter_keys:
                if key in project_keys:
                    test_project = key
                    break
        else:
            test_project = project_keys[0]
            
        if not test_project:
            print_warning("No suitable project found for write testing")
            return False
            
        print_info(f"Testing write permissions on project: {test_project}")
        
        # Get project metadata to understand available issue types
        response = self.make_request(f"/project/{test_project}")
        if response is None or response.status_code != 200:
            print_error(f"Failed to get project metadata for {test_project}")
            return False
            
        project_data = response.json()
        issue_types = project_data.get('issueTypes', [])
        
        if not issue_types:
            print_error("No issue types found in project")
            return False
            
        # Find a basic issue type (preferably Task or Story)
        preferred_types = ['Task', 'Story', 'Bug']
        selected_issue_type = None
        
        for issue_type in issue_types:
            if issue_type.get('name') in preferred_types:
                selected_issue_type = issue_type
                break
                
        if not selected_issue_type:
            selected_issue_type = issue_types[0]  # Use first available
            
        print_info(f"Using issue type: {selected_issue_type.get('name')}")
        
        # Test creating an issue (dry run - we'll check metadata only)
        create_meta_response = self.make_request(f"/issue/createmeta?projectKeys={test_project}")
        
        if create_meta_response and create_meta_response.status_code == 200:
            print_success("✓ Create issue metadata accessible - likely has create permissions")
        else:
            print_error("✗ Cannot access create issue metadata - may lack create permissions")
            return False
            
        # Test getting editable fields (indicates edit permissions)
        # We'll use a recent issue if available
        search_response = self.make_request(f"/search?jql=project={test_project}&maxResults=1")
        
        if search_response and search_response.status_code == 200:
            search_data = search_response.json()
            issues = search_data.get('issues', [])
            
            if issues:
                issue_key = issues[0].get('key')
                edit_meta_response = self.make_request(f"/issue/{issue_key}/editmeta")
                
                if edit_meta_response and edit_meta_response.status_code == 200:
                    print_success(f"✓ Edit metadata accessible for {issue_key} - likely has edit permissions")
                else:
                    print_warning(f"✗ Cannot access edit metadata for {issue_key} - may lack edit permissions")
            else:
                print_info("No existing issues found to test edit permissions")
        
        return True

    def test_additional_permissions(self) -> None:
        """Test additional API capabilities."""
        print_header("Testing Additional Permissions")
        
        # Test user search
        response = self.make_request("/user/search?query=a&maxResults=1")
        if response and response.status_code == 200:
            print_success("✓ User search - can search for users")
        else:
            print_warning("✗ User search - limited or no user search permissions")
            
        # Test getting priorities
        response = self.make_request("/priority")
        if response and response.status_code == 200:
            print_success("✓ Priorities - can read issue priorities")
        else:
            print_warning("✗ Priorities - cannot read priorities")
            
        # Test getting issue types
        response = self.make_request("/issuetype")
        if response and response.status_code == 200:
            print_success("✓ Issue types - can read issue types")
        else:
            print_warning("✗ Issue types - cannot read issue types")
            
        # Test getting statuses
        response = self.make_request("/status")
        if response and response.status_code == 200:
            print_success("✓ Statuses - can read issue statuses")
        else:
            print_warning("✗ Statuses - cannot read statuses")

    def run_all_tests(self) -> bool:
        """Run all API tests."""
        print_header(f"Jira API Key Validation Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        success = True
        
        # Test 1: Authentication
        if not self.test_authentication():
            return False
            
        # Test 2: Project access
        project_keys = self.test_projects_access()
        
        # Test 3: Read permissions
        if not self.test_read_permissions(project_keys):
            success = False
            
        # Test 4: Write permissions
        if not self.test_write_permissions(project_keys):
            success = False
            
        # Test 5: Additional permissions
        self.test_additional_permissions()
        
        # Summary
        print_header("Test Summary")
        
        if success:
            print_success("All critical tests passed!")
            print_info("Your API token appears to have sufficient permissions for:")
            print_info("  • Reading issues, projects, and metadata")
            print_info("  • Creating and editing issues (metadata check)")
            print_info("  • Searching and filtering")
        else:
            print_warning("Some tests failed - your API token may have limited permissions")
            
        print_info("\nNote: API tokens inherit permissions from the user account")
        print_info("If you need additional permissions, contact your Jira administrator")
        
        return success

def main():
    """Main function."""
    try:
        tester = JiraApiTester()
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_warning("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
