#!/usr/bin/env -S uv run
"""Fork a new terminal window with a command."""

import os
import platform
import subprocess


def fork_terminal(command: str) -> str:
    """Open a new Terminal window and run the specified command.

    Add '--auto-close' or 'auto-close' to the command to close the window when complete.
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
