#!/usr/bin/env python3
"""
Test runner script for all Jira tests.
This script runs all available tests in the recommended order
and provides a comprehensive report.
"""

import subprocess
import sys
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

def run_test(test_name: str, script_path: str, use_uv: bool = False) -> bool:
    """Run a single test script."""
    print_section(f"Running {test_name}")
    
    try:
        # Change to parent directory to run tests
        original_dir = os.getcwd()
        parent_dir = Path(__file__).parent.parent
        os.chdir(parent_dir)
        
        if use_uv:
            cmd = ["uv", "run", "python3", script_path]
        else:
            cmd = ["python3", script_path]
        
        print_info(f"Command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60  # 60 second timeout
        )
        
        # Always show the output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        success = result.returncode == 0
        
        if success:
            print_success(f"{test_name} completed successfully")
        else:
            print_error(f"{test_name} failed (exit code: {result.returncode})")
        
        return success
        
    except subprocess.TimeoutExpired:
        print_error(f"{test_name} timed out")
        return False
    except Exception as e:
        print_error(f"Error running {test_name}: {e}")
        return False
    finally:
        # Restore original directory
        os.chdir(original_dir)

def main():
    """Run all tests in recommended order."""
    print_section("Jira MCP Server Test Suite")
    print_info("Running comprehensive tests for Jira MCP server configuration")
    
    # Define tests in recommended order
    tests = [
        ("Environment Configuration", "Jira-tests/test_env_config.py", False),
        ("Jira API Key Validation", "Jira-tests/test_jira_api_key.py", True),
        ("MCP Server Configuration", "Jira-tests/test_mcp_server_config.py", True),
        ("Final Status Check", "Jira-tests/test_final_status.py", True),
    ]
    
    results = {}
    
    for test_name, script_path, use_uv in tests:
        success = run_test(test_name, script_path, use_uv)
        results[test_name] = success
        
        # If a critical test fails, show warning but continue
        if not success:
            print_warning(f"{test_name} failed, but continuing with remaining tests...")
    
    # Final summary
    print_section("Test Suite Results Summary")
    
    passed = 0
    total = len(tests)
    
    for test_name, success in results.items():
        if success:
            print_success(f"{test_name}: PASSED")
            passed += 1
        else:
            print_error(f"{test_name}: FAILED")
    
    print_section("Overall Results")
    
    if passed == total:
        print_success(f"🎉 All {total} tests passed!")
        print_info("Your MCP server is correctly configured for AI project access.")
        return 0
    elif passed > 0:
        print_warning(f"⚠️  {passed}/{total} tests passed")
        print_info("Some issues were detected. Check the test output above.")
        return 1
    else:
        print_error(f"💥 All tests failed!")
        print_info("Please check your configuration and try again.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print_warning("\n⚠️ Test suite interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"\n💥 Unexpected error: {e}")
        sys.exit(1)
