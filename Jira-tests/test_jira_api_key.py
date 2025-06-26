#!/usr/bin/env python3
"""
Test script to validate Jira API key and permissions.
This script verifies that your Jira API credentials work correctly
and checks access to projects, including the AI project filter.
"""

import os
import requests
from typing import List, Dict, Any
from pathlib import Path

def print_header(title: str):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def print_info(message: str):
    """Print info message."""
    print(f"ℹ️  {message}")

def print_success(message: str):
    """Print success message."""
    print(f"✅ {message}")

def print_error(message: str):
    """Print error message."""
    print(f"❌ {message}")

def print_warning(message: str):
    """Print warning message."""
    print(f"⚠️  {message}")

class JiraApiTester:
    """Test Jira API key validity and permissions."""
    
    def __init__(self):
        """Initialize the tester with environment variables."""
        # Load environment variables from .env file if it exists
        env_path = Path(".env")
        if env_path.exists():
            print_info(f"Loading environment variables from {env_path}")
            # Simple env file parser
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value
        
        self.base_url = os.getenv("JIRA_URL")
        self.username = os.getenv("JIRA_USERNAME")
        self.api_token = os.getenv("JIRA_API_TOKEN")
        self.projects_filter = os.getenv("JIRA_PROJECTS_FILTER")
        
        if not all([self.base_url, self.username, self.api_token]):
            raise ValueError("Missing required environment variables: JIRA_URL, JIRA_USERNAME, JIRA_API_TOKEN")
        
        # Remove trailing slash from base URL
        self.base_url = self.base_url.rstrip('/')
        
        print_info(f"Jira URL: {self.base_url}")
        print_info(f"Username: {self.username}")
        print_info(f"API Token: {'*' * len(self.api_token)}")
        print_info(f"Projects Filter: {self.projects_filter}")
    
    def make_request(self, endpoint: str) -> requests.Response:
        """Make an authenticated request to Jira API."""
        url = f"{self.base_url}/rest/api/2{endpoint}"
        
        try:
            response = requests.get(
                url,
                auth=(self.username, self.api_token),
                headers={
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                timeout=30
            )
            return response
        except requests.exceptions.RequestException as e:
            print_error(f"Request failed: {e}")
            return None
    
    def test_authentication(self) -> bool:
        """Test basic authentication."""
        print_header("Testing Authentication")
        
        response = self.make_request("/myself")
        
        if response is None:
            print_error("Failed to make request - network or connection issue")
            return False
        
        if response.status_code == 200:
            user_info = response.json()
            print_success("Authentication successful!")
            print_info(f"Logged in as: {user_info.get('displayName', 'Unknown')} ({user_info.get('emailAddress', 'No email')})")
            print_info(f"Account ID: {user_info.get('accountId', 'Unknown')}")
            return True
        elif response.status_code in [401, 403]:
            print_error(f"Authentication failed - HTTP {response.status_code}")
            print_error("Please check your username and API token")
            return False
        else:
            print_error(f"Unexpected response - HTTP {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    
    def test_permissions(self) -> Dict[str, Any]:
        """Test API permissions."""
        print_header("Testing API Permissions")
        
        permissions = {
            "browse_projects": False,
            "create_issues": False,
            "edit_issues": False,
            "view_issues": False
        }
        
        # Test project browsing
        response = self.make_request("/project")
        if response and response.status_code == 200:
            permissions["browse_projects"] = True
            print_success("✓ Can browse projects")
        else:
            print_error("✗ Cannot browse projects")
        
        # Test issue viewing (try to get recent issues)
        response = self.make_request("/search?jql=created >= -7d&maxResults=1")
        if response and response.status_code == 200:
            permissions["view_issues"] = True
            print_success("✓ Can view issues")
        else:
            print_error("✗ Cannot view issues")
        
        # Test issue creation permissions by checking create meta
        response = self.make_request("/issue/createmeta")
        if response and response.status_code == 200:
            permissions["create_issues"] = True
            print_success("✓ Can create issues")
        else:
            print_error("✗ Cannot create issues")
        
        return permissions
    
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
        
        # Show summary of project filter issue
        if self.projects_filter:
            filter_keys = [key.strip() for key in self.projects_filter.split(',')]
            matching_projects = [p for p in projects if p.get('key') in filter_keys]
            print_info(f"\nProject filter '{self.projects_filter}' matches {len(matching_projects)} out of {len(projects)} projects")
            if len(matching_projects) == 0:
                print_warning("⚠ No projects match the current filter! This is why the MCP server returns an empty list.")
                print_warning(f"Available project keys: {', '.join([p.get('key', 'Unknown') for p in projects])}")
                print_warning("Consider updating JIRA_PROJECTS_FILTER in your .env file or removing it entirely.")
        
        return accessible_projects
    
    def test_ai_project_specific(self) -> bool:
        """Test specific access to AI project."""
        print_header("Testing AI Project Specific Access")
        
        # Test AI project details
        response = self.make_request("/project/AI")
        if response and response.status_code == 200:
            project_info = response.json()
            print_success("AI project is accessible!")
            print_info(f"Project Key: {project_info.get('key', 'Unknown')}")
            print_info(f"Project Name: {project_info.get('name', 'Unknown')}")
            print_info(f"Project Type: {project_info.get('projectTypeKey', 'Unknown')}")
            print_info(f"Project Lead: {project_info.get('lead', {}).get('displayName', 'Unknown')}")
        else:
            print_error(f"AI project is not accessible - HTTP {response.status_code if response else 'N/A'}")
            return False
        
        # Test AI project issues
        response = self.make_request("/search?jql=project=AI&maxResults=5")
        if response and response.status_code == 200:
            search_result = response.json()
            total_issues = search_result.get('total', 0)
            issues = search_result.get('issues', [])
            
            print_success(f"Found {total_issues} issues in AI project")
            print_info("Sample issues:")
            for issue in issues[:5]:
                print_info(f"  • {issue.get('key', 'Unknown')}: {issue.get('fields', {}).get('summary', 'No summary')}")
        else:
            print_error(f"Cannot access AI project issues - HTTP {response.status_code if response else 'N/A'}")
            return False
        
        return True
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return results."""
        print_header("Jira API Key Validation Test Suite")
        
        results = {
            "authentication": False,
            "permissions": {},
            "projects": [],
            "ai_project": False,
            "overall_success": False
        }
        
        try:
            # Test authentication
            results["authentication"] = self.test_authentication()
            if not results["authentication"]:
                print_error("Authentication failed - stopping tests")
                return results
            
            # Test permissions
            results["permissions"] = self.test_permissions()
            
            # Test project access
            results["projects"] = self.test_projects_access()
            
            # Test AI project specifically
            results["ai_project"] = self.test_ai_project_specific()
            
            # Overall success
            results["overall_success"] = (
                results["authentication"] and
                results["permissions"].get("browse_projects", False) and
                results["permissions"].get("view_issues", False) and
                len(results["projects"]) > 0 and
                results["ai_project"]
            )
            
            # Final summary
            print_header("Test Results Summary")
            if results["overall_success"]:
                print_success("🎉 All tests passed! Your Jira API key is working correctly.")
            else:
                print_warning("⚠️  Some tests failed. Check the details above.")
            
            return results
            
        except Exception as e:
            print_error(f"Unexpected error during testing: {e}")
            return results

def main():
    """Main function."""
    try:
        tester = JiraApiTester()
        results = tester.run_all_tests()
        
        if results["overall_success"]:
            exit(0)
        else:
            exit(1)
            
    except ValueError as e:
        print_error(f"Configuration error: {e}")
        exit(1)
    except KeyboardInterrupt:
        print_warning("\n⚠️ Test interrupted by user")
        exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
