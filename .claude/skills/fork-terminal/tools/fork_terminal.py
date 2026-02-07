#!/usr/bin/env python3
"""Fork a new terminal window with a command."""

import os
import platform
import subprocess
import sys
from pathlib import Path

# Add tools directory to path for imports
tools_dir = Path(__file__).parent
if str(tools_dir) not in sys.path:
    sys.path.insert(0, str(tools_dir))

# Ensure virtual environment is set up and activated
from env_setup import activate_venv
activate_venv()

# Import credential resolution and backends
try:
    from credential_resolver import CredentialResolver, CredentialNotFoundError
    from sandbox_backend import SandboxBackend
    SANDBOX_AVAILABLE = True
except ImportError:
    SANDBOX_AVAILABLE = False
    CredentialResolver = None
    SandboxBackend = None

# Import SSH backend
try:
    from ssh_backend import SSHBackend
    from ssh_host_config import SSHHostConfigManager
    SSH_AVAILABLE = True
except ImportError:
    SSH_AVAILABLE = False
    SSHBackend = None
    SSHHostConfigManager = None

# Import Docker backend
try:
    from docker_backend import DockerBackend
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False
    DockerBackend = None


def _execute_in_sandbox(agent: str, command: str, auto_close: bool, working_dir: str = None) -> str:
    """
    Execute a command or AI agent in E2B sandbox.

    Args:
        agent: Agent name ("claude", "gemini", "codex") or None for raw commands.
        command: The command/prompt.
        auto_close: Close sandbox after execution.
        working_dir: Working directory for file resolution.

    Returns:
        Execution result string.
    """
    try:
        backend = SandboxBackend(verbose=True)

        # The command is already cleaned by parse_command, so we can use it directly.
        # The agent is also detected, which determines if it's an agentic or raw command execution.
        print(f"\n📦 Executing in E2B sandbox...")
        if agent:
            print(f"👤 Agent: {agent}")
        print(f"💬 Command/Prompt: {command}\n")

        result = backend.execute(
            prompt=command,
            agent=agent,
            auto_close=auto_close,
            working_dir=working_dir
        )

        if result["success"]:
            output_msg = f"✅ Sandbox execution completed\n"
            output_msg += f"Sandbox ID: {result['sandbox_id']}\n"
            if result['output']:
                output_msg += f"\nOutput:\n{result['output']}\n"
            if auto_close:
                output_msg += "\n🔒 Sandbox closed"
            return output_msg
        else:
            error_msg = f"❌ Sandbox execution failed\n"
            if result['error']:
                error_msg += f"Error: {result['error']}\n"
            return error_msg

    except Exception as e:
        return f"❌ Sandbox execution error: {str(e)}"


def _execute_via_ssh(host_name: str, agent: str, command: str, auto_close: bool, working_dir: str = None) -> str:
    """
    Execute a command or AI agent on a remote SSH host.

    Args:
        host_name: Name of configured SSH host (e.g., "dgx").
        agent: Agent name ("claude", "gemini", "codex") or None for raw commands.
        command: The command/prompt.
        auto_close: Close connection after execution.
        working_dir: Working directory for file resolution.

    Returns:
        Execution result string.
    """
    try:
        backend = SSHBackend(verbose=True)

        print(f"\n🔌 Executing on SSH host: {host_name}")
        if agent:
            print(f"👤 Agent: {agent}")
        print(f"💬 Command/Prompt: {command}\n")

        result = backend.execute(
            host_name=host_name,
            prompt=command,
            agent=agent,
            working_dir=working_dir,
            auto_close=auto_close
        )

        if result["success"]:
            output_msg = f"✅ SSH execution completed on {host_name}\n"

            # Show GPU info if available
            if result.get("gpu_info"):
                output_msg += f"\n🎮 GPUs: {len(result['gpu_info'])}\n"
                for gpu in result["gpu_info"]:
                    output_msg += f"  [{gpu.index}] {gpu.name} ({gpu.utilization})\n"

            if result['output']:
                output_msg += f"\nOutput:\n{result['output']}\n"

            if auto_close:
                output_msg += "\n🔒 Connection closed"

            return output_msg
        else:
            error_msg = f"❌ SSH execution failed on {host_name}\n"
            if result['error']:
                error_msg += f"Error: {result['error']}\n"
            return error_msg

    except Exception as e:
        return f"❌ SSH execution error: {str(e)}"


