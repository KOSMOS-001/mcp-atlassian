#!/usr/bin/env python3
"""
Test script to verify MCP server configuration and AI project access.
This script tests the full MCP server configuration including Jira client
initialization and project filtering functionality.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# Add the source directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp_atlassian.jira import JiraFetcher
from mcp_atlassian.jira.config import JiraConfig

# Enable logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

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

def print_warning(message: str):
    """Print warning message."""
    print(f"⚠️  {message}")

async def test_mcp_server_config():
    """Test MCP server configuration and project access."""
    
    print_section("MCP Server Configuration Test")
    
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
        
        # Test Jira configuration
        print_section("Testing Jira Configuration")
        
        try:
            config = JiraConfig.from_env()
            print_success("Jira configuration loaded successfully")
            print_info(f"URL: {config.url}")
            print_info(f"Auth Type: {config.auth_type}")
            print_info(f"Username: {config.username}")
            print_info(f"Projects Filter: {config.projects_filter}")
            print_info(f"SSL Verify: {config.ssl_verify}")
            
            if not config.is_auth_configured():
                print_error("Authentication is not properly configured")
                return False
                
        except Exception as e:
            print_error(f"Failed to load Jira configuration: {e}")
            return False
        
        # Test Jira client initialization
        print_section("Testing Jira Client Initialization")
        
        try:
            jira_fetcher = JiraFetcher(config)
            print_success("Jira client initialized successfully")
        except Exception as e:
            print_error(f"Failed to initialize Jira client: {e}")
            return False
        
        # Test all projects access
        print_section("Testing All Projects Access")
        
        try:
            all_projects = jira_fetcher.get_all_projects()
            print_success(f"Retrieved {len(all_projects)} total projects")
            
            for project in all_projects:
                key = project.get('key', 'Unknown')
                name = project.get('name', 'Unknown')
                print_info(f"  • {key}: {name}")
                
        except Exception as e:
            print_error(f"Failed to get all projects: {e}")
            return False
        
        # Test AI project specific access
        print_section("Testing AI Project Specific Access")
        
        try:
            # Test if AI project exists
            ai_project = jira_fetcher.get_project("AI")
            if ai_project:
                print_success("AI project found and accessible")
                print_info(f"  Project Key: {ai_project.get('key')}")
                print_info(f"  Project Name: {ai_project.get('name')}")
                print_info(f"  Project ID: {ai_project.get('id')}")
            else:
                print_error("AI project not found or not accessible")
                return False
                
        except Exception as e:
            print_error(f"Failed to access AI project: {e}")
            return False
        
        # Test AI project issues
        print_section("Testing AI Project Issues Access")
        
        try:
            search_result = jira_fetcher.get_project_issues("AI", limit=5)
            print_success(f"Retrieved {search_result.total} total issues from AI project")
            print_info(f"Showing first {len(search_result.issues)} issues:")
            
            for issue in search_result.issues:
                print_info(f"  • {issue.key}: {issue.summary}")
                
        except Exception as e:
            print_error(f"Failed to get AI project issues: {e}")
            return False
        
        # Test search with projects filter
        print_section("Testing Search with Projects Filter")
        
        try:
            # Test general search that should be filtered to AI project
            search_result = jira_fetcher.search_issues("", limit=5)
            print_success(f"Search returned {search_result.total} total issues")
            print_info(f"Issues from search (should be AI project only):")
            
            for issue in search_result.issues:
                project_key = issue.key.split('-')[0] if '-' in issue.key else 'Unknown'
                print_info(f"  • {issue.key}: {issue.summary} (Project: {project_key})")
                
        except Exception as e:
            print_error(f"Failed to search issues: {e}")
            return False
        
        print_section("Test Results Summary")
        print_success("All tests passed! MCP server should be able to access AI project.")
        return True
        
    except Exception as e:
        print_error(f"Unexpected error during testing: {e}")
        return False

async def main():
    """Main test function."""
    try:
        success = await test_mcp_server_config()
        if success:
            print_success("\n🎉 MCP server configuration test completed successfully!")
            sys.exit(0)
        else:
            print_error("\n💥 MCP server configuration test failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print_warning("\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"\n💥 Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
