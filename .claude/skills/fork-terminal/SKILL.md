---
name: Fork Terminal Skill
description: Fork a terminal session to a new terminal window. Use this when the user requests 'fork terminal' or 'create a new terminal' or 'new terminal: <command>' or 'fork session: <command>'.
---

# Overview

The Fork Terminal skill allows you to open a new terminal window to run commands, scripts, or even AI agents. This is useful for starting a long-running process without blocking your current terminal, or for getting help from an AI to write a script.

You can run commands directly on your machine, in a secure cloud sandbox for safety, or on remote SSH-accessible machines like NVIDIA DGX workstations.

## Common Examples

- **Open a new terminal and list files:**
  `fork terminal: ls -l`

- **Run a test script in the background:**
  `fork terminal --auto-close: npm test`

- **Ask an AI to write a Python script for you:**
  `fork terminal: use gemini to write a python script that prints 'hello world'`

- **Run a command in a secure sandbox:**
  `fork terminal in sandbox: python -c "import os; print(os.listdir())"`

- **Run a command on a remote DGX:**
  `fork terminal on dgx: nvidia-smi`

- **Use AI on remote GPU machine:**
  `fork terminal use claude on dgx to analyze GPU memory usage`

# Purpose

Fork a terminal session to a new terminal window. Using one agentic coding tools or raw cli commands.
Follow the `Instructions`, execute the `Workflow`, based on the `Cookbook`.

## Variables

ENABLE_RAW_CLI_COMMANDS: true
ENABLE_GEMINI_CLI: true
ENABLE_CODEX_CLI: true
ENABLE_CLAUDE_CODE: true
ENABLE_E2B_SANDBOX: true
ENABLE_SSH_BACKEND: true
AGENTIC_CODING_TOOLS: claude-code, codex-cli, gemini-cli
BACKENDS: local, e2b-sandbox, ssh-remote
E2B_TEMPLATE_ID: whhe4zpvcrwa0ahyu559
E2B_TEMPLATE_NAME: fork-terminal-ai-agents
SSH_CONFIG_PATH: ~/.config/fork-terminal/ssh_hosts.yaml

## Instructions

- Based on the user's request, follow the `Cookbook` to determine which tool to use.

### Auto-Close Feature

The fork_terminal tool supports an optional auto-close feature:
- Add `auto-close` or `--auto-close` to the command (at the beginning or end)
- **Behavior**: Commands run directly in the background and capture output instead of opening a visible terminal window
- **Output**: Results are captured and returned to you immediately after the command completes
- Works with all tools: raw CLI commands, Claude Code, Codex CLI, and Gemini CLI
- **Important**: When auto-close is used with agentic coding tools (Claude Code, Codex CLI, Gemini CLI), the tools will run in non-interactive mode to ensure the command exits after completion. Without auto-close, they run in interactive mode in a new terminal window for continued interaction.
- Examples:
  - "fork terminal auto-close: ls -la"
  - "fork terminal --auto-close use gemini to create hello.py"
  - "fork terminal: npm test auto-close"

### Using Conversation History with AI Agents (Summaries)

- **WHEN**: The user asks to fork a terminal with an AI agent and also requests a "summary" or wants the new agent to be aware of the work done so far. This feature is only for agentic tools (`AGENTIC_CODING_TOOLS`).
- **ACTION**: You should construct a detailed prompt for the new AI agent that includes the history of your current conversation.
- **HOW**:
    1.  **Read the template**: Look at the contents of `.claude/skills/fork-terminal/prompts/fork_summary_user_prompt.md`. This is your template for the new prompt.
    2.  **Gather History**: Collect the relevant parts of the conversation between you and the user.
    3.  **Construct the New Prompt**: Create a new prompt string by filling in the `<fill_in_the_history_here>` and `<fill_in_the_next_user_request_here>` sections of the template with the conversation history and the user's latest request.
    4.  **Execute**: Pass this newly constructed, detailed prompt to the `fork_terminal` tool.

- **KEYWORDS**: "summarize work so far", "include summary", "with summary"
- **EXAMPLES**:
  - "fork terminal use claude code to <xyz> summarize work so far"
  - "spin up a new terminal request <xyz> using claude code include summary"
  - "create a new terminal to <xyz> with claude code with summary"

## Workflow

1. Understand the user's request.
2. READ: `.claude/skills/fork-terminal/tools/fork_terminal.py` to understand our tooling.
3. Follow the `Cookbook` to determine which tool to use.
4. Execute the `.claude/skills/fork-terminal/tools/fork_terminal.py: fork_terminal(command: str)` tool.

## Cookbook

### SSH Remote Execution (DGX/GPU Workstations)

- IF: The user requests execution on a remote SSH host AND `ENABLE_SSH_BACKEND` is true.
- THEN: Read and execute: `.claude/skills/fork-terminal/cookbook/ssh-remote.md`
- TRIGGER KEYWORDS: "on <hostname>", "ssh to <hostname>", "remote:<hostname>", "@<hostname>"
- EXAMPLES:
  - "fork terminal on dgx: nvidia-smi"
  - "fork terminal use claude on dgx to analyze memory usage"
  - "fork terminal ssh to dgx: python train.py"
  - "fork terminal use gemini on dgx to optimize the training loop auto-close"
  - "@dgx nvidia-smi --query-gpu=utilization.gpu --format=csv"
