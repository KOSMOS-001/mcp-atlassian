#!/usr/bin/env python3
"""
Live MCP Server Test Script
This script connects to a running MCP server via HTTP and tests the actual tools
to verify they work correctly with the AI project filtering.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add the source directory to path for MCP client
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    import httpx
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from mcp.client.session import ClientSession
    from mcp.types import Tool
except ImportError as e:
    print(f"❌ Missing required dependency: {e}")
    print("💡 Install with: pip install mcp httpx")
    sys.exit(1)

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

class MCPServerTester:
    """Test the live MCP server."""
    
    def __init__(self, server_url: str = "http://localhost:9000"):
        """Initialize the tester with server URL."""
        self.server_url = server_url
        self.mcp_url = f"{server_url}/mcp/"
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def test_server_health(self) -> bool:
        """Test if the MCP server is responding."""
        print_section("Testing Server Health")
        
        try:
            # Test health endpoint
            response = await self.client.get(f"{self.server_url}/healthz")
            if response.status_code == 200:
                print_success("Health endpoint responding")
            else:
                print_warning(f"Health endpoint returned {response.status_code}")
            
            # Test MCP endpoint availability - just check if it responds to OPTIONS
            response = await self.client.options(f"{self.server_url}/mcp/")
            if response.status_code in [200, 204, 405]:  # Various acceptable responses
                print_success("MCP endpoint is accessible")
                return True
            else:
                print_warning(f"MCP endpoint returned {response.status_code} for OPTIONS")
                # Try a basic test request instead
                try:
                    test_response = await self.client.post(
                        f"{self.server_url}/mcp/",
                        json={"jsonrpc": "2.0", "id": "test", "method": "ping", "params": {}},
                        headers={
                            "Content-Type": "application/json",
                            "Accept": "application/json, text/event-stream"
                        }
                    )
                    if test_response.status_code in [200, 400, 404]:  # Even errors show it's responding
                        print_success("MCP endpoint is accessible (via test request)")
                        return True
                    else:
                        print_error(f"MCP endpoint test returned {test_response.status_code}")
                        return False
                except Exception as e:
                    print_error(f"MCP endpoint test failed: {e}")
                    return False
                
        except Exception as e:
            print_error(f"Server health check failed: {e}")
            return False
    
    async def call_mcp_method(self, method: str, params: dict = None) -> dict:
        """Call an MCP method via HTTP."""
        if params is None:
            params = {}
            
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params
        }
        
        try:
            response = await self.client.post(
                self.mcp_url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
            
            result = response.json()
            
            if "error" in result:
                raise Exception(f"MCP Error: {result['error']}")
            
            return result.get("result", {})
            
        except Exception as e:
            print_error(f"MCP call failed for {method}: {e}")
            raise
    
    async def test_list_tools(self) -> list:
        """Test listing available tools."""
        print_section("Testing List Tools")
        
        try:
            result = await self.call_mcp_method("tools/list")
            tools = result.get("tools", [])
            
            print_success(f"Found {len(tools)} available tools")
            
            # Filter for Jira tools
            jira_tools = [tool for tool in tools if tool.get("name", "").startswith("jira_")]
            print_info(f"Jira tools available: {len(jira_tools)}")
            
            for tool in jira_tools[:10]:  # Show first 10
                print_info(f"  • {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')[:80]}...")
            
            if len(jira_tools) > 10:
                print_info(f"  ... and {len(jira_tools) - 10} more Jira tools")
            
            return jira_tools
            
        except Exception as e:
            print_error(f"Failed to list tools: {e}")
            return []
    
    async def test_jira_get_all_projects(self) -> bool:
        """Test the jira_get_all_projects tool."""
        print_section("Testing jira_get_all_projects")
        
        try:
            result = await self.call_mcp_method("tools/call", {
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
                elif len(projects_data) > 1:
                    print_warning(f"⚠️ Expected only AI project, but got {len(projects_data)} projects")
                    ai_projects = [p for p in projects_data if p.get("key") == "AI"]
                    if ai_projects:
                        print_info("AI project is included in results")
                    else:
                        print_error("AI project is NOT in results")
                    return False
                else:
                    print_error("No projects returned or AI project missing")
                    return False
            else:
                print_error(f"Expected list of projects, got {type(projects_data)}")
                return False
                
        except Exception as e:
            print_error(f"Failed to test jira_get_all_projects: {e}")
            return False
    
    async def test_jira_search(self) -> bool:
        """Test the jira_search tool."""
        print_section("Testing jira_search")
        
        try:
            result = await self.call_mcp_method("tools/call", {
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
                else:
                    print_warning(f"    ⚠️ Issue {key} is from project {project_key}, not AI")
            
            if ai_issues == len(issues) and len(issues) > 0:
                print_success("✅ All search results are from AI project - filtering working correctly")
                return True
            elif len(issues) == 0:
                print_warning("⚠️ No issues returned from search")
                return False
            else:
                print_error(f"❌ Only {ai_issues}/{len(issues)} issues are from AI project")
                return False
                
        except Exception as e:
            print_error(f"Failed to test jira_search: {e}")
            return False
    
    async def test_jira_get_project_issues(self) -> bool:
        """Test the jira_get_project_issues tool."""
        print_section("Testing jira_get_project_issues")
        
        try:
            result = await self.call_mcp_method("tools/call", {
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
            
            if total > 0 and len(issues) > 0:
                print_success("✅ Successfully retrieved AI project issues")
                return True
            else:
                print_error("❌ No issues retrieved from AI project")
                return False
                
        except Exception as e:
            print_error(f"Failed to test jira_get_project_issues: {e}")
            return False
    
    async def run_all_tests(self) -> bool:
        """Run all MCP server tests."""
        print_section("Live MCP Server Test Suite")
        print_info(f"Testing server at: {self.server_url}")
        
        results = {}
        
        # Test server health
        results["health"] = await self.test_server_health()
        if not results["health"]:
            print_error("Server health check failed - aborting tests")
            return False
        
        # Test tools listing
        tools = await self.test_list_tools()
        results["list_tools"] = len(tools) > 0
        
        if not results["list_tools"]:
            print_error("No tools available - aborting tests")
            return False
        
        # Test specific Jira tools
        results["get_all_projects"] = await self.test_jira_get_all_projects()
        results["search"] = await self.test_jira_search()
        results["get_project_issues"] = await self.test_jira_get_project_issues()
        
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
            print_info("Your MCP server is working correctly with AI project filtering.")
            return True
        else:
            print_warning(f"⚠️ {passed}/{total} tests passed")
            print_info("Some issues were detected with the live server.")
            return False

async def main():
    """Main test function."""
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
        default=9000,
        help="Server port (default: 9000)"
    )
    
    args = parser.parse_args()
    
    # Construct URL if port is provided
    if args.port != 9000:
        server_url = f"http://localhost:{args.port}"
    else:
        server_url = args.url
    
    try:
        async with MCPServerTester(server_url) as tester:
            success = await tester.run_all_tests()
            
            if success:
                print_success("\n🎉 Live MCP server test completed successfully!")
                print_info("\nYour MCP server is ready for use in frontend applications!")
                sys.exit(0)
            else:
                print_error("\n💥 Live MCP server test failed!")
                print_info("\nCheck the server logs and configuration.")
                sys.exit(1)
                
    except KeyboardInterrupt:
        print_warning("\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"\n💥 Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
