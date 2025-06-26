# Jira Test Scripts

This folder contains various test scripts used to diagnose and validate the MCP server configuration for Jira access, specifically for the AI project.

## Test Scripts Overview

### 1. `test_jira_api_key.py`
**Purpose**: Validates Jira API key and permissions
- Tests basic authentication with Jira API
- Checks project access permissions
- Validates access to specific AI project
- Tests issue access within AI project
- Provides detailed feedback on any permission issues

**Usage**:
```bash
cd /path/to/mcp-atlassian
uv run python Jira-tests/test_jira_api_key.py
```

### 2. `test_env_config.py`
**Purpose**: Validates environment configuration
- Checks all required environment variables are set
- Validates optional configuration settings
- Verifies JIRA_PROJECTS_FILTER is set to "AI"
- Provides configuration recommendations

**Usage**:
```bash
cd /path/to/mcp-atlassian
python Jira-tests/test_env_config.py
```

### 3. `test_mcp_server_config.py`
**Purpose**: Tests full MCP server configuration
- Tests Jira configuration loading from environment
- Validates MCP server client initialization
- Tests project filtering functionality
- Verifies AI project access through MCP components

**Usage**:
```bash
cd /path/to/mcp-atlassian
uv run python Jira-tests/test_mcp_server_config.py
```

### 4. `test_final_status.py`
**Purpose**: Comprehensive final status check
- Runs all validation checks in sequence
- Provides complete status report
- Simulates MCP server filtering logic
- Gives final go/no-go recommendation

**Usage**:
```bash
cd /path/to/mcp-atlassian
uv run python Jira-tests/test_final_status.py
```

### 5. `test_quick_connectivity.py`
**Purpose**: Quick connectivity test without full setup
- Generates curl command for manual testing
- Minimal dependencies
- Good for initial troubleshooting

**Usage**:
```bash
cd /path/to/mcp-atlassian
python Jira-tests/test_quick_connectivity.py
```

## Common Issues and Solutions

### Issue: "Missing required environment variables"
**Solution**: Ensure your `.env` file contains:
```
JIRA_URL=https://your-instance.atlassian.net
JIRA_USERNAME=your.email@domain.com
JIRA_API_TOKEN=your_api_token_here
JIRA_PROJECTS_FILTER=AI
```

### Issue: "Authentication failed"
**Solutions**:
1. Verify your API token is correct and not expired
2. Check that your username/email is correct
3. Ensure you have proper permissions in Jira

### Issue: "AI project not accessible"
**Solutions**:
1. Verify the project key is exactly "AI" (case-sensitive)
2. Check that you have "Browse Projects" permission for the AI project
3. Ensure the project exists and is not archived

### Issue: "Project filter not working"
**Solutions**:
1. Ensure `JIRA_PROJECTS_FILTER=AI` is uncommented in `.env`
2. Restart the MCP server after changing the filter
3. Verify the project key matches exactly (case-sensitive)

## Running All Tests

To run a complete test suite:

```bash
cd /path/to/mcp-atlassian

# 1. Test environment configuration
python Jira-tests/test_env_config.py

# 2. Test API key and permissions
uv run python Jira-tests/test_jira_api_key.py

# 3. Test MCP server configuration
uv run python Jira-tests/test_mcp_server_config.py

# 4. Final comprehensive check
uv run python Jira-tests/test_final_status.py
```

## Expected Results

When everything is working correctly, you should see:
- ✅ All environment variables are set correctly
- ✅ Authentication successful with Jira API
- ✅ AI project is accessible with X issues
- ✅ Project filtering is working correctly - only AI project available
- ✅ MCP server configuration is ready for AI project access

## Troubleshooting Tips

1. **Always run tests in order**: Environment → API Key → MCP Config → Final Status
2. **Check the logs**: Enable verbose logging with `MCP_VERBOSE=true`
3. **Verify credentials**: Use `test_quick_connectivity.py` for manual curl testing
4. **Check project access**: Ensure you can access the AI project through Jira web interface
5. **Restart after changes**: Restart MCP server after changing environment variables

## Historical Context

These tests were created during the resolution of an issue where:
- The Jira API key was valid and had access to 21 projects including "AI"
- The `JIRA_PROJECTS_FILTER=AI` line was commented out in `.env`
- This prevented the MCP server from filtering to only the AI project
- After uncommenting the filter, all functionality worked correctly

The tests help prevent similar configuration issues in the future.
