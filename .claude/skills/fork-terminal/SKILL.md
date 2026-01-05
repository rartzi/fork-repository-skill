---
name: Fork Terminal Skill
description: Fork a terminal session to a new terminal window. Use this when the user requests 'fork terminal' or 'create a new terminal' or 'new terminal: <command>' or 'fork session: <command>'.
---

# Purpose

Fork a terminal session to a new terminal window. Using one agentic coding tools or raw cli commands.
Follow the `Instructions`, execute the `Workflow`, based on the `Cookbook`.

## Variables

ENABLE_RAW_CLI_COMMANDS: true
ENABLE_GEMINI_CLI: true
ENABLE_CODEX_CLI: true
ENABLE_CLAUDE_CODE: true
ENABLE_E2B_SANDBOX: true
AGENTIC_CODING_TOOLS: claude-code, codex-cli, gemini-cli
BACKENDS: local, e2b-sandbox

## Instructions

- Based on the user's request, follow the `Cookbook` to determine which tool to use.

### Auto-Close Feature

The fork_terminal tool supports an optional auto-close feature:
- Add `auto-close` or `--auto-close` to the command (at the beginning or end)
- The terminal window/tab will automatically close after the command completes
- Works with all tools: raw CLI commands, Claude Code, Codex CLI, and Gemini CLI
- **Important**: When auto-close is used with agentic coding tools (Claude Code, Codex CLI, Gemini CLI), the tools will run in non-interactive mode (using `-p` flag) to ensure the command exits after completion. Without auto-close, they run in interactive mode for continued interaction.
- Examples:
  - "fork terminal auto-close: ls -la"
  - "fork terminal --auto-close use gemini to create hello.py"
  - "fork terminal: npm test auto-close"

### Fork Summary User Prompts

- IF: The user requests a fork terminal with a summary. This ONLY works for our agentic coding tools `AGENTIC_CODING_TOOLS`. The tool MUST BE enabled as well.
- THEN: 
  - Read, and REPLACE the `.claude/skills/fork-terminal/prompts/fork_summary_user_prompt.md` with the history of the conversation between you and the user so far. 
  - Include the next users request in the `Next User Request` section.
  - This will be what you pass into the PROMPT parameter of the agentic coding tool.
  - IMPORTANT: To be clear, don't update the file directly, just read it, fill it out IN YOUR MEMORY and use it to craft a new prompt in the structure provided for the new fork agent.
  - Let's be super clear here, the fork_summary_user_prompt.md is a template for you to fill out IN YOUR MEMORY. Once you've filled it out, pass that prompt to the agentic coding tool.
  - XML Tags have been added to let you know exactly what you need to replace. You'll be replacing the <fill in the history here> and <fill in the next user request here> sections.
- EXAMPLES:
  - "fork terminal use claude code to <xyz> summarize work so far"
  - "spin up a new terminal request <xyz> using claude code include summary"
  - "create a new terminal to <xyz> with claude code with summary"

## Workflow

1. Understand the user's request.
2. READ: `.claude/skills/fork-terminal/tools/fork_terminal.py` to understand our tooling.
3. Follow the `Cookbook` to determine which tool to use.
4. Execute the `.claude/skills/fork-terminal/tools/fork_terminal.py: fork_terminal(command: str)` tool.

## Cookbook

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
- NOTES:
  - Requires E2B_API_KEY credential
  - Executes in isolated cloud VM
  - More secure than local execution
  - Use for experimental or untrusted code
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
