# Jira Test Scripts - Usage Guide

## Quick Start

To run all tests in the recommended order:

```bash
cd /path/to/mcp-atlassian
python3 Jira-tests/run_all_tests.py
```

## Individual Tests

### 1. Environment Configuration Check
```bash
python3 Jira-tests/test_env_config.py
```
**Purpose**: Validates that all environment variables are properly set
**Runtime**: ~1 second

### 2. Jira API Key Validation
```bash
uv run python3 Jira-tests/test_jira_api_key.py
```
**Purpose**: Tests authentication and permissions with Jira API
**Runtime**: ~5-10 seconds
**Requires**: Network access to Jira

### 3. MCP Server Configuration Test
```bash
uv run python3 Jira-tests/test_mcp_server_config.py
```
**Purpose**: Tests MCP server components and filtering
**Runtime**: ~10-15 seconds
**Requires**: Network access to Jira

### 4. Final Status Check
```bash
uv run python3 Jira-tests/test_final_status.py
```
**Purpose**: Comprehensive final validation
**Runtime**: ~10-15 seconds
**Requires**: Network access to Jira

### 5. Quick Connectivity Test (Manual)
```bash
python3 Jira-tests/test_quick_connectivity.py
```
**Purpose**: Generates curl command for manual testing
**Runtime**: Instant
**Note**: Provides curl command to run manually

## Expected Output When Working

When everything is configured correctly, you should see:

```
✅ All required environment variables are set correctly
✅ Authentication successful with Jira API
✅ AI project found and accessible
✅ Retrieved 78 total issues from AI project
✅ Project filtering is working correctly - only AI project available
✅ MCP Server is correctly configured for AI project access!
```

## Troubleshooting

### Common Error Messages and Solutions

#### "Missing required environment variables"
**Fix**: Ensure your `.env` file contains:
```env
JIRA_URL=https://your-instance.atlassian.net
JIRA_USERNAME=your.email@domain.com
JIRA_API_TOKEN=your_api_token_here
JIRA_PROJECTS_FILTER=AI
```

#### "Authentication failed - HTTP 401"
**Fix**: 
- Check your API token is correct and not expired
- Verify your username/email is correct
- Create a new API token at https://id.atlassian.com/manage-profile/security/api-tokens

#### "AI project not found or not accessible"
**Fix**:
- Verify the project key is exactly "AI" (case-sensitive)
- Check that you have "Browse Projects" permission for the AI project
- Ensure the project exists and is not archived

#### "Project filtering is not working"
**Fix**:
- Ensure `JIRA_PROJECTS_FILTER=AI` is uncommented in `.env`
- Restart the MCP server after changing the filter
- Verify the project key matches exactly (case-sensitive)

#### "ImportError: cannot import name..."
**Fix**: Run tests using `uv run python3` instead of just `python3` for tests that require MCP dependencies

## Test Development Notes

These tests were created to prevent and diagnose issues like:
- Commented out environment variables
- Incorrect API tokens or expired credentials
- Project access permission issues
- MCP server configuration problems
- Project filtering not working

The tests are designed to be:
- **Comprehensive**: Cover all aspects of the configuration
- **Clear**: Provide specific error messages and solutions
- **Fast**: Complete in under 30 seconds total
- **Reliable**: Work consistently across different environments

## Maintenance

When updating the MCP server or changing configuration:

1. Run the tests before making changes to establish baseline
2. Make your changes
3. Run the tests again to verify everything still works
4. If tests fail, the output will guide you to the specific issue

The tests are version-controlled and should be updated if the MCP server architecture changes significantly.