- NOTES:
  - **Configuration**: Hosts configured in `~/.config/fork-terminal/ssh_hosts.yaml`
  - **Dependencies**: Requires `paramiko` and `pyyaml` packages
  - **Authentication**: Key-based SSH only (no passwords)
  - **GPU Support**: Auto-detects GPUs via nvidia-smi when `gpu_enabled: true`
  - **CUDA Setup**: Automatically configures PATH and LD_LIBRARY_PATH if `cuda_path` specified
  - **File Transfer**: Samba share (primary) or SFTP (fallback)
  - **API Key Injection**: Agent credentials injected at runtime, never stored on remote
  - **AI CLIs**: Must be pre-installed on the remote host (claude, gemini, codex)
  - **Connection Pooling**: Connections reused within session for performance

### E2B Sandbox (Isolated Execution)

- IF: The user requests sandbox execution AND `ENABLE_E2B_SANDBOX` is true.
- THEN: Read and execute: `.claude/skills/fork-terminal/cookbook/e2b-sandbox.md`
- TRIGGER KEYWORDS: "in sandbox", "use sandbox", "with sandbox", "sandbox:"
- EXAMPLES:
  - "fork terminal use gemini in sandbox to <xyz>"
  - "fork terminal use claude in sandbox to <xyz> auto-close"
  - "create a new terminal with codex in sandbox to <xyz>"
  - "fork terminal use gemini in sandbox to analyze my config.yaml"
  - "fork terminal use codex in sandbox to review my code.py"
  - "fork terminal in sandbox: python script.py" (raw CLI, uses same template)
- NOTES:
  - **E2B Template**: Uses custom template `fork-terminal-ai-agents` (whhe4zpvcrwa0ahyu559)
  - **Template Size**: ~723 MB (includes all CLIs and dependencies)
  - **Template Build Date**: 2026-01-05
  - Requires E2B_API_KEY credential
  - Executes in isolated cloud VM
  - More secure than local execution
  - Use for experimental or untrusted code
  - **Real CLIs Installed**:
    - Claude Code CLI v2.0.76 at `/usr/bin/claude`
    - Gemini CLI v0.22.5 at `/usr/bin/gemini`
    - Codex CLI v0.77.0 at `/usr/bin/codex`
    - Node.js v20.19.6 (required for CLIs)
    - Python 3.10 + pip
  - **Hybrid CLI/API Execution**: Sandbox uses real CLI tools by default, falls back to Python APIs if CLIs fail or are unavailable
  - **Template Architecture**: Single unified template serves both AI agents and raw CLI commands
    - AI agents (Claude/Gemini/Codex): Use installed CLIs
    - Raw commands (python, curl, git): Use standard tools
    - Future: Separate lightweight base template planned for raw CLI only
  - **Automatic File Upload**: Local files referenced in prompts are automatically detected, uploaded to the sandbox, and made available to the agent
    - Supports common file types: `.md`, `.py`, `.js`, `.json`, `.yaml`, `.txt`, `.csv`, etc.
    - Files are uploaded to `/home/user/` in the sandbox
    - File contents are injected into the agent's prompt for analysis
    - Works transparently - just reference files naturally in your prompt
  - **Automatic File Download**: Files created by agents in `/home/user/output/` are automatically downloaded after execution
    - Downloaded to `./sandbox-output/` by default (configurable)
    - Directory structure is preserved
    - Works for reports, code, images, data files, etc.
    - Agents should write output files to `/home/user/output/` for automatic retrieval

### Raw CLI Commands

- IF: The user requests a non-agentic coding tool AND `ENABLE_RAW_CLI_COMMANDS` is true.
- THEN: Read and execute: `.claude/skills/fork-terminal/cookbook/cli-command.md`
- EXAMPLES:
  - "Create a new terminal to <xyz> with ffmpeg"
  - "Create a new terminal to <xyz> with curl"
  - "Create a new terminal to <xyz> with python"

### Claude Code

- IF: The user requests a claude code agent to execute the command AND `ENABLE_CLAUDE_CODE` is true.
- THEN: Read and execute: `.claude/skills/fork-terminal/cookbook/claude-code.md`
- EXAMPLES:
  - "fork terminal use claude code to <xyz>"
  - "spin up a new terminal request <xyz> using claude code"
  - "create a new terminal to <xyz> with claude code"

### Codex CLI

- IF: The user requests a codex CLI agent to execute the command AND `ENABLE_CODEX_CLI` is true.
- THEN: Read and execute: `.claude/skills/fork-terminal/cookbook/codex-cli.md`
- EXAMPLES:
  - "fork terminal use codex to <xyz>"
  - "spin up a new terminal request <xyz> using codex"
  - "create a new terminal to <xyz> with codex"

### Gemini CLI

- IF: The user requests a gemini CLI agent to execute the command AND `ENABLE_GEMINI_CLI` is true.
- THEN: Read and execute: `.claude/skills/fork-terminal/cookbook/gemini-cli.md`
- EXAMPLES:
  - "fork terminal use gemini to <xyz>"
  - "spin up a new terminal request <xyz> with gemini"
  - "create a new terminal to <xyz> using gemini"
