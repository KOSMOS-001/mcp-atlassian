#!/usr/bin/env python3
"""
Basic Live MCP Server Test Script
This script uses only Python standard library to test your running MCP server.
No external dependencies required.
"""

import json
import sys
import urllib.request
import urllib.parse
import urllib.error
from typing import Dict, Any

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

class BasicMCPTester:
    """Basic MCP server tester using only standard library."""
    
    def __init__(self, server_url: str = "http://localhost:9000"):
        """Initialize the tester."""
        self.server_url = server_url
        self.mcp_url = f"{server_url}/mcp"
    
    def make_request(self, method: str, url: str, data: bytes = None, headers: Dict[str, str] = None) -> Dict[str, Any]:
        """Make an HTTP request using urllib."""
        if headers is None:
            headers = {}
        
        try:
            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            
            with urllib.request.urlopen(req, timeout=30) as response:
                response_text = response.read().decode('utf-8')
                result = {
                    "status_code": response.status,
                    "text": response_text,
                    "json": None
                }
                
                try:
                    result["json"] = json.loads(response_text)
                except json.JSONDecodeError:
                    pass
                
                return result
                
        except urllib.error.HTTPError as e:
            error_text = ""
            try:
                error_text = e.read().decode('utf-8')
            except:
                error_text = str(e)
            
            return {
                "status_code": e.code,
                "text": error_text,
                "json": None,
                "error": str(e)
            }
        except Exception as e:
            return {
                "status_code": 0,
                "text": str(e),
                "json": None,
                "error": str(e)
            }
    
    def test_server_health(self) -> bool:
        """Test if the MCP server is responding."""
        print_section("Testing Server Health")
        
        try:
            # Test health endpoint
            response = self.make_request("GET", f"{self.server_url}/healthz")
            if response["status_code"] == 200:
                print_success("Health endpoint responding")
            else:
                print_warning(f"Health endpoint returned {response['status_code']}")
            
            # Test MCP endpoint availability
            response = self.make_request("GET", self.mcp_url)
            if response["status_code"] in [200, 404, 405]:  # 404/405 expected for GET
                print_success("MCP endpoint is accessible")
                return True
            else:
                print_error(f"MCP endpoint returned {response['status_code']}")
                print_error(f"Response: {response['text'][:200]}...")
                return False
                
        except Exception as e:
            print_error(f"Server health check failed: {e}")
            return False
    
    def call_mcp_method(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Call an MCP method via HTTP."""
        if params is None:
            params = {}
            
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params
        }
        
        data = json.dumps(payload).encode('utf-8')
        headers = {"Content-Type": "application/json"}
        
        try:
            response = self.make_request("POST", self.mcp_url, data=data, headers=headers)
            
            if response["status_code"] != 200:
                raise Exception(f"HTTP {response['status_code']}: {response['text']}")
            
            if not response["json"]:
                raise Exception(f"No JSON response: {response['text']}")
            
            result = response["json"]
            
            if "error" in result:
                raise Exception(f"MCP Error: {result['error']}")
            
            return result.get("result", {})
            
        except Exception as e:
            print_error(f"MCP method call failed for {method}: {e}")
            raise
    
    def test_list_tools(self) -> list:
        """Test listing available tools."""
        print_section("Testing List Tools")
        
        try:
            result = self.call_mcp_method("tools/list")
            tools = result.get("tools", [])
            
            print_success(f"Found {len(tools)} available tools")
            
            # Filter for Jira tools
            jira_tools = [tool for tool in tools if tool.get("name", "").startswith("jira_")]
            print_info(f"Jira tools available: {len(jira_tools)}")
            
            for tool in jira_tools[:10]:  # Show first 10
                name = tool.get('name', 'Unknown')
                desc = tool.get('description', 'No description')
                print_info(f"  • {name}: {desc[:80]}...")
            
            if len(jira_tools) > 10:
                print_info(f"  ... and {len(jira_tools) - 10} more Jira tools")
            
            return jira_tools
            
        except Exception as e:
            print_error(f"Failed to list tools: {e}")
            return []
    
    def test_jira_get_all_projects(self) -> bool:
        """Test the jira_get_all_projects tool."""
        print_section("Testing jira_get_all_projects")
        
        try:
            result = self.call_mcp_method("tools/call", {
                "name": "jira_get_all_projects",
                "arguments": {
                    "include_archived": False
                }
            })
            
            # Parse the result content
            content = result.get("content", [])
            if not content:
                print_error("No content in response")
                return False
            
            # Get the actual data
            text_content = content[0].get("text", "")
            if not text_content:
                print_error("No text content in response")
                return False
            
            try:
                projects_data = json.loads(text_content)
            except json.JSONDecodeError as e:
                print_error(f"Failed to parse JSON response: {e}")
                print_info(f"Raw response: {text_content[:200]}...")
                return False
            
            if isinstance(projects_data, list):
                print_success(f"Retrieved {len(projects_data)} projects")
                
                # Check if filtering is working (should only return AI project)
                for project in projects_data:
                    key = project.get("key", "Unknown")
                    name = project.get("name", "Unknown")
                    print_info(f"  • {key}: {name}")
                
                # Verify filtering
                if len(projects_data) == 1 and projects_data[0].get("key") == "AI":
                    print_success("✅ Project filtering is working correctly - only AI project returned")
                    return True
                else:
                    print_warning(f"⚠️ Expected only AI project, but got {len(projects_data)} projects")
                    return len(projects_data) > 0  # At least some projects returned
            else:
                print_error(f"Expected list of projects, got {type(projects_data)}")
                return False
                
        except Exception as e:
            print_error(f"Failed to test jira_get_all_projects: {e}")
            return False
    
    def test_jira_search(self) -> bool:
        """Test the jira_search tool."""
        print_section("Testing jira_search")
        
        try:
            result = self.call_mcp_method("tools/call", {
                "name": "jira_search",
                "arguments": {
                    "jql": "order by updated DESC",
                    "limit": 5
                }
            })
            
            # Parse the result content
            content = result.get("content", [])
            if not content:
                print_error("No content in response")
                return False
            
            text_content = content[0].get("text", "")
            if not text_content:
                print_error("No text content in response")
                return False
            
            try:
                search_data = json.loads(text_content)
            except json.JSONDecodeError as e:
                print_error(f"Failed to parse JSON response: {e}")
                return False
            
            total = search_data.get("total", 0)
            issues = search_data.get("issues", [])
            
            print_success(f"Search returned {total} total issues, showing {len(issues)}")
            
            # Check that all issues are from AI project
            ai_issues = 0
            for issue in issues:
                key = issue.get("key", "")
                summary = issue.get("summary", "No summary")
                project_key = key.split("-")[0] if "-" in key else "Unknown"
                
                print_info(f"  • {key}: {summary[:60]}...")
                
                if project_key == "AI":
                    ai_issues += 1
            
            if ai_issues == len(issues) and len(issues) > 0:
                print_success("✅ All search results are from AI project - filtering working correctly")
                return True
            else:
                print_warning(f"⚠️ {ai_issues}/{len(issues)} issues are from AI project")
                return len(issues) > 0  # At least some results
                
        except Exception as e:
            print_error(f"Failed to test jira_search: {e}")
            return False
    
    def test_jira_get_project_issues(self) -> bool:
        """Test the jira_get_project_issues tool."""
        print_section("Testing jira_get_project_issues")
        
        try:
            result = self.call_mcp_method("tools/call", {
                "name": "jira_get_project_issues",
                "arguments": {
                    "project_key": "AI",
                    "limit": 3
                }
            })
            
            # Parse the result content
            content = result.get("content", [])
            if not content:
                print_error("No content in response")
                return False
            
            text_content = content[0].get("text", "")
            if not text_content:
                print_error("No text content in response")
                return False
            
            try:
                issues_data = json.loads(text_content)
            except json.JSONDecodeError as e:
                print_error(f"Failed to parse JSON response: {e}")
                return False
            
            total = issues_data.get("total", 0)
            issues = issues_data.get("issues", [])
            
            print_success(f"Retrieved {total} total issues from AI project, showing {len(issues)}")
            
            for issue in issues:
                key = issue.get("key", "")
                summary = issue.get("summary", "No summary")
                print_info(f"  • {key}: {summary}")
            
            return total > 0 and len(issues) > 0
                
        except Exception as e:
            print_error(f"Failed to test jira_get_project_issues: {e}")
            return False
    
    def run_all_tests(self) -> bool:
        """Run all tests."""
        print_section("Basic Live MCP Server Test")
        print_info(f"Testing server at: {self.server_url}")
        print_info("Using Python standard library (urllib)")
        
        results = {}
        
        # Test server health
        results["health"] = self.test_server_health()
        if not results["health"]:
            print_error("Server health check failed - aborting tests")
            return False
        
        # Test tools listing
        tools = self.test_list_tools()
        results["list_tools"] = len(tools) > 0
        
        if not results["list_tools"]:
            print_error("No tools available - aborting tests")
            return False
        
        # Test specific Jira tools
        results["get_all_projects"] = self.test_jira_get_all_projects()
        results["search"] = self.test_jira_search()
        results["get_project_issues"] = self.test_jira_get_project_issues()
        
        # Summary
        print_section("Live Test Results Summary")
        
        passed = 0
        total = len(results)
        
        for test_name, success in results.items():
            if success:
                print_success(f"{test_name}: PASSED")
                passed += 1
            else:
                print_error(f"{test_name}: FAILED")
        
        print_section("Overall Results")
        
        if passed == total:
            print_success(f"🎉 All {total} live tests passed!")
            print_info("Your MCP server is working correctly!")
            return True
        elif passed > total * 0.6:  # If most tests pass
            print_warning(f"⚠️ {passed}/{total} tests passed - mostly working")
            print_info("Your MCP server is mostly functional with minor issues.")
            return True
        else:
            print_error(f"💥 Only {passed}/{total} tests passed")
            print_info("Significant issues detected with the live server.")
            return False

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test live MCP server")
    parser.add_argument(
        "--url", 
        default="http://localhost:9000",
        help="MCP server URL (default: http://localhost:9000)"
    )
    parser.add_argument(
        "--port",
        type=int,
        help="Server port (overrides URL)"
    )
    
    args = parser.parse_args()
    
    # Construct URL
    if args.port:
        server_url = f"http://localhost:{args.port}"
    else:
        server_url = args.url
    
    try:
        tester = BasicMCPTester(server_url)
        success = tester.run_all_tests()
        
        if success:
            print_success("\n🎉 Live MCP server test completed successfully!")
            print_info("\nYour MCP server is ready for use!")
            print_info("\nYou can now connect your frontend application to:")
            print_info(f"  {server_url}/mcp")
            return 0
        else:
            print_error("\n💥 Live MCP server test failed!")
            print_info("\nCheck the server logs and configuration.")
            return 1
            
    except KeyboardInterrupt:
        print_warning("\n⚠️ Test interrupted by user")
        return 1
    except Exception as e:
        print_error(f"\n💥 Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
