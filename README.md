# Fork Terminal Skill
> A simple skill you can use to fork your agentic coding tools to different execution environments—local terminal windows, isolated cloud sandboxes, Docker containers, or remote SSH-accessible machines like NVIDIA DGX workstations.
>
> Why? To offload context (delegate), to branch work, to parallelize work, to run experimental code securely, to leverage remote GPU resources, to run the same command against different tools + models, and more.
>
> Inspired by [IndyDevDan's original video](https://youtu.be/X2ciJedw2vU), we forked and extended this skill with E2B sandbox execution, Docker container execution, SSH remote execution, auto-close with output capture, and multi-CLI support.

<img src="images/fork-terminal.png" alt="Fork Terminal Skill" width="800">

A [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skill that enables AI agents to spawn new execution environments on demand. This skill extends Claude Code's capabilities to launch additional sessions—including other AI coding assistants like Claude Code, Codex CLI, and Gemini CLI—in local terminal windows, isolated E2B cloud sandboxes, Docker containers, or remote SSH machines.

## Requirements

**Core**:
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code)
- [Gemini CLI](https://github.com/google-gemini/gemini-cli)
- [Codex CLI](https://github.com/openai/codex)

**Optional (for E2B Sandbox)**:
- [E2B Account](https://e2b.dev/) - For isolated sandbox execution
- Python dependencies: `pip install -r requirements.txt`

**Optional (for Docker)**:
- [Docker](https://www.docker.com/) - Docker daemon running locally
- Image auto-builds on first use (no manual setup)

**Optional (for SSH Remote Execution)**:
- SSH access to remote machine (key-based authentication)
- Python dependencies: `pip install paramiko pyyaml`

## What is a Claude Code Skill?

Claude Code skills are **modular, context-aware capabilities** that extend what Claude can do. Unlike slash commands (which require explicit `/command` invocation), skills are **automatically discovered and invoked** by Claude when user requests match the skill's description.

Skills live in `.claude/skills/` directories and consist of:
- A `SKILL.md` file defining triggers, instructions, and workflow
- Supporting files (scripts, templates, documentation)

When you say something like "fork terminal to run tests with Claude Code", Claude automatically detects the matching skill, reads the instructions, and executes the workflow.

## Purpose

This skill allows you to:
- **Spawn parallel AI agents** in separate terminal windows, E2B sandboxes, or Docker containers
- **Run raw CLI commands** in new terminals or isolated containers
- **Pass conversation context** to forked agents (summary mode)
- **Execute agents securely** in cloud sandboxes or Docker containers
- **Leverage remote GPU resources** via SSH

This is useful when you want Claude to delegate work to another agent running independently, execute experimental code safely, or run long-running commands in a separate environment.

## Execution Backends

| Backend | Description | Use Case |
|---------|-------------|----------|
| **Local Terminal** | Spawns new terminal window on your machine | Fast, trusted tasks |
| **E2B Sandbox** | Executes in isolated cloud VM | Secure, experimental, untrusted code |
| **Docker** | Executes in isolated local container | Free, offline, reproducible environments |
| **SSH Remote** | Executes on remote SSH-accessible machines | GPU workloads, heavy compute, DGX |

Add `in sandbox` to any command to use E2B backend:
```bash
"fork terminal use gemini in sandbox to test risky code"
```

Add `in docker` to execute in a Docker container:
```bash
"fork terminal use claude in docker to analyze this codebase"
```

Add `on <hostname>` to execute on a configured SSH host:
```bash
"fork terminal use claude on dgx to train the model"
```

## Supported Tools

| Tool            | Trigger Examples                      | Default Model          | Sandbox | Docker | SSH |
| --------------- | ------------------------------------- | ---------------------- | ------- | ------ | --- |
| **Claude Code** | "fork terminal use claude code to..." | `opus`                 | Yes     | Yes    | Yes |
| **Codex CLI**   | "fork terminal use codex to..."       | `gpt-5.1-codex-max`    | Yes     | Yes    | Yes |
| **Gemini CLI**  | "fork terminal use gemini to..."      | `gemini-3-pro-preview` | Yes     | Yes    | Yes |
| **Raw CLI**     | "fork terminal run ffmpeg..."         | N/A                    | Yes     | Yes    | Yes |

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

## E2B Sandbox Execution

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
   - .env file
   - System keychain (macOS)
   - Config files (~/.config/<tool>/credentials.json)

### E2B Template: Real CLIs Pre-Installed

The E2B sandbox uses a **custom template** with all AI agent CLIs pre-installed and ready to use!

**Template Details**:
- **Template ID**: `whhe4zpvcrwa0ahyu559`
- **Template Name**: `fork-terminal-ai-agents`
- **Size**: ~723 MB
- **Build Date**: 2026-01-05
- **Status**: Production Ready

**Pre-Installed CLIs**:
- **Claude Code CLI** v2.0.76 at `/usr/bin/claude`
- **Gemini CLI** v0.22.5 at `/usr/bin/gemini`
- **Codex CLI** v0.77.0 at `/usr/bin/codex`
- **Node.js** v20.19.6 (required for CLIs)
- **Python 3.10** + pip

**Hybrid Execution**:
1. **Real CLI execution** (default): Uses the pre-installed CLIs for authentic behavior
2. **Python API fallback**: Automatically falls back to Python APIs if CLI execution fails
3. **Transparent switching**: You don't need to worry about which is used

**Template Architecture**:
- **Single unified template** serves both AI agents and raw CLI commands
- AI agents (Claude/Gemini/Codex) use the installed CLIs
- Raw commands (python, curl, git) use standard Linux tools

### Automatic File Upload

Sandboxes are isolated from your local filesystem, but **local files are automatically uploaded** when referenced in prompts!

**How It Works**:
- The system detects file references in your prompt (e.g., "my config.yaml", "SKILL.md", "data.csv")
- Files are automatically uploaded to `/home/user/` in the sandbox
- File contents are injected into the agent's prompt for analysis
- Works transparently - just reference files naturally!

**File Upload Examples**:
```bash
# Analyze a local file in sandbox
"fork terminal use gemini in sandbox to analyze my config.yaml"

# Review local code safely
"fork terminal use claude in sandbox to review my script.py"
```

### Automatic File Download

Agents running in sandboxes can create files, and **those files are automatically downloaded** back to your local machine!

**How It Works**:
- Agents write output files to `/home/user/output/` in the sandbox
- After execution, files are automatically downloaded to `./sandbox-output/` locally
- Directory structure is preserved

### Sandbox Examples

```bash
# Basic sandbox execution
"fork terminal use gemini in sandbox to create hello world in Python"

# With auto-close
"fork terminal use claude in sandbox to analyze this code auto-close"

# Race all three agents
"fork terminal use claude in sandbox to optimize algorithm auto-close"
"fork terminal use gemini in sandbox to optimize algorithm auto-close"
"fork terminal use codex in sandbox to optimize algorithm auto-close"
```

### Credential Security

All backends use **waterfall credential resolution**:

1. **Environment Variable** (highest priority):
   ```bash
   export GEMINI_API_KEY="your-key"
   ```

2. **.env File** (project-specific):
   ```bash
   # .env (gitignored)
   E2B_API_KEY=your_e2b_key
   GEMINI_API_KEY=your_gemini_key
   ANTHROPIC_API_KEY=your_anthropic_key
   OPENAI_API_KEY=your_openai_key
   ```

3. **System Keychain** (macOS):
   ```bash
   security add-generic-password -s GEMINI_API_KEY -a $USER -w "your-key"
   ```

4. **Config Files** (tool-native location):
   ```bash
   ~/.config/gemini/credentials.json
   ```

**Security Notes**:
- Only the specific agent credential is injected into each backend
- No AWS keys, GitHub tokens, or SSH keys are accessible
- Sandboxes and containers are destroyed after execution (with auto-close)

## Docker Execution

Execute AI agents and commands in isolated Docker containers on your local machine. Free, offline, and reproducible.

### Why Use Docker?

**Benefits**:
- **Free** - No cloud costs, runs on local Docker daemon
- **Offline** - Works without internet (once image is built)
- **Isolated** - Container-level isolation from host system
- **Reproducible** - Dockerfile defines exact dependencies
- **CI/CD Ready** - Same container runs locally and in pipelines

**Use Cases**:
- Running untrusted code with local isolation
- Reproducible development environments
- Offline isolated execution
- Local GPU workloads with `--gpus all`

### Docker Setup

1. **Install Docker**: [docker.com](https://www.docker.com/)

2. **Start Docker Daemon**: Ensure Docker Desktop or daemon is running
   ```bash
   docker info  # Verify Docker is running
   ```

3. **No other setup needed!** The Docker image auto-builds on first use from `Dockerfile.agents`

### Docker Image

The Docker image (`fork-terminal-agents`) is auto-built on first use with:
- **Claude Code CLI** (latest)
- **Gemini CLI** (latest)
- **Codex CLI** (latest)
- **Node.js** v20 (required for CLIs)
- **Python 3.11** + pip + git

The image runs as a non-root `agent` user for security (required by Claude Code).

### Docker Trigger Keywords

- `in docker` - "fork terminal use claude in docker to analyze code"
- `use docker` - "fork terminal use docker to run tests"
- `with docker` - "fork terminal with docker: python script.py"
- `docker:` - "fork terminal docker: npm test"

### Docker Examples

**AI Agents in Docker**:
```bash
# Claude in Docker
"fork terminal use claude in docker to analyze this codebase"

# Gemini in Docker with auto-close
"fork terminal use gemini in docker to write tests auto-close"

# Codex in Docker
"fork terminal use codex in docker to refactor the auth module"
```

**Raw CLI in Docker**:
```bash
# Run Python in isolation
"fork terminal in docker: python script.py"

# Run tests in container
"fork terminal docker: npm test auto-close"

# List workspace files
"fork terminal in docker: ls -la /workspace auto-close"
```

### How Docker Execution Works

1. **Detect backend** - `in docker` / `docker:` keywords trigger Docker backend
2. **Check Docker** - Verify Docker daemon is running
3. **Build image** - Auto-build `fork-terminal-agents` if not found locally
4. **Resolve credentials** - Get API key from env/`.env`/Keychain waterfall
5. **Run container** - Mount working directory as `/workspace`, inject credentials via `-e`
6. **Return results** - Display output
7. **Cleanup** - Remove container with `--rm` (auto-close)

### Docker Security

- **Non-root execution** - Container runs as `agent` user, not root
- **Credential injection** - API keys passed via `-e` flags, never baked into image
- **Volume mount** - Only working directory mounted as `/workspace`
- **No SSH keys** - SSH keys are not exposed to containers
- **Auto cleanup** - Containers removed after execution with `--rm`

## SSH Remote Execution (DGX/GPU Workstations)

Execute commands and AI agents on remote SSH-accessible machines like NVIDIA DGX workstations. Supports GPU detection, file sharing via Samba, and secure API key injection.

### Why Use SSH Remote?

**Benefits**:
- Access powerful GPU resources on remote machines
- Run heavy compute tasks without blocking local machine
- Leverage pre-installed AI CLIs on dedicated workstations
- Secure execution with key-based authentication only

**Use Cases**:
- Training ML models on DGX
- Running GPU-accelerated inference
- Heavy data processing
- Multi-GPU workloads

### SSH Setup

#### 1. Install Dependencies

```bash
pip install paramiko pyyaml
```

#### 2. Configure SSH Access

If you already have SSH config set up (e.g., `~/.ssh/config`), you can use those settings:

```bash
# Test your existing SSH connection
ssh dgx hostname
```

#### 3. Create Fork-Terminal SSH Config

Create `~/.config/fork-terminal/ssh_hosts.yaml`:

```yaml
# SSH Host Configuration for Fork Terminal
hosts:
  dgx:
    hostname: your-dgx-hostname   # Or use hostname from ~/.ssh/config
    port: 22
    user: your-username
    key_path: ~/.ssh/your_key     # Path to SSH private key
    gpu_enabled: true
    cuda_path: /usr/local/cuda
    environment:
      CUDA_VISIBLE_DEVICES: "0,1,2,3,4,5,6,7"
```

#### 4. SSH Key Setup

SSH uses key-based authentication only (no passwords for security):

```bash
# Generate a key if needed
ssh-keygen -t ed25519 -f ~/.ssh/dgx_key

# Copy to remote host
ssh-copy-id -i ~/.ssh/dgx_key user@hostname

# Store passphrase in macOS keychain (optional)
ssh-add --apple-use-keychain ~/.ssh/dgx_key
```

### SSH Trigger Keywords

- `on <hostname>` - "fork terminal on dgx: nvidia-smi"
- `ssh to <hostname>` - "fork terminal ssh to dgx: python train.py"
- `remote:<hostname>` - "fork terminal remote:dgx nvidia-smi"
- `@<hostname>` - "@dgx nvidia-smi"

### SSH Examples

```bash
# Check GPU status
"fork terminal on dgx: nvidia-smi"

# Claude on remote GPU machine
"fork terminal use claude on dgx to analyze GPU memory usage"

# With auto-close
"fork terminal use claude on dgx to check system status auto-close"
```

### SSH Security

- **Key-based auth only** - No passwords for security
- **Host key verification** - Validates against `~/.ssh/known_hosts`
- **API keys injected at runtime** - Never stored on remote
- **Connection pooling** - Reused within session for performance

## Backend Comparison

| Aspect | Local | E2B Sandbox | Docker | SSH Remote |
|--------|-------|-------------|--------|------------|
| **Speed** | Instant | ~2-5s latency | ~1-2s (cached) | Network latency |
| **Cost** | Free | E2B costs | Free | Free (your hardware) |
| **Isolation** | None | Full VM | Container | Full remote |
| **Offline** | Yes | No | Yes | LAN only |
| **GPU Access** | Local GPUs | No GPUs | Local (nvidia-docker) | Remote GPUs |
| **Custom Env** | Your machine | Fixed template | Dockerfile | Pre-configured |
| **Reproducible** | No | Template-based | Yes (Dockerfile) | No |
| **CI/CD Ready** | No | No | Yes | No |
| **Use Case** | Dev tasks | Experimental | Isolated + custom | Heavy compute |

## Usage Examples

### Examples you can run NOW

These examples work against this codebase. Generated files go to `temp/`.

**Claude Code**
```
# Analyze the skill architecture and save a report
"fork terminal use claude code to analyze SKILL.md and write a summary to temp/skill-analysis.md"

# Add Linux support to fork_terminal.py
"fork terminal use claude code to add Linux support to tools/fork_terminal.py, save changes to temp/fork_terminal_linux.py"
```

**Codex CLI**
```
# Review the cookbook structure
"fork terminal use codex to review cookbook/*.md and write suggestions to temp/codex-cookbook-review.md"

# Generate a test file for the fork tool
"fork terminal use codex to read tools/fork_terminal.py and generate pytest tests, save to temp/test_fork_terminal.py"
```

**Gemini CLI**
```
# Document the skill's purpose
"fork terminal use gemini to read README.md and SKILL.md, write a one-pager summary to temp/gemini-summary.md"

# Suggest new cookbook entries
"fork terminal use gemini to review cookbook/ and suggest a new tool integration, save to temp/new-cookbook-idea.md"
```

**Docker Execution**
```
# Run Python in isolated container
"fork terminal in docker: python -c 'print(\"hello from container\")' auto-close"

# Use Claude in Docker
"fork terminal use claude in docker to analyze this codebase auto-close"

# Run tests in Docker
"fork terminal docker: npm test auto-close"
```

**Multi-Agent Combinations**
```
# Race all three agents in Docker
"fork terminal use claude in docker to optimize algorithm auto-close"
"fork terminal use gemini in docker to optimize algorithm auto-close"
"fork terminal use codex in docker to optimize algorithm auto-close"

# Mix backends
"fork terminal use claude in sandbox to analyze code auto-close"
"fork terminal use gemini in docker to write tests auto-close"
"fork terminal use codex on dgx to train model auto-close"
```

**With Conversation Summary (Context Handoff)**
```
# Hand off your current conversation context to a new Claude Code agent
"fork terminal use claude code to request a new plan summarize work so far"

# Delegate a subtask with full context to Gemini
"fork terminal use gemini to implement the feature include summary"
```

## How It Works

1. **Trigger Detection**: Claude detects phrases like "fork terminal", "new terminal", or "fork session"
2. **Backend Selection**: Keywords like "in docker", "in sandbox", "on dgx" route to the appropriate backend
3. **Cookbook Selection**: Based on the requested tool, Claude reads the appropriate cookbook (e.g., `claude-code.md`, `docker.md`)
4. **Command Construction**: Claude builds the command with proper flags (interactive mode, model selection, permission bypasses)
5. **Execution**: The `fork_terminal.py` script routes to the selected backend and executes the command

## Architecture

```
.claude/skills/fork-terminal/
├── SKILL.md                    # Skill definition and workflow
├── cookbook/
│   ├── cli-command.md          # Raw CLI instructions
│   ├── claude-code.md          # Claude Code agent instructions
│   ├── codex-cli.md            # Codex CLI instructions
│   ├── gemini-cli.md           # Gemini CLI instructions
│   ├── e2b-sandbox.md          # E2B sandbox execution instructions
│   ├── docker.md               # Docker container execution instructions
│   └── ssh-remote.md           # SSH remote execution instructions
├── prompts/
│   └── fork_summary_user_prompt.md  # Template for context handoff
└── tools/
    ├── fork_terminal.py        # Main execution router (local/sandbox/docker/ssh)
    ├── sandbox_backend.py      # E2B sandbox integration
    ├── docker_backend.py       # Docker container execution backend
    ├── Dockerfile.agents       # Docker image definition (auto-built)
    ├── ssh_backend.py          # SSH remote execution backend
    ├── ssh_host_config.py      # SSH host configuration manager
    ├── credential_resolver.py  # API key & SSH key management (waterfall)
    ├── e2b-template/           # E2B template with real CLIs (Claude/Gemini/Codex)
    └── .e2b_template_id        # Current template ID

~/.config/fork-terminal/
└── ssh_hosts.yaml              # SSH host configurations
```

## Platform Support

| Platform    | Status              | Method                     |
| ----------- | ------------------- | -------------------------- |
| **macOS**   | Supported           | AppleScript -> Terminal.app |
| **Windows** | Supported           | `cmd /k` via `start`       |
| **Linux**   | Not yet implemented | --                          |

## Installation

Copy the `.claude/skills/fork-terminal/` directory to your project's `.claude/skills/` folder, or to `~/.claude/skills/` for personal use across all projects.

## Improvements

Ideas for future enhancements:

- **Focus spawned windows** - Bring new terminal windows to front automatically, or keep them in background based on user preference
- **More agentic coding tools** - Add cookbooks for OpenCode, and other agentic coding tools
- **Linux local terminal support** - Add support for Linux terminal emulators
- **Docker Compose** - Multi-agent Docker Compose scenarios
- **Per-agent Docker images** - Lightweight images per agent instead of single unified image
- **Whatever else you can think of** - Feel free to fork the terminal fork skill and make it your own
