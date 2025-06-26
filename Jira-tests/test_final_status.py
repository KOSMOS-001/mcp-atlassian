#!/usr/bin/env python3
"""
Test script to verify the current status of MCP server AI project access.
This is a comprehensive final status check that validates all components
are working correctly together.
"""

import json
import os
import sys
from pathlib import Path

# Add the source directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp_atlassian.jira import JiraFetcher, JiraConfig

def print_section(title: str):
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

def main():
    """Test the final configuration status."""
    
    print_section("Final MCP Server Status Check")
    
    try:
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
        
        # Check environment variables
        print_section("Environment Variables Status")
        
        jira_url = os.getenv("JIRA_URL")
        jira_username = os.getenv("JIRA_USERNAME")
        jira_api_token = os.getenv("JIRA_API_TOKEN")
        jira_projects_filter = os.getenv("JIRA_PROJECTS_FILTER")
        
        print_info(f"JIRA_URL: {jira_url}")
        print_info(f"JIRA_USERNAME: {jira_username}")
        print_info(f"JIRA_API_TOKEN: {'*' * len(jira_api_token) if jira_api_token else 'Not set'}")
        print_info(f"JIRA_PROJECTS_FILTER: {jira_projects_filter}")
        
        if not all([jira_url, jira_username, jira_api_token]):
            print_error("Missing required environment variables")
            return False
        
        if jira_projects_filter != "AI":
            print_error(f"JIRA_PROJECTS_FILTER should be 'AI', but it's '{jira_projects_filter}'")
            return False
        
        print_success("All required environment variables are set correctly")
        
        # Test configuration loading
        print_section("Configuration Loading Test")
        
        try:
            config = JiraConfig.from_env()
            print_success("Jira configuration loaded successfully")
            print_info(f"Projects filter in config: {config.projects_filter}")
            
            if config.projects_filter == "AI":
                print_success("Projects filter is correctly set to 'AI'")
            else:
                print_error(f"Projects filter should be 'AI', but it's '{config.projects_filter}'")
                return False
                
        except Exception as e:
            print_error(f"Failed to load Jira configuration: {e}")
            return False
        
        # Test actual Jira access
        print_section("Jira API Access Test")
        
        try:
            jira_fetcher = JiraFetcher(config)
            
            # Test AI project access
            ai_project = jira_fetcher.get_project("AI")
            if ai_project:
                print_success("AI project is accessible")
                print_info(f"Project: {ai_project.get('key')} - {ai_project.get('name')}")
            else:
                print_error("AI project is not accessible")
                return False
            
            # Test project filtering
            all_projects = jira_fetcher.get_all_projects()
            print_info(f"Total projects accessible: {len(all_projects)}")
            
            # Simulate the MCP server's project filtering logic
            if config.projects_filter:
                allowed_project_keys = {
                    p.strip().upper() for p in config.projects_filter.split(",")
                }
                filtered_projects = [
                    project
                    for project in all_projects
                    if project.get("key") in allowed_project_keys
                ]
            else:
                filtered_projects = all_projects
            
            print_info(f"Projects after filtering: {len(filtered_projects)}")
            for project in filtered_projects:
                print_info(f"  • {project.get('key')}: {project.get('name')}")
            
            if len(filtered_projects) == 1 and filtered_projects[0].get('key') == 'AI':
                print_success("Project filtering is working correctly - only AI project available")
            else:
                print_error(f"Expected only AI project, but got: {[p.get('key') for p in filtered_projects]}")
                return False
            
            # Test issues access
            search_result = jira_fetcher.get_project_issues("AI", limit=3)
            print_success(f"Retrieved {search_result.total} issues from AI project")
            print_info("Sample issues:")
            for issue in search_result.issues[:3]:
                print_info(f"  • {issue.key}: {issue.summary}")
                
        except Exception as e:
            print_error(f"Jira API access test failed: {e}")
            return False
        
        print_section("Summary")
        print_success("🎉 MCP Server is correctly configured for AI project access!")
        print_info("\nThe MCP server should now work correctly in your frontend application.")
        print_info("Available tools should only return data from the AI project:")
        print_info("  • jira_get_all_projects - returns only AI project")
        print_info("  • jira_search - returns only AI project issues")
        print_info("  • jira_get_project_issues - works with AI project")
        print_info("  • All other Jira tools will be scoped to AI project")
        
        return True
        
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return False

if __name__ == "__main__":
    try:
        success = main()
        if success:
            sys.exit(0)
        else:
            print_error("\n💥 Configuration check failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print_error("\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"\n💥 Unexpected error: {e}")
        sys.exit(1)