def _execute_in_docker(agent: str, command: str, auto_close: bool, working_dir: str = None, gpu: bool = False) -> str:
    """
    Execute a command or AI agent in a Docker container.

    Args:
        agent: Agent name ("claude", "gemini", "codex") or None for raw commands.
        command: The command/prompt.
        auto_close: Remove container after execution.
        working_dir: Working directory to mount as /workspace.
        gpu: Enable GPU passthrough.

    Returns:
        Execution result string.
    """
    try:
        backend = DockerBackend(verbose=True)

        print(f"\n🐳 Executing in Docker container...")
        if agent:
            print(f"👤 Agent: {agent}")
        print(f"💬 Command/Prompt: {command}\n")

        result = backend.execute(
            prompt=command,
            agent=agent,
            auto_close=auto_close,
            working_dir=working_dir,
            gpu=gpu,
        )

        if result["success"]:
            output_msg = f"✅ Docker execution completed\n"
            if result['output']:
                output_msg += f"\nOutput:\n{result['output']}\n"
            if auto_close:
                output_msg += "\n🔒 Container removed"
            return output_msg
        else:
            error_msg = f"❌ Docker execution failed\n"
            if result['error']:
                error_msg += f"Error: {result['error']}\n"
            return error_msg

    except Exception as e:
        return f"❌ Docker execution error: {str(e)}"


import re
import shlex


def _get_configured_ssh_hosts() -> list:
    """Get list of configured SSH host names"""
    if not SSH_AVAILABLE:
        return []
    try:
        manager = SSHHostConfigManager()
        return manager.list_hosts()
    except Exception:
        return []


def parse_command(command: str) -> dict:
    """
    Parse the command string to extract agent, backend, auto_close, ssh_host, and the core command.

    Args:
        command: The command string

    Returns:
        A dictionary containing parsed components.
    """
    # Defaults
    result = {
        "agent": None,
        "backend": "local",
        "ssh_host": None,
        "auto_close": False,
        "command": command.strip(),
    }

    cmd = result["command"]

    # 1. Detect and strip auto-close
    auto_close_pattern = r"^(auto-close|--auto-close)\s*|\s*(auto-close|--auto-close)$"
    if re.search(auto_close_pattern, cmd, re.IGNORECASE):
        result["auto_close"] = True
        cmd = re.sub(auto_close_pattern, "", cmd, flags=re.IGNORECASE).strip()

    # 2. Detect E2B sandbox backend
    sandbox_pattern = r"\s*(in sandbox|sandbox:|use sandbox|with sandbox)\s*"
    sandbox_match = re.search(sandbox_pattern, cmd, re.IGNORECASE)
    if sandbox_match:
        result["backend"] = "e2b"
        # Remove the backend keyword from the command
        cmd = cmd[:sandbox_match.start()] + cmd[sandbox_match.end():]

    # 3. Detect Docker backend
    if result["backend"] == "local":
        docker_pattern = r"\s*(in docker|docker:|use docker|with docker)\s*"
        docker_match = re.search(docker_pattern, cmd, re.IGNORECASE)
        if docker_match:
            result["backend"] = "docker"
            cmd = cmd[:docker_match.start()] + cmd[docker_match.end():]

    # 4. Detect SSH backend - check for known host patterns
    # Patterns: "on <host>", "ssh to <host>", "remote:<host>", "@<host>"
    configured_hosts = _get_configured_ssh_hosts()

    if configured_hosts and result["backend"] == "local":
        # Build pattern for known hosts
        hosts_pattern = "|".join(re.escape(h) for h in configured_hosts)

        # Pattern 1: "on <hostname>" (e.g., "on dgx")
        # Use (?:^|\s+) to match at start of string OR after whitespace
        on_host_pattern = rf"(?:^|\s+)on\s+({hosts_pattern})\b"
        on_host_match = re.search(on_host_pattern, cmd, re.IGNORECASE)
        if on_host_match:
            result["backend"] = "ssh"
            result["ssh_host"] = on_host_match.group(1).lower()
            cmd = cmd[:on_host_match.start()] + cmd[on_host_match.end():]

        # Pattern 2: "ssh to <hostname>" (e.g., "ssh to dgx")
        if not result["ssh_host"]:
            ssh_to_pattern = rf"\s*ssh\s+to\s+({hosts_pattern})\b"
            ssh_to_match = re.search(ssh_to_pattern, cmd, re.IGNORECASE)
            if ssh_to_match:
                result["backend"] = "ssh"
                result["ssh_host"] = ssh_to_match.group(1).lower()
                cmd = cmd[:ssh_to_match.start()] + cmd[ssh_to_match.end():]

        # Pattern 3: "remote:<hostname>" (e.g., "remote:dgx")
        if not result["ssh_host"]:
            remote_pattern = rf"\s*remote:({hosts_pattern})\b"
            remote_match = re.search(remote_pattern, cmd, re.IGNORECASE)
            if remote_match:
                result["backend"] = "ssh"
                result["ssh_host"] = remote_match.group(1).lower()
                cmd = cmd[:remote_match.start()] + cmd[remote_match.end():]

        # Pattern 4: "@<hostname>" at start (e.g., "@dgx ls -la")
        if not result["ssh_host"]:
            at_host_pattern = rf"^@({hosts_pattern})\s+"
            at_host_match = re.search(at_host_pattern, cmd, re.IGNORECASE)
            if at_host_match:
                result["backend"] = "ssh"
                result["ssh_host"] = at_host_match.group(1).lower()
                cmd = cmd[at_host_match.end():]

    # 4. Detect agent
    # Pattern to find "use <agent>" or just the agent name
    agent_pattern = r"(use\s+)?(claude-code|claude\s+code|claude|gemini|codex)"
    agent_match = re.search(agent_pattern, cmd, re.IGNORECASE)
    if agent_match:
        agent_name = agent_match.group(2).lower().replace(" ", "-")
        result["agent"] = agent_name
        # Remove the agent keyword from the command
        cmd = cmd[:agent_match.start()] + cmd[agent_match.end():]

    # 5. Clean up the final command/prompt
    # Remove leading "to" or ":" if present
    cmd = cmd.strip()
    if cmd.startswith(":"):
        cmd = cmd[1:].strip()
    result["command"] = cmd.lstrip("to ").strip()

    return result


