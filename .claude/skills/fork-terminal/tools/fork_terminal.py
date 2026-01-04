#!/usr/bin/env -S uv run
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

# Import credential resolution and sandbox backend
try:
    from credential_resolver import CredentialResolver, CredentialNotFoundError
    from sandbox_backend import SandboxBackend
    SANDBOX_AVAILABLE = True
except ImportError:
    SANDBOX_AVAILABLE = False
    CredentialResolver = None
    SandboxBackend = None


def _execute_in_sandbox(agent: str, command: str, auto_close: bool) -> str:
    """
    Execute an AI agent in E2B sandbox

    Args:
        agent: Agent name ("claude", "gemini", "codex")
        command: The command/prompt
        auto_close: Close sandbox after execution

    Returns:
        Execution result string
    """
    try:
        backend = SandboxBackend(verbose=True)

        # Extract the actual prompt from the command
        # Remove sandbox keywords and agent names
        prompt = command
        for keyword in ["in sandbox", "sandbox:", "use sandbox", "with sandbox"]:
            prompt = prompt.replace(keyword, "")
        for ag in ["claude", "gemini", "codex", "claude code", "claude-code"]:
            prompt = prompt.replace(f"use {ag}", "").replace(ag, "")

        prompt = prompt.replace("to ", "", 1).strip()  # Remove leading "to"

        print(f"\n📦 Executing {agent} in E2B sandbox...")
        print(f"💬 Prompt: {prompt}\n")

        result = backend.execute_agent(agent, prompt, auto_close=auto_close)

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


def detect_backend(command: str) -> str:
    """
    Detect which backend to use based on command keywords

    Args:
        command: The command string

    Returns:
        "e2b" if sandbox backend requested, "local" otherwise
    """
    command_lower = command.lower()
    sandbox_keywords = ["in sandbox", "sandbox:", "use sandbox", "with sandbox"]

    for keyword in sandbox_keywords:
        if keyword in command_lower:
            return "e2b"

    return "local"


def detect_agent(command: str) -> str:
    """
    Detect which AI agent is being requested

    Args:
        command: The command string

    Returns:
        Agent name ("claude", "gemini", "codex") or None if not an agentic command
    """
    command_lower = command.lower()

    # Check for agent keywords
    if "claude" in command_lower or "claude-code" in command_lower or "claude code" in command_lower:
        return "claude"
    elif "gemini" in command_lower:
        return "gemini"
    elif "codex" in command_lower:
        return "codex"

    return None


def fork_terminal(command: str) -> str:
    """Open a new Terminal window and run the specified command.

    Add '--auto-close' or 'auto-close' to the command to close the window when complete.
    Add 'in sandbox' or similar keywords to execute in E2B sandbox instead of local terminal.
    """
    system = platform.system()
    cwd = os.getcwd()

    # Check for auto-close flag
    auto_close = False
    command_clean = command.strip()

    # Check for auto-close at the beginning or end
    if command_clean.startswith("auto-close ") or command_clean.startswith("--auto-close "):
        auto_close = True
        command_clean = command_clean.replace("auto-close ", "", 1).replace("--auto-close ", "", 1).strip()
    elif command_clean.endswith(" auto-close") or command_clean.endswith(" --auto-close"):
        auto_close = True
        command_clean = command_clean.replace(" auto-close", "", 1).replace(" --auto-close", "", 1).strip()

    command = command_clean

    # Detect backend (local or E2B sandbox)
    backend = detect_backend(command)
    agent = detect_agent(command)

    # Route to E2B sandbox if requested
    if backend == "e2b":
        if not SANDBOX_AVAILABLE:
            return (
                "❌ E2B sandbox backend not available.\n"
                "Install dependencies: pip install -r requirements.txt"
            )

        if agent is None:
            return (
                "❌ Sandbox backend requires an AI agent (claude, gemini, or codex).\n"
                "Example: 'use gemini in sandbox to create hello.py'"
            )

        return _execute_in_sandbox(agent, command, auto_close)

    # Continue with local terminal execution (existing logic)

    if system == "Darwin":  # macOS
        # Build shell command - use single quotes for cd to avoid escaping issues
        shell_command = f"cd '{cwd}' && {command}"
        # Escape for AppleScript: backslashes first, then quotes
        escaped_shell_command = shell_command.replace("\\", "\\\\").replace('"', '\\"')

        try:
            if auto_close:
                # Use AppleScript to create tab, wait for completion, then close the window
                applescript = f'''
                tell application "Terminal"
                    set newTab to do script "{escaped_shell_command}"
                    repeat
                        delay 0.5
                        if not busy of newTab then exit repeat
                    end repeat
                    set theWindow to first window whose tabs contains newTab
                    close theWindow
                end tell
                '''
                result = subprocess.run(
                    ["osascript", "-e", applescript],
                    capture_output=True,
                    text=True,
                )
            else:
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
        subprocess.Popen(["cmd", "/c", "start", "cmd", cmd_flag, full_command], shell=True)
        return "Windows terminal launched"

    else:  # Linux and others
        raise NotImplementedError(f"Platform {system} not supported")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        output = fork_terminal(" ".join(sys.argv[1:]))
        print(output)
