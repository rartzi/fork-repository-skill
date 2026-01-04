"""
E2B Sandbox Backend

Provides isolated execution environment for AI agents using E2B sandboxes.
Supports Claude Code, Gemini CLI, and Codex CLI in secure cloud containers.
"""

import sys
from typing import Optional
from credential_resolver import CredentialResolver, CredentialNotFoundError


class SandboxBackend:
    """Manages E2B sandbox creation and agent execution"""

    def __init__(self, verbose: bool = True):
        """
        Initialize sandbox backend

        Args:
            verbose: Print status messages
        """
        self.verbose = verbose
        self.resolver = CredentialResolver()
        self._ensure_e2b_available()

    def _ensure_e2b_available(self):
        """Ensure E2B SDK is installed"""
        try:
            from e2b_code_interpreter import Sandbox
            self.Sandbox = Sandbox
        except ImportError:
            print("❌ E2B SDK not installed.")
            print("\nTo use sandbox backend, install dependencies:")
            print("  pip install -r requirements.txt")
            print("\nOr install directly:")
            print("  pip install e2b-code-interpreter")
            sys.exit(1)

    def execute_agent(
        self,
        agent: str,
        prompt: str,
        auto_close: bool = False,
        model: Optional[str] = None
    ) -> dict:
        """
        Execute an AI agent in an isolated E2B sandbox

        Args:
            agent: Agent name ("claude", "gemini", "codex")
            prompt: The prompt/task for the agent
            auto_close: Close sandbox after execution
            model: Optional model override

        Returns:
            Dictionary with execution results:
            {
                "success": bool,
                "output": str,
                "error": Optional[str],
                "sandbox_id": str
            }

        Raises:
            CredentialNotFoundError: If required credentials not found
        """
        # Resolve credentials using waterfall
        try:
            agent_credential = self.resolver.get_credential(agent, verbose=self.verbose)
            e2b_key = self.resolver.get_credential("e2b", verbose=self.verbose)
        except CredentialNotFoundError as e:
            return {
                "success": False,
                "output": "",
                "error": str(e),
                "sandbox_id": None
            }

        # Get agent-specific command
        command = self._build_agent_command(agent, prompt, model, auto_close)

        if self.verbose:
            print(f"\n🔨 Creating E2B sandbox for {agent}...")

        try:
            # Create sandbox with injected credential
            sandbox = self.Sandbox(
                api_key=e2b_key,
                env_vars={
                    self.resolver.AGENT_KEY_MAP[agent]: agent_credential
                }
            )

            if self.verbose:
                print(f"✓ Sandbox created: {sandbox.id}")
                print(f"🚀 Executing: {command}\n")

            # Execute the agent command
            result = sandbox.run_code(command)

            # Capture output
            output = ""
            error = None

            if hasattr(result, 'stdout'):
                output += result.stdout
            if hasattr(result, 'stderr') and result.stderr:
                error = result.stderr
            if hasattr(result, 'error') and result.error:
                error = str(result.error)

            # Close sandbox if auto-close enabled
            if auto_close:
                if self.verbose:
                    print("\n🔒 Auto-closing sandbox...")
                sandbox.close()

            return {
                "success": error is None,
                "output": output,
                "error": error,
                "sandbox_id": sandbox.id
            }

        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": f"Sandbox execution failed: {str(e)}",
                "sandbox_id": None
            }

    def _build_agent_command(
        self,
        agent: str,
        prompt: str,
        model: Optional[str],
        auto_close: bool
    ) -> str:
        """
        Build the command to run the agent in the sandbox

        Args:
            agent: Agent name
            prompt: User prompt
            model: Optional model override
            auto_close: Whether auto-close is enabled

        Returns:
            Shell command to execute in sandbox
        """
        # Escape single quotes in prompt for shell safety
        safe_prompt = prompt.replace("'", "'\\''")

        if agent == "claude":
            # Claude Code command
            cmd = "claude"
            if auto_close:
                cmd += " -p"  # Non-interactive mode for auto-close
            if model:
                cmd += f" --model {model}"
            cmd += f" '{safe_prompt}'"
            return cmd

        elif agent == "gemini":
            # Gemini CLI command
            cmd = "gemini"
            if auto_close:
                cmd += " -p"  # Non-interactive mode for auto-close
            if model:
                cmd += f" --model {model}"
            cmd += f" '{safe_prompt}'"
            return cmd

        elif agent == "codex":
            # Codex CLI command
            cmd = "codex"
            if auto_close:
                cmd += " -p"  # Non-interactive mode for auto-close
            if model:
                cmd += f" --model {model}"
            cmd += f" '{safe_prompt}'"
            return cmd

        else:
            raise ValueError(f"Unknown agent: {agent}")

    def install_agent(self, agent: str, sandbox) -> bool:
        """
        Install an agent CLI in the sandbox

        Args:
            agent: Agent name
            sandbox: E2B sandbox instance

        Returns:
            True if installation succeeded
        """
        install_commands = {
            "claude": "pip install anthropic-claude-cli",
            "gemini": "pip install google-gemini-cli",
            "codex": "pip install openai-codex-cli"
        }

        cmd = install_commands.get(agent)
        if not cmd:
            return False

        try:
            if self.verbose:
                print(f"📦 Installing {agent} CLI in sandbox...")
            result = sandbox.run_code(cmd)
            return result.error is None
        except Exception:
            return False


def execute_in_sandbox(
    agent: str,
    prompt: str,
    auto_close: bool = False,
    model: Optional[str] = None,
    verbose: bool = True
) -> dict:
    """
    Convenience function to execute agent in sandbox

    Args:
        agent: Agent name ("claude", "gemini", "codex")
        prompt: The prompt/task
        auto_close: Close sandbox after execution
        model: Optional model override
        verbose: Print status messages

    Returns:
        Execution result dictionary
    """
    backend = SandboxBackend(verbose=verbose)
    return backend.execute_agent(agent, prompt, auto_close, model)


if __name__ == "__main__":
    # Test sandbox execution
    import sys

    if len(sys.argv) < 3:
        print("Usage: python sandbox_backend.py <agent> <prompt>")
        print("Example: python sandbox_backend.py gemini 'write hello world in python'")
        sys.exit(1)

    agent = sys.argv[1]
    prompt = " ".join(sys.argv[2:])

    print(f"Testing sandbox execution: {agent}")
    result = execute_in_sandbox(agent, prompt, auto_close=True)

    print("\n" + "="*60)
    print("RESULT:")
    print("="*60)
    print(f"Success: {result['success']}")
    print(f"Sandbox ID: {result['sandbox_id']}")
    if result['output']:
        print(f"\nOutput:\n{result['output']}")
    if result['error']:
        print(f"\nError:\n{result['error']}")