def fork_terminal(command: str) -> str:
    """Open a new Terminal window and run the specified command.

    Add '--auto-close' or 'auto-close' to the command to close the window when complete.
    Add 'in sandbox' or similar keywords to execute in E2B sandbox instead of local terminal.
    Add 'on <hostname>' or 'ssh to <hostname>' to execute on a remote SSH host.
    """
    system = platform.system()
    cwd = os.getcwd()

    # Parse the command to get components
    parsed_command = parse_command(command)
    agent = parsed_command["agent"]
    backend = parsed_command["backend"]
    ssh_host = parsed_command.get("ssh_host")
    auto_close = parsed_command["auto_close"]
    command = parsed_command["command"]

    # Route to SSH backend if requested
    if backend == "ssh" and ssh_host:
        if not SSH_AVAILABLE:
            return (
                "❌ SSH backend not available.\n"
                "Install dependencies: pip install paramiko pyyaml"
            )

        return _execute_via_ssh(ssh_host, agent, command, auto_close, working_dir=cwd)

    # Route to E2B sandbox if requested
    if backend == "e2b":
        if not SANDBOX_AVAILABLE:
            return (
                "❌ E2B sandbox backend not available.\n"
                "Install dependencies: pip install -r requirements.txt"
            )

        # Allow raw CLI commands in sandbox
        return _execute_in_sandbox(agent, command, auto_close, working_dir=cwd)

    # Route to Docker backend if requested
    if backend == "docker":
        if not DOCKER_AVAILABLE:
            return (
                "❌ Docker backend not available.\n"
                "Ensure docker_backend.py is in the tools directory."
            )

        return _execute_in_docker(agent, command, auto_close, working_dir=cwd)

    # Handle local agent execution
    if agent is not None:
        # Build CLI command based on agent
        # Source NVM first to ensure CLI tools are available
        nvm_source = "source ~/.nvm/nvm.sh 2>/dev/null || true"

        # Use shlex.quote to prevent command injection
        quoted_prompt = shlex.quote(command)

        if agent == "codex":
            if auto_close:
                command = f"{nvm_source} && codex exec --full-auto --sandbox danger-full-access --skip-git-repo-check {quoted_prompt}"
            else:
                command = f"{nvm_source} && codex {quoted_prompt}"
        elif agent == "gemini":
            if auto_close:
                command = f"{nvm_source} && gemini -y -p {quoted_prompt}"
            else:
                command = f"{nvm_source} && gemini {quoted_prompt}"
        elif agent == "claude":
            if auto_close:
                command = f"{nvm_source} && claude -p --dangerously-skip-permissions {quoted_prompt}"
            else:
                command = f"{nvm_source} && claude {quoted_prompt}"


    # Continue with local terminal execution (existing logic)

    if system == "Darwin":  # macOS
        # Build shell command - use single quotes for cd to avoid escaping issues
        shell_command = f"cd '{cwd}' && {command}"
        # Escape for AppleScript: backslashes first, then quotes
        escaped_shell_command = shell_command.replace("\\", "\\\\").replace('"', '\\"')

        try:
            if auto_close:
                # For auto-close, run command directly and capture output
                # instead of opening a terminal window
                # Use zsh login shell to ensure NVM and other tools are available
                result = subprocess.run(
                    ["/bin/zsh", "-lc", shell_command],
                    capture_output=True,
                    text=True,
                )
                output = f"✅ Command completed (auto-closed)\n"
                if result.stdout.strip():
                    output += f"\n[Output]\n{result.stdout.strip()}\n"
                if result.stderr.strip():
                    output += f"\n[Error]\n{result.stderr.strip()}\n"
                output += f"\nExit code: {result.returncode}"
                return output
            else:
                # For interactive mode, open terminal window normally
                result = subprocess.run(
                    ["osascript", "-e", f'tell application "Terminal" to do script "{escaped_shell_command}"'],
                    capture_output=True,
                    text=True,
                )
                output = f"stdout: {result.stdout.strip()}\nstderr: {result.stderr.strip()}\nreturn_code: {result.returncode}"
                return output
        except Exception as e:
            return f"Error: {str(e)}"

    elif system == "Windows":
        # Use /d flag to change drives if necessary
        # /k keeps window open, /c closes it after command completes
        full_command = f'cd /d "{cwd}" && {command}'
        cmd_flag = "/c" if auto_close else "/k"
        subprocess.Popen(["cmd", "/c", "start", "cmd", cmd_flag, full_command])  # nosec B602
        return "Windows terminal launched"

    else:  # Linux
        # Try to find a common terminal emulator
        terminals = [
            ("gnome-terminal", "--"),
            ("konsole", "-e"),
            ("xterm", "-e")
        ]
        
        selected_terminal = None
        for terminal, arg_sep in terminals:
            if subprocess.run(["which", terminal], capture_output=True).returncode == 0:
                selected_terminal = (terminal, arg_sep)
                break

        if not selected_terminal:
            return "Error: Could not find a supported terminal emulator (gnome-terminal, konsole, xterm)."

        terminal_cmd, arg_separator = selected_terminal
        
        # Construct the command to be run in the new terminal
        shell_command = f"cd '{cwd}' && {command}"
        
        try:
            if auto_close:
                # Run command directly and capture output for auto-close
                result = subprocess.run(
                    ["/bin/bash", "-c", shell_command],
                    capture_output=True,
                    text=True,
                )
                output = f"✅ Command completed (auto-closed)\n"
                if result.stdout.strip():
                    output += f"\n[Output]\n{result.stdout.strip()}\n"
                if result.stderr.strip():
                    output += f"\n[Error]\n{result.stderr.strip()}\n"
                output += f"\nExit code: {result.returncode}"
                return output
            else:
                # Open a new terminal window
                if arg_separator == "--": # gnome-terminal
                    subprocess.Popen([terminal_cmd, arg_separator, "bash", "-c", shell_command])
                else: # konsole, xterm
                    subprocess.Popen([terminal_cmd, arg_separator, shell_command])
                return f"{terminal_cmd} terminal launched"
        except Exception as e:
            return f"Error: {str(e)}"


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        output = fork_terminal(" ".join(sys.argv[1:]))
        print(output)
