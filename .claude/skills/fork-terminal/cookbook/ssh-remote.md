# SSH Remote Execution Cookbook

## Overview

Execute commands and AI agents on remote SSH-accessible machines like NVIDIA DGX workstations. Supports GPU detection, Samba-based file sharing, and secure API key injection.

## Triggers

User requests remote execution with keywords:
- `on <hostname>` (e.g., "on dgx")
- `ssh to <hostname>` (e.g., "ssh to dgx")
- `remote:<hostname>` (e.g., "remote:dgx")
- `@<hostname>` at start (e.g., "@dgx nvidia-smi")

## Supported Agents

- Claude Code
- Gemini CLI
- Codex CLI
- Raw CLI commands

## Prerequisites

### 1. Install Dependencies

```bash
pip install paramiko pyyaml
```

### 2. Configure SSH Host

Create or edit `~/.config/fork-terminal/ssh_hosts.yaml`:

```yaml
hosts:
  dgx:
    hostname: 192.168.1.100
    port: 22
    user: nvidia
    key_path: ~/.ssh/dgx_key
    gpu_enabled: true
    cuda_path: /usr/local/cuda
    samba_share:
      local_mount: /Volumes/DGX-Share
      remote_path: /mnt/shared
    environment:
      CUDA_VISIBLE_DEVICES: "0,1,2,3"
```

### 3. SSH Key Setup

SSH uses key-based authentication only (no passwords for security).

```bash
# Generate a key if needed
ssh-keygen -t ed25519 -f ~/.ssh/dgx_key

# Copy to remote host
ssh-copy-id -i ~/.ssh/dgx_key nvidia@192.168.1.100

# Add to known_hosts
ssh-keyscan -H 192.168.1.100 >> ~/.ssh/known_hosts
```

### 4. Agent Credentials

API keys for AI agents are required (resolved via the credential waterfall):
- ANTHROPIC_API_KEY (Claude)
- GEMINI_API_KEY (Gemini)
- OPENAI_API_KEY (Codex)

### 5. AI CLIs on Remote

Ensure AI CLIs are installed on the remote host:
- `claude` - Claude Code CLI
- `gemini` - Gemini CLI
- `codex` - Codex CLI

## Command Structure

```
fork terminal [use <agent>] on <hostname> <command/prompt> [auto-close]
```

**Components**:
- `<agent>`: claude, gemini, or codex (optional for raw commands)
- `on <hostname>`: Target SSH host from config
- `<command/prompt>`: The command or AI prompt
- `auto-close` (optional): Close connection when done

## Examples

### Raw CLI Commands

```bash
# Check hostname
"fork terminal on dgx: hostname"

# Check GPU status
"fork terminal on dgx: nvidia-smi"

# Run Python script
"fork terminal on dgx: python train.py"

# Using @hostname syntax
"@dgx nvidia-smi --query-gpu=utilization.gpu --format=csv"
```

### Claude on DGX

```bash
# Ask Claude to analyze code
"fork terminal use claude on dgx to review the training script"

# With auto-close
"fork terminal use claude on dgx to explain CUDA errors auto-close"

# Code generation
"fork terminal use claude on dgx to write a PyTorch data loader"
```

### Gemini on DGX

```bash
# Generate code
"fork terminal use gemini on dgx to write a distributed training script"

# Analyze data
"fork terminal use gemini on dgx to analyze the model performance logs"
```

### Codex on DGX

```bash
# Full-auto mode
"fork terminal use codex on dgx to refactor the model architecture"

# Bug fixing
"fork terminal use codex on dgx to fix the memory leak in data loading"
```

## Workflow

When user requests SSH execution:

1. **Parse Command**: Detect SSH keywords and host name
2. **Load Host Config**: Read from `~/.config/fork-terminal/ssh_hosts.yaml`
3. **Resolve SSH Key**: Waterfall resolution
   - Explicit key_path
   - Host config key_path
   - SSH_DEFAULT_KEY_PATH env var
   - ~/.ssh/id_ed25519
   - ~/.ssh/id_rsa
4. **Connect**: Establish SSH connection (pooled for performance)
5. **Detect GPUs**: Query nvidia-smi if gpu_enabled
6. **Resolve Credentials**: Get agent API key if using an agent
7. **Execute**: Run command with environment variables
8. **Return Results**: Display output and GPU info
9. **Cleanup**: Close connection if auto-close

## File Transfer

### Samba Share (Primary Method)

When configured, files are shared via a mounted Samba share:

