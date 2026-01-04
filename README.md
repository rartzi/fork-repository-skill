# Fork Terminal Skill
> A simple skill you can use to fork your agentic coding tools to a new terminal window.
>
> Why? To offload context (delegate), to branch work, to parallelize work, to run the same command against different tools + models, and more.
>
> Check out this [YouTube video](https://youtu.be/X2ciJedw2vU) where we build this skill from scratch.

<img src="images/fork-terminal.png" alt="Fork Terminal Skill" width="800">

A [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skill that enables AI agents to spawn new terminal windows on demand. This skill extends Claude Code's capabilities to launch additional terminal sessions—including other AI coding assistants like Claude Code, Codex CLI, and Gemini CLI—in parallel terminals.

## Requirements

**Core**:
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code)
- [Gemini CLI](https://github.com/google-gemini/gemini-cli)
- [Codex CLI](https://github.com/openai/codex)

**Optional (for E2B Sandbox)**:
- [E2B Account](https://e2b.dev/) - For isolated sandbox execution
- Python dependencies: `pip install -r requirements.txt`

## What is a Claude Code Skill?

Claude Code skills are **modular, context-aware capabilities** that extend what Claude can do. Unlike slash commands (which require explicit `/command` invocation), skills are **automatically discovered and invoked** by Claude when user requests match the skill's description.

Skills live in `.claude/skills/` directories and consist of:
- A `SKILL.md` file defining triggers, instructions, and workflow
- Supporting files (scripts, templates, documentation)

When you say something like "fork terminal to run tests with Claude Code", Claude automatically detects the matching skill, reads the instructions, and executes the workflow.

## Purpose

This skill allows you to:
- **Spawn parallel AI agents** in separate terminal windows OR isolated E2B sandboxes
- **Run raw CLI commands** in new terminals
- **Pass conversation context** to forked agents (summary mode)
- **Execute agents securely** in cloud sandboxes (new!)

This is useful when you want Claude to delegate work to another agent running independently, execute experimental code safely, or run long-running commands in a separate environment.

## Execution Backends

| Backend | Description | Use Case |
|---------|-------------|----------|
| **Local Terminal** | Spawns new terminal window on your machine | Fast, trusted tasks |
| **E2B Sandbox** | Executes in isolated cloud VM | Secure, experimental, untrusted code |

Add `in sandbox` to any command to use E2B backend:
```bash
"fork terminal use gemini in sandbox to test risky code"
```

## Supported Tools

| Tool            | Trigger Examples                      | Default Model          | Sandbox Support |
| --------------- | ------------------------------------- | ---------------------- | --------------- |
| **Claude Code** | "fork terminal use claude code to..." | `opus`                 | ✅ Yes          |
| **Codex CLI**   | "fork terminal use codex to..."       | `gpt-5.1-codex-max`    | ✅ Yes          |
| **Gemini CLI**  | "fork terminal use gemini to..."      | `gemini-3-pro-preview` | ✅ Yes          |
| **Raw CLI**     | "fork terminal run ffmpeg..."         | N/A                    | ❌ Local only   |

### Model Modifiers

Each agentic tool supports model selection:
- **Default**: Uses the tool's default model
- **"fast"**: Uses a lighter, faster model (e.g., `haiku`, `gpt-5.1-codex-mini`, `gemini-2.5-flash`)
- **"heavy"**: Uses the most capable model

## Auto-Close Feature

The fork terminal skill supports an **auto-close** feature that automatically closes the terminal window/tab after the command completes. This is useful for quick tasks where you don't need to keep the terminal open.

### Usage

Add `auto-close` or `--auto-close` anywhere in your command:

```
# At the beginning
"fork terminal auto-close: ls -la"

# At the end
"fork terminal: npm test auto-close"

# With a flag
"fork terminal --auto-close use gemini to create hello.py"
```

### Behavior by Platform

| Platform    | Behavior                                                                 |
| ----------- | ------------------------------------------------------------------------ |
| **macOS**   | Creates terminal tab, waits for command completion, closes entire window |
| **Windows** | Uses `/c` flag to close window after command completion                 |

### Interactive Mode Handling

When auto-close is used with agentic coding tools (Claude Code, Codex CLI, Gemini CLI):
- **With auto-close**: Tools run in **non-interactive mode** (using `-p` flag) so the command exits after completion, allowing the terminal to close automatically
- **Without auto-close**: Tools run in **interactive mode** (default) to keep the session open for continued interaction

### Examples

```
# Quick directory listing
"fork terminal auto-close: ls -la"

# Run tests and close
"fork terminal auto-close: npm test"

# Generate a file with Gemini and close
"fork terminal auto-close use gemini to create hello.py"

# Run build with Claude Code and close
"fork terminal --auto-close use claude code to run the build"
```

## E2B Sandbox Execution (New!)

Execute AI agents in isolated E2B cloud sandboxes for secure, scalable deployment.

### Why Use Sandboxes?

**Security Benefits**:
- Complete isolation from your local system
- No access to your local filesystem, credentials, or network
- Safe execution of experimental or untrusted code
- Limited blast radius if agent misbehaves

**Use Cases**:
- Testing risky or experimental code
- Running untrusted agent-generated code
- Parallel agent experiments without conflicts
- Production agent deployment with isolation guarantees

### Setup

1. **Get E2B API Key**:
   - Sign up at [e2b.dev](https://e2b.dev/)
   - Copy your API key

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Credentials**:

   Copy `.env.sample` to `.env` and fill in your keys:
   ```bash
   cp .env.sample .env
   ```

   Or use the credential waterfall (checked in order):
   - Environment variables (highest priority)
   - System keychain
   - .env file
   - Config files (~/.config/<tool>/credentials.json)

### Sandbox Examples

**Basic Sandbox Execution**:
```bash
"fork terminal use gemini in sandbox to create hello world in Python"
```

**With Auto-Close**:
```bash
"fork terminal use claude in sandbox to analyze this code auto-close"
```

**Experimental Code**:
```bash
"fork terminal use codex in sandbox to test this risky refactor"
```

**Parallel Sandbox Experiments**:
```bash
# Race all three agents on the same task, each in isolated sandbox
"fork terminal use claude in sandbox to optimize algorithm auto-close"
"fork terminal use gemini in sandbox to optimize algorithm auto-close"
"fork terminal use codex in sandbox to optimize algorithm auto-close"
```

### Credential Security

The sandbox backend uses **waterfall credential resolution**:

1. **Environment Variable** (highest priority):
   ```bash
   export GEMINI_API_KEY="your-key"
   ```

2. **System Keychain** (recommended for security):
   ```bash
   # macOS
   security add-generic-password -s GEMINI_API_KEY -a $USER -w "your-key"
   ```

3. **.env File** (project-specific):
   ```bash
   # .env (gitignored)
   E2B_API_KEY=your_e2b_key
   GEMINI_API_KEY=your_gemini_key
   ANTHROPIC_API_KEY=your_anthropic_key
   OPENAI_API_KEY=your_openai_key
   ```

4. **Config Files** (tool-native location):
   ```bash
   ~/.config/gemini/credentials.json
   ```

**Security Notes**:
- Only the specific agent credential is injected into the sandbox
- No AWS keys, GitHub tokens, or SSH keys are accessible
- Sandboxes are destroyed after execution (with auto-close)
- Environment variables allow testing with separate keys

### Local vs Sandbox Comparison

| Aspect | Local Terminal | E2B Sandbox |
|--------|----------------|-------------|
| **Speed** | Instant | Network latency (~2-5s) |
| **Cost** | Free | E2B service costs |
| **Security** | Full system access | Isolated VM |
| **Filesystem** | Your local files | Isolated sandbox |
| **Credentials** | All local credentials | Only injected credential |
| **Use Case** | Trusted, fast tasks | Experimental, risky tasks |

## Usage Examples

### Examples you can run NOW

These examples work against this codebase. Generated files go to `temp/`.

**Claude Code**
```
# Analyze the skill architecture and save a report
"fork terminal use claude code to analyze SKILL.md and write a summary to temp/skill-analysis.md"

# Add Linux support to fork_terminal.py
"fork terminal use claude code to add Linux support to tools/fork_terminal.py, save changes to temp/fork_terminal_linux.py"

# Generate documentation for the Python tool
"fork terminal use claude code fast to read tools/fork_terminal.py and generate docstrings, save to temp/fork_terminal_documented.py"
```

**Codex CLI**
```
# Review the cookbook structure
"fork terminal use codex to review cookbook/*.md and write suggestions to temp/codex-cookbook-review.md"

# Generate a test file for the fork tool
"fork terminal use codex to read tools/fork_terminal.py and generate pytest tests, save to temp/test_fork_terminal.py"

# Analyze the SKILL.md workflow
"fork terminal use codex fast to analyze SKILL.md and explain the workflow in temp/workflow-explained.md"
```

**Gemini CLI**
```
# Document the skill's purpose
"fork terminal use gemini to read README.md and SKILL.md, write a one-pager summary to temp/gemini-summary.md"

# Suggest new cookbook entries
"fork terminal use gemini to review cookbook/ and suggest a new tool integration, save to temp/new-cookbook-idea.md"

# Analyze cross-platform support
"fork terminal use gemini fast to analyze tools/fork_terminal.py and recommend Linux implementation, save to temp/linux-recommendations.md"
```

**Raw CLI**
```
# List all skill files
"new terminal: find .claude/skills -name '*.md' | head -20"

# Watch for file changes
"fork terminal: watch -n 2 'ls -la .claude/skills/fork-terminal/'"
```

**Multi-Agent Combinations**
```
# Fork all three agents to review different aspects of the codebase
"fork terminal use claude code to review tools/fork_terminal.py and save analysis to temp/claude-tool-review.md,
 then fork terminal use codex to review SKILL.md and save analysis to temp/codex-skill-review.md,
 then fork terminal use gemini to review cookbook/*.md and save analysis to temp/gemini-cookbook-review.md"

# Race all three agents on the same task
"fork three terminals: claude code, codex, and gemini - each should read README.md and write improvement suggestions to temp/<agent>-readme-suggestions.md"

# Parallel documentation generation
"fork terminal use claude code to document tools/fork_terminal.py to temp/claude-docs.md,
 fork terminal use codex to document SKILL.md to temp/codex-docs.md,
 fork terminal use gemini to document the cookbook/ files to temp/gemini-docs.md"
```

**With Conversation Summary (Context Handoff)**
```
# Hand off your current conversation context to a new Claude Code agent
"fork terminal use claude code to request a new plan in temp/specs/<relevant-name>.md that details a net new cookbook file for a new agentic coding tool, summarize work so far"

# Delegate a subtask with full context to Gemini
"fork terminal use gemini to implement temp/specs/add-linux-support.md that details how to add Linux support to the fork terminal skill, include summary"
```

### Examples you can run later

These examples demonstrate usage patterns for other projects.

```
# Launch Claude Code for a refactor task
"fork terminal use claude code to refactor the auth module"

# Use a faster model for quick fixes
"fork terminal use claude code fast to fix the typo in utils.py"

# Launch Gemini CLI for test generation
"fork terminal use gemini to write tests for the API"

# Run a dev server in a new terminal
"create a new terminal to run npm run dev"

# Hand off context to a new agent
"fork terminal use claude code to implement the feature we discussed, summarize work so far"
```

## How It Works

1. **Trigger Detection**: Claude detects phrases like "fork terminal", "new terminal", or "fork session"
2. **Cookbook Selection**: Based on the requested tool, Claude reads the appropriate cookbook (e.g., `claude-code.md`)
3. **Command Construction**: Claude builds the command with proper flags (interactive mode, model selection, permission bypasses)
4. **Terminal Spawn**: The `fork_terminal.py` script opens a new terminal window and executes the command

## Architecture

```
.claude/skills/fork-terminal/
├── SKILL.md                    # Skill definition and workflow
├── cookbook/
│   ├── cli-command.md          # Raw CLI instructions
│   ├── claude-code.md          # Claude Code agent instructions
│   ├── codex-cli.md            # Codex CLI instructions
│   └── gemini-cli.md           # Gemini CLI instructions
├── prompts/
│   └── fork_summary_user_prompt.md  # Template for context handoff
└── tools/
    └── fork_terminal.py        # Cross-platform terminal spawner
```

## Platform Support

| Platform    | Status              | Method                     |
| ----------- | ------------------- | -------------------------- |
| **macOS**   | Supported           | AppleScript → Terminal.app |
| **Windows** | Supported           | `cmd /k` via `start`       |
| **Linux**   | Not yet implemented | —                          |

## Installation

Copy the `.claude/skills/fork-terminal/` directory to your project's `.claude/skills/` folder, or to `~/.claude/skills/` for personal use across all projects.

## Improvements

Ideas for future enhancements:

- **Focus spawned windows** - Bring new terminal windows to front automatically, or keep them in background based on user preference
- **More agentic coding tools** - Add cookbooks for OpenCode, and other agentic coding tools.
- **Whatever else you can think of** - Feel free to fork the terminal fork skill and make it your own.

## Master **Agentic Coding**
> Prepare for the future of software engineering

Learn tactical agentic coding patterns with [Tactical Agentic Coding](https://agenticengineer.com/tactical-agentic-coding?y=frktskl)

Follow the [IndyDevDan YouTube channel](https://www.youtube.com/@indydevdan) to improve your agentic coding advantage.
