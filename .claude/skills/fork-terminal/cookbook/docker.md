# Docker Cookbook

## Overview

Execute AI agents and commands in isolated Docker containers on your local machine. Free, offline, reproducible.

## Triggers

User requests Docker execution with keywords:
- "in docker"
- "use docker"
- "with docker"
- "docker:"

## Supported Agents

- Claude Code
- Gemini CLI
- Codex CLI
- Raw CLI commands (python, curl, git, etc.)

## Prerequisites

1. **Docker**: Docker daemon must be running locally
   ```bash
   docker info  # Verify Docker is running
   ```

2. **Agent Credentials**: API keys for the agents you want to use (set as environment variables)
   - ANTHROPIC_API_KEY (Claude)
   - GEMINI_API_KEY (Gemini)
   - OPENAI_API_KEY (Codex)

3. **Docker Image**: Auto-built on first use from `Dockerfile.agents`
   - No manual setup required
   - Pre-installs: Claude Code, Gemini CLI, Codex CLI, Python, Node.js

## Command Structure

```
fork terminal use <agent> in docker to <task> [auto-close]
```

**Components**:
- `<agent>`: claude, gemini, or codex (optional for raw CLI)
- `in docker`: Triggers Docker backend
- `<task>`: The prompt/task for the agent
- `auto-close` (optional): Remove container when done

## Examples

### AI Agents in Docker

```bash
# Claude in Docker
"fork terminal use claude in docker to analyze this codebase"

# Gemini in Docker with auto-close
"fork terminal use gemini in docker to write tests auto-close"

# Codex in Docker
"fork terminal use codex in docker to refactor the auth module"
```

### Raw CLI in Docker

```bash
# Run Python script in isolation
"fork terminal in docker: python script.py"

# Run untrusted code safely
"fork terminal docker: npm test auto-close"
```

## Workflow

When user requests Docker execution:

1. **Detect Backend**: Check for Docker keywords
2. **Detect Agent**: Identify which AI agent to use (if any)
3. **Check Docker**: Verify Docker daemon is running
4. **Build Image**: Auto-build `fork-terminal-agents` if not found locally
5. **Resolve Credentials**: Get API key from environment variables
6. **Run Container**: Execute with volume mount and credential injection
7. **Return Results**: Display output
8. **Cleanup** (if auto-close): Remove container with `--rm`

## How It Works

- Working directory is mounted as `/workspace` in the container
- Only the relevant agent's API key is injected via `-e` flag
- Auto-close uses `docker run --rm` (container removed after exit)
- Image is auto-built from `Dockerfile.agents` on first use

## Error Handling

### Docker Not Running
```
❌ Docker daemon is not running or not installed.
```
**Solution**: Start Docker Desktop or the Docker daemon

### Image Build Failed
```
❌ Docker image 'fork-terminal-agents' not found and auto-build failed.
```
**Solution**: Build manually: `docker build -t fork-terminal-agents -f tools/Dockerfile.agents tools/`

### Missing API Key
```
⚠️ ANTHROPIC_API_KEY not found in environment
```
**Solution**: Export the required API key: `export ANTHROPIC_API_KEY="your-key"`