```yaml
samba_share:
  local_mount: /Volumes/DGX-Share     # Mac mount point
  remote_path: /mnt/shared            # Linux path on DGX
```

Files placed in the shared directory are immediately available on both sides without explicit upload/download steps.

### SFTP (Fallback)

If Samba is not configured or unavailable, SFTP is used automatically for file transfers.

## GPU Features

### Auto-Detection

When `gpu_enabled: true`, the backend queries `nvidia-smi` and displays:
- GPU name and model
- Memory usage (used/total)
- GPU utilization percentage

### CUDA Environment

When `cuda_path` is configured:
- Adds CUDA bin to PATH
- Adds CUDA lib64 to LD_LIBRARY_PATH
- Sets CUDA_VISIBLE_DEVICES from environment config

## Security

### Key-Based Auth Only

SSH connections require key-based authentication. Password authentication is not supported for security reasons.

### API Key Injection

Agent API keys are:
- Resolved locally from your credential sources
- Injected at runtime via environment variables
- Never stored on the remote host
- Only available for the duration of the command

### Host Key Verification

SSH connections verify host keys against `~/.ssh/known_hosts`. Unknown hosts are rejected to prevent MITM attacks.

### Path Traversal Prevention

File paths are validated to prevent directory traversal attacks (no `..` in paths).

## Error Handling

### Host Not Configured

```
SSH host 'dgx' not configured.
Add it to: ~/.config/fork-terminal/ssh_hosts.yaml
```

**Solution**: Create the config file with host details.

### SSH Key Not Found

```
SSH private key not found.
Checked locations:
  1. Explicit key_path: not provided
  2. Host config key_path: ~/.ssh/dgx_key
  ...
```

**Solution**: Generate and configure an SSH key.

### Connection Failed

```
SSH connection failed: Authentication failed
```

**Solutions**:
- Verify SSH key is in authorized_keys on remote
- Check host is in known_hosts
- Verify username and port are correct

### Agent Credential Missing

```
Credential not found for claude (ANTHROPIC_API_KEY).
```

**Solution**: Set the API key in environment, keychain, or .env file.

## Configuration Reference

### Full Host Config

```yaml
hosts:
  dgx:
    # Required
    hostname: 192.168.1.100       # IP or hostname

    # Optional (with defaults)
    port: 22                       # SSH port
    user: root                     # SSH username
    key_path: ~/.ssh/id_ed25519    # SSH private key

    # GPU settings
    gpu_enabled: true              # Enable GPU detection
    cuda_path: /usr/local/cuda     # CUDA installation path

    # File sharing
    samba_share:
      local_mount: /Volumes/DGX-Share
      remote_path: /mnt/shared

    # Environment variables
    environment:
      CUDA_VISIBLE_DEVICES: "0,1,2,3"
      PATH: "/opt/tools/bin:$PATH"
```

### Multiple Hosts

```yaml
hosts:
  dgx:
    hostname: 192.168.1.100
    user: nvidia
    gpu_enabled: true

  workstation:
    hostname: workstation.local
    user: developer
    gpu_enabled: false

  cloud-gpu:
    hostname: gpu.example.com
    port: 2222
    user: ubuntu
    key_path: ~/.ssh/cloud_key
    gpu_enabled: true
```

## Comparison: Local vs E2B vs SSH

| Aspect | Local | E2B Sandbox | SSH Remote |
|--------|-------|-------------|------------|
| **Speed** | Instant | Network latency | Network latency |
| **Cost** | Free | E2B costs | Free (your hardware) |
| **Security** | Full system | Isolated VM | Full remote access |
| **GPU Access** | Local GPUs | No GPUs | Remote GPUs |
| **Use Case** | Dev tasks | Experimental | Heavy compute |

## Debugging

### Test Connection

```bash
# Test SSH connection directly
ssh -i ~/.ssh/dgx_key nvidia@192.168.1.100 hostname

# Test via fork terminal
"fork terminal on dgx: whoami"
```

### Check GPU Access

```bash
# Basic GPU info
"fork terminal on dgx: nvidia-smi"

# Detailed query
"fork terminal on dgx: nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv"
```

### Verbose Output

The SSH backend prints detailed status:
- Connection status
- GPU detection results
- Command execution
- Exit codes and output

## Notes

- SSH connections are pooled for performance (reused within a session)
- Timeouts: Connection 30s, Command execution 300s
- API keys are exported as environment variables, never written to files
- Auto-close is recommended for non-interactive commands
