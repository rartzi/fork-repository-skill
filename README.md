# Fork Terminal Skill
> A simple skill you can use to fork your agentic coding tools to different execution environments—either a new local terminal window or an isolated cloud sandbox.
>
> Why? To offload context (delegate), to branch work, to parallelize work, to run experimental code securely, to run the same command against different tools + models, and more.
>
> Check out this [YouTube video](https://youtu.be/X2ciJedw2vU) where we build this skill from scratch.

<img src="images/fork-terminal.png" alt="Fork Terminal Skill" width="800">

A [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skill that enables AI agents to spawn new execution environments on demand. This skill extends Claude Code's capabilities to launch additional sessions—including other AI coding assistants like Claude Code, Codex CLI, and Gemini CLI—in either local terminal windows or isolated E2B cloud sandboxes.

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

The fork terminal skill supports an **auto-close** feature that executes commands in the background and captures their output. This is useful for quick tasks where you don't need to keep a terminal window open.

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

### Behavior

| Mode | Behavior |
|------|----------|
| **With auto-close** | Command runs directly in background, output is captured and returned immediately. No terminal window is opened. |
| **Without auto-close** | Opens a new terminal window/tab that remains open for interactive use. |

### Interactive Mode Handling

When auto-close is used with agentic coding tools (Claude Code, Codex CLI, Gemini CLI):
- **With auto-close**: Tools run in **non-interactive mode** to ensure the command exits after completion and output is captured
- **Without auto-close**: Tools run in **interactive mode** in a new terminal window for continued interaction

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

### E2B Template: Real CLIs Pre-Installed

The E2B sandbox uses a **custom template** with all AI agent CLIs pre-installed and ready to use!

**Template Details**:
- **Template ID**: `whhe4zpvcrwa0ahyu559`
- **Template Name**: `fork-terminal-ai-agents`
- **Size**: ~723 MB
- **Build Date**: 2026-01-05
- **Status**: ✅ Production Ready

**Pre-Installed CLIs**:
- ✅ **Claude Code CLI** v2.0.76 at `/usr/bin/claude`
- ✅ **Gemini CLI** v0.22.5 at `/usr/bin/gemini`
- ✅ **Codex CLI** v0.77.0 at `/usr/bin/codex`
- ✅ **Node.js** v20.19.6 (required for CLIs)
- ✅ **Python 3.10** + pip

**Hybrid Execution**:
1. **Real CLI execution** (default): Uses the pre-installed CLIs for authentic behavior
2. **Python API fallback**: Automatically falls back to Python APIs if CLI execution fails
3. **Transparent switching**: You don't need to worry about which is used

**Benefits**:
- ✅ **No runtime installation** - CLIs are ready instantly
- ✅ **Faster startup** - No npm install delays
- ✅ **Authentic CLI experience** - Same behavior as local execution
- ✅ **Reliable fallback** - Python APIs ensure execution always works
- ✅ **Zero configuration** - Works out of the box

**Template Architecture**:
- **Single unified template** serves both AI agents and raw CLI commands
- AI agents (Claude/Gemini/Codex) use the installed CLIs
- Raw commands (python, curl, git) use standard Linux tools
- Future: Separate lightweight base template planned for raw CLI only (when needed)

### Automatic File Upload

Sandboxes are isolated from your local filesystem, but **local files are automatically uploaded** when referenced in prompts!

**How It Works**:
- The system detects file references in your prompt (e.g., "my config.yaml", "SKILL.md", "data.csv")
- Files are automatically uploaded to `/home/user/` in the sandbox
- File contents are injected into the agent's prompt for analysis
- Works transparently - just reference files naturally!

**Supported File Types**:
- Common extensions: `.md`, `.py`, `.js`, `.ts`, `.json`, `.yaml`, `.txt`, `.csv`, `.html`, `.css`, `.sh`, etc.
- Uppercase files: `SKILL.MD`, `README.MD`
- Natural language: "my config.yaml", "the data.csv"

**File Upload Examples**:
```bash
# Analyze a local file in sandbox
"fork terminal use gemini in sandbox to analyze my config.yaml"

# Review local code safely
"fork terminal use claude in sandbox to review my script.py"

# Process local data
"fork terminal use codex in sandbox to summarize data.csv"

# Multi-file analysis
"fork terminal use gemini in sandbox to compare settings.json with defaults.json"
```

### Automatic File Download

Agents running in sandboxes can create files, and **those files are automatically downloaded** back to your local machine!

**How It Works**:
- Agents write output files to `/home/user/output/` in the sandbox
- After execution, files are automatically downloaded to `./sandbox-output/` locally
- Directory structure is preserved
- Works for any file type: reports, code, images, data, etc.

**Output Directory Convention**:
When prompting agents, instruct them to save files to `/home/user/output/`:

```bash
# Generate a report that gets downloaded automatically
"fork terminal use gemini in sandbox to analyze data.csv and save report to /home/user/output/analysis.md"

# Create code that's downloaded locally
"fork terminal use claude in sandbox to implement the feature and save to /home/user/output/feature.py"

# Generate multiple files
"fork terminal use codex in sandbox to create tests and save to /home/user/output/test_*.py"
```

**What Gets Downloaded**:
- ✅ Reports (`.md`, `.txt`, `.pdf`)
- ✅ Code files (`.py`, `.js`, `.ts`, etc.)
- ✅ Data files (`.json`, `.csv`, `.yaml`)
- ✅ Images (`.png`, `.jpg`, `.svg`)
- ✅ Any file in `/home/user/output/` directory

**Where Files Are Saved Locally**:
```
./sandbox-output/          # Default local directory
├── analysis.md           # Downloaded files
├── feature.py
└── tests/
    ├── test_auth.py
    └── test_api.py
```

**File Download Examples**:
```bash
# Generate and download a report
"fork terminal use gemini in sandbox to create a project summary and save to /home/user/output/summary.md"

# Create and download code
"fork terminal use claude in sandbox to implement the calculator class and save to /home/user/output/calculator.py"

# Process data and download results
"fork terminal use codex in sandbox to analyze sales.csv and save charts to /home/user/output/charts/"

# Generate documentation
"fork terminal use gemini in sandbox to document my API and save to /home/user/output/api-docs.md"
```

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
| **Filesystem** | Direct access to all local files | Isolated (auto-upload/download) |
| **Credentials** | All local credentials | Only injected credential |
| **File Upload** | N/A (direct access) | Automatic when files referenced |
| **File Download** | N/A (writes directly) | Automatic from `/home/user/output/` |
| **Output Location** | Current directory | `./sandbox-output/` locally |
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
│   ├── gemini-cli.md           # Gemini CLI instructions
│   └── e2b-sandbox.md          # E2B sandbox execution instructions
├── prompts/
│   └── fork_summary_user_prompt.md  # Template for context handoff
└── tools/
    ├── fork_terminal.py        # Main execution router (local/sandbox)
    ├── sandbox_backend.py      # E2B sandbox integration
    ├── credential_resolver.py  # API key management (env/keychain/.env)
    ├── e2b-template/           # E2B template with real CLIs (Claude/Gemini/Codex)
    ├── e2b-template-base/      # Lightweight base template (planned)
    └── .e2b_template_id        # Current template ID
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
