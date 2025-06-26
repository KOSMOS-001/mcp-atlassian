#!/usr/bin/env python3
"""
Environment configuration test script.
This script validates that all environment variables are properly loaded
and configured for the MCP server.
"""

import os
from pathlib import Path

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

def load_env_file(env_path: Path) -> dict:
    """Load environment variables from .env file."""
    env_vars = {}
    if env_path.exists():
        print_info(f"Loading environment variables from {env_path}")
        with open(env_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    try:
                        key, value = line.split('=', 1)
                        env_vars[key] = value
                        os.environ[key] = value
                    except ValueError:
                        print_warning(f"Line {line_num}: Could not parse line: {line}")
    else:
        print_error(f"Environment file not found: {env_path}")
    
    return env_vars

def test_env_configuration():
    """Test environment configuration."""
    print_section("Environment Configuration Test")
    
    # Load .env file
    env_path = Path(".env")
    env_vars = load_env_file(env_path)
    
    # Define required variables
    required_vars = {
        "JIRA_URL": "Jira instance URL",
        "JIRA_USERNAME": "Jira username/email",
        "JIRA_API_TOKEN": "Jira API token"
    }
    
    # Define optional but important variables
    optional_vars = {
        "JIRA_PROJECTS_FILTER": "Project filter (should be 'AI')",
        "READ_ONLY_MODE": "Read-only mode setting",
        "MCP_VERBOSE": "Verbose logging",
        "TRANSPORT": "MCP transport mode"
    }
    
    print_section("Required Environment Variables")
    
    missing_required = []
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            if "TOKEN" in var or "PASSWORD" in var:
                masked_value = "*" * len(value)
            else:
                masked_value = value
            print_success(f"{var}: {masked_value}")
            print_info(f"  Description: {description}")
        else:
            print_error(f"{var}: NOT SET")
            print_info(f"  Description: {description}")
            missing_required.append(var)
    
    print_section("Optional Environment Variables")
    
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value:
            print_success(f"{var}: {value}")
            print_info(f"  Description: {description}")
        else:
            print_warning(f"{var}: Not set")
            print_info(f"  Description: {description}")
    
    # Specific checks
    print_section("Configuration Validation")
    
    # Check JIRA_PROJECTS_FILTER
    projects_filter = os.getenv("JIRA_PROJECTS_FILTER")
    if projects_filter == "AI":
        print_success("JIRA_PROJECTS_FILTER is correctly set to 'AI'")
    elif projects_filter:
        print_warning(f"JIRA_PROJECTS_FILTER is set to '{projects_filter}' (expected 'AI')")
    else:
        print_warning("JIRA_PROJECTS_FILTER is not set (will return all projects)")
    
    # Check READ_ONLY_MODE
    read_only = os.getenv("READ_ONLY_MODE")
    if read_only == "true":
        print_success("READ_ONLY_MODE is enabled (recommended for testing)")
    else:
        print_info("READ_ONLY_MODE is not set or disabled")
    
    # Check Jira URL format
    jira_url = os.getenv("JIRA_URL")
    if jira_url:
        if jira_url.startswith("https://") and jira_url.endswith(".atlassian.net"):
            print_success("JIRA_URL appears to be a valid Atlassian Cloud URL")
        elif jira_url.startswith("https://"):
            print_info("JIRA_URL appears to be a custom/server URL")
        else:
            print_warning("JIRA_URL should start with https://")
    
    # Summary
    print_section("Summary")
    
    if missing_required:
        print_error(f"Missing required variables: {', '.join(missing_required)}")
        print_error("Please set these variables in your .env file")
        return False
    else:
        print_success("All required environment variables are set!")
        
        if projects_filter == "AI":
            print_success("Configuration is ready for AI project access")
        else:
            print_warning("Consider setting JIRA_PROJECTS_FILTER=AI for AI project access")
        
        return True

def main():
    """Main function."""
    try:
        success = test_env_configuration()
        if success:
            print_success("\n🎉 Environment configuration test passed!")
            return 0
        else:
            print_error("\n💥 Environment configuration test failed!")
            return 1
    except Exception as e:
        print_error(f"\n💥 Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
