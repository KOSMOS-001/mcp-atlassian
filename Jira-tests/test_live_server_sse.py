#!/usr/bin/env python3
"""
SSE MCP Server Test Script
This script tests the running MCP server using the SSE transport
which is simpler than streamable-HTTP.
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

def test_health_endpoint(base_url: str) -> bool:
    """Test the health endpoint."""
    try:
        url = f"{base_url}/healthz"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                print_success("Health endpoint responding")
                return True
            else:
                print_error(f"Health endpoint returned {response.status}")
                return False
    except Exception as e:
        print_error(f"Health endpoint error: {str(e)[:100]}...")
        return False

def get_sse_endpoint(base_url: str) -> str | None:
    """Get the SSE endpoint by connecting to the SSE endpoint."""
    try:
        url = f"{base_url}/sse"
        req = urllib.request.Request(url)
        
        with urllib.request.urlopen(req, timeout=5) as response:
            # Read line by line until we find the endpoint
            for _ in range(10):  # Read max 10 lines
                try:
                    line = response.readline().decode('utf-8').strip()
                    if line.startswith('data: /messages/'):
                        endpoint = line[6:]  # Remove 'data: ' prefix
                        print_success(f"Got SSE endpoint: {endpoint}")
                        return endpoint
                except Exception:
                    break
            
            print_error("No endpoint found in SSE response")
            return None
            
    except Exception as e:
        print_error(f"SSE endpoint discovery error: {str(e)[:100]}...")
        return None

def send_sse_request(base_url: str, endpoint: str, request_data: Dict[str, Any]) -> Dict[str, Any] | None:
    """Send a request to the SSE endpoint."""
    try:
        url = f"{base_url}{endpoint}"
        
        # Convert request to JSON
        json_data = json.dumps(request_data).encode('utf-8')
        
        # Create request with proper headers for SSE
        req = urllib.request.Request(
            url,
            data=json_data,
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Cache-Control': 'no-cache'
            },
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            # SSE transport should return JSON directly
            response_text = response.read().decode('utf-8')
            
            # Try to parse as JSON
            try:
                return json.loads(response_text)
            except json.JSONDecodeError:
                print_warning(f"Response not valid JSON: {response_text[:100]}...")
                return None
                
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print_error(f"HTTP {e.code}: {error_body[:200]}...")
        return None
    except Exception as e:
        print_error(f"Request error: {str(e)[:100]}...")
        return None

def test_list_tools(base_url: str, endpoint: str) -> bool:
    """Test listing available tools."""
    print_info("Testing list tools...")
    
    request_data = {
        "jsonrpc": "2.0",
        "id": "test-list-tools",
        "method": "tools/list",
        "params": {}
    }
    
    response = send_sse_request(base_url, endpoint, request_data)
    
    if response is None:
        print_error("Failed to get response from list tools")
        return False
    
    if "error" in response:
        print_error(f"List tools error: {response['error']}")
        return False
    
    if "result" in response and "tools" in response["result"]:
        tools = response["result"]["tools"]
        print_success(f"Found {len(tools)} tools available")
        
        # Show first few tools
        for i, tool in enumerate(tools[:3]):
            tool_name = tool.get("name", "Unknown")
            tool_desc = tool.get("description", "No description")[:60]
            print_info(f"  Tool {i+1}: {tool_name} - {tool_desc}...")
        
        if len(tools) > 3:
            print_info(f"  ... and {len(tools) - 3} more tools")
        
        return True
    else:
        print_error("Invalid response format for list tools")
        return False

def test_jira_projects_call(base_url: str, endpoint: str) -> bool:
    """Test calling a Jira tool to list projects."""
    print_info("Testing Jira list projects tool...")
    
    request_data = {
        "jsonrpc": "2.0",
        "id": "test-jira-projects",
        "method": "tools/call",
        "params": {
            "name": "jira_list_projects",
            "arguments": {}
        }
    }
    
    response = send_sse_request(base_url, endpoint, request_data)
    
    if response is None:
        print_error("Failed to get response from Jira list projects")
        return False
    
    if "error" in response:
        print_error(f"Jira list projects error: {response['error']}")
        return False
    
    if "result" in response:
        result = response["result"]
        if "content" in result:
            content = result["content"]
            if isinstance(content, list) and len(content) > 0:
                text_content = content[0].get("text", "")
                print_success("Jira list projects call successful")
                
                # Try to parse as JSON to show project info
                try:
                    projects_data = json.loads(text_content)
                    if isinstance(projects_data, list):
                        print_info(f"Found {len(projects_data)} Jira projects")
                        for project in projects_data[:2]:  # Show first 2
                            key = project.get("key", "?")
                            name = project.get("name", "Unknown")
                            print_info(f"  Project: {key} - {name}")
                        if len(projects_data) > 2:
                            print_info(f"  ... and {len(projects_data) - 2} more projects")
                    else:
                        print_info(f"Projects data: {str(projects_data)[:100]}...")
                except json.JSONDecodeError:
                    print_info(f"Response: {text_content[:100]}...")
                
                return True
            else:
                print_error("Empty or invalid content in response")
                return False
        else:
            print_error("No content in tool call response")
            return False
    else:
        print_error("Invalid response format for tool call")
        return False

def main():
    """Main test function."""
    print_section("SSE MCP Server Test")
    
    base_url = "http://localhost:9000"
    print_info(f"Testing server at: {base_url}")
    print_info("Using SSE transport")
    
    # Test 1: Health check
    print_section("Testing Server Health")
    if not test_health_endpoint(base_url):
        print_error("Server health check failed - aborting tests")
        return False
    
    # Test 2: Get SSE endpoint
    print_section("Getting SSE Endpoint")
    endpoint = get_sse_endpoint(base_url)
    if not endpoint:
        print_error("Failed to get SSE endpoint - aborting tests")
        return False
    
    # Test 3: List tools
    print_section("Testing MCP Tools List")
    if not test_list_tools(base_url, endpoint):
        print_error("List tools test failed")
        return False
    
    # Test 4: Call a Jira tool
    print_section("Testing Jira Tool Call")
    if not test_jira_projects_call(base_url, endpoint):
        print_error("Jira tool call test failed")
        return False
    
    # Success
    print_section("Test Results")
    print_success("All tests passed!")
    print_info("✅ Server is responding correctly")
    print_info("✅ Tools are available")
    print_info("✅ Jira integration is working")
    print_info("")
    print_info("🎉 Your MCP server is ready for use!")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            print("\n💥 Live MCP server test failed!")
            print_info("\nCheck the server logs and configuration.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)
