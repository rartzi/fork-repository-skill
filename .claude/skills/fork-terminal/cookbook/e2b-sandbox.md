# E2B Sandbox Cookbook

## Overview

Execute AI agents in isolated E2B cloud sandboxes for secure, scalable agent deployment.

## Triggers

User requests sandbox execution with keywords:
- "in sandbox"
- "use sandbox"
- "with sandbox"
- "sandbox:"

## Supported Agents

- Claude Code
- Gemini CLI
- Codex CLI

## Prerequisites

1. **E2B API Key**: Required for sandbox access
   - Get key from: https://e2b.dev/
   - Set in environment, keychain, or .env file

2. **Agent Credentials**: API keys for the agents you want to use
   - ANTHROPIC_API_KEY (Claude)
   - GEMINI_API_KEY (Gemini)
   - OPENAI_API_KEY (Codex)

3. **Dependencies**: Install E2B SDK
   ```bash
   pip install -r requirements.txt
   ```

## Command Structure

```
fork terminal use <agent> in sandbox to <task> [auto-close]
```

**Components**:
- `<agent>`: claude, gemini, or codex
- `in sandbox`: Triggers E2B backend
- `<task>`: The prompt/task for the agent
- `auto-close` (optional): Close sandbox when done

## Examples

### Claude Code in Sandbox

```bash
# Basic sandbox execution
"fork terminal use claude in sandbox to analyze this Python file"

# With auto-close
"fork terminal use claude in sandbox to fix bugs auto-close"

# Code generation
"fork terminal use claude in sandbox to create a REST API"
```

### Gemini CLI in Sandbox

```bash
# Generate code
"fork terminal use gemini in sandbox to write hello world in Python"

# Test risky code
"fork terminal use gemini in sandbox to test this experimental feature auto-close"

# Data analysis
"fork terminal use gemini in sandbox to analyze this CSV file"
```

### Codex CLI in Sandbox

```bash
# Code review
"fork terminal use codex in sandbox to review this pull request"

# Refactoring
"fork terminal use codex in sandbox to refactor the auth module auto-close"

# Documentation
"fork terminal use codex in sandbox to generate API docs"
```

## Workflow

When user requests sandbox execution:

1. **Detect Backend**: Check for sandbox keywords
2. **Detect Agent**: Identify which AI agent to use
3. **Resolve Credentials**: Use waterfall resolution
   - Environment variables
   - System keychain
   - .env file
   - Config files
4. **Create Sandbox**: Initialize E2B sandbox with agent credential
5. **Execute**: Run agent command in isolated environment
6. **Return Results**: Display output and sandbox ID
7. **Cleanup** (if auto-close): Close sandbox

## Security Benefits

### Isolation
- Each sandbox is a fresh cloud VM
- No access to your local filesystem
- No access to other credentials
- Network isolated from your machine

### Principle of Least Privilege
- Only the specific agent credential is injected
- No AWS keys, GitHub tokens, or SSH keys
- Limited blast radius if agent misbehaves

### Safe Experimentation
- Test untrusted code without risk
- Run experimental features safely
- Parallel execution without conflicts

## Error Handling

### Missing E2B SDK
```
❌ E2B sandbox backend not available.
Install dependencies: pip install -r requirements.txt
```

**Solution**: Run `pip install -r requirements.txt`

### Missing Credentials
```
❌ Credential not found for gemini (GEMINI_API_KEY).
Checked: environment, keychain, .env, config files
```

**Solution**: Set the required API key in one of the credential sources

### Agent Not Specified
```
❌ Sandbox backend requires an AI agent (claude, gemini, or codex).
Example: 'use gemini in sandbox to create hello.py'
```

**Solution**: Include agent name in command

## Credential Resolution

The sandbox backend uses waterfall credential resolution:

1. **Environment Variable** (highest priority)
   ```bash
   export GEMINI_API_KEY="your-key"
   ```

2. **System Keychain**
   ```bash
   # macOS
   security add-generic-password -s GEMINI_API_KEY -a $USER -w "your-key"
   ```

3. **.env File**
   ```bash
   # .env
   GEMINI_API_KEY=your-key
   ```

4. **Config File** (lowest priority)
   ```bash
   # ~/.config/gemini/credentials.json
   {"api_key": "your-key"}
   ```

## Comparison: Local vs Sandbox

| Aspect | Local Terminal | E2B Sandbox |
|--------|----------------|-------------|
| **Speed** | Instant | Network latency |
| **Cost** | Free | E2B service costs |
| **Security** | Full system access | Isolated VM |
| **Use Case** | Trusted tasks | Experimental/risky |

## Advanced Usage

### Testing with Override Credentials

```bash
# Override credential for testing
export GEMINI_API_KEY="test-key-12345"

# Run in sandbox with test key
"fork terminal use gemini in sandbox to test feature"

# Unset when done
unset GEMINI_API_KEY
```

### Debugging Sandbox Execution

The sandbox backend prints verbose output:
- ✓ Credential resolution status
- 📦 Sandbox creation
- 🚀 Command execution
- ✅ Results
- 🔒 Cleanup (if auto-close)

### Keeping Sandboxes Open

Omit `auto-close` to keep sandbox running:
```bash
"fork terminal use claude in sandbox to start dev server"
```

The sandbox stays active for continued interaction or debugging.

## Notes

- Sandbox execution is non-interactive by default
- Use `-p` flag for agentic tools to ensure clean exit
- Auto-close automatically applies `-p` flag
- Sandbox IDs are displayed for reference
