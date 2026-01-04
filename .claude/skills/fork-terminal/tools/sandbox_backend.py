"""
E2B Sandbox Backend

Provides isolated execution environment for AI agents using E2B sandboxes.
Supports Claude Code, Gemini CLI, and Codex CLI in secure cloud containers.
"""

import os
import sys
from pathlib import Path
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
        self.template_id = self._load_template_id()
        self._ensure_e2b_available()

    def _load_template_id(self) -> Optional[str]:
        """Load E2B template ID from file if it exists"""
        template_file = Path(__file__).parent / ".e2b_template_id"

        if template_file.exists():
            template_id = template_file.read_text().strip()
            if template_id:
                return template_id

        return None

    def _ensure_e2b_available(self):
        """Ensure E2B SDK is installed"""
        try:
            from e2b import Sandbox
            self.Sandbox = Sandbox
        except ImportError:
            print("❌ E2B SDK not installed.")
            print("\nTo use sandbox backend, install dependencies:")
            print("  pip install -r requirements.txt")
            print("\nOr install directly:")
            print("  pip install e2b")
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
            if self.template_id:
                print(f"📦 Using custom template: {self.template_id}")
            else:
                print(f"⚠️  Using base template (AI CLIs via wrappers)")
                print(f"💡 Build custom template for better performance:")
                print(f"   cd .claude/skills/fork-terminal/tools/e2b-template && ./build.sh")

        try:
            # Set E2B API key as environment variable (required by E2B SDK)
            original_e2b_key = os.environ.get('E2B_API_KEY')
            os.environ['E2B_API_KEY'] = e2b_key

            # Create sandbox with template if available
            if self.template_id:
                sandbox = self.Sandbox.create(template=self.template_id)
            else:
                # Use base template and install dependencies at runtime
                sandbox = self.Sandbox.create()

                if self.verbose:
                    print("📦 Installing Python API libraries...")

                # Install Python libraries for AI agents
                install_cmd = "pip3 install -q anthropic google-genai openai"
                sandbox.commands.run(install_cmd)

                if self.verbose:
                    print("✓ API libraries installed")

            # Restore original E2B key if it existed
            if original_e2b_key:
                os.environ['E2B_API_KEY'] = original_e2b_key
            elif 'E2B_API_KEY' in os.environ:
                del os.environ['E2B_API_KEY']

            if self.verbose:
                print(f"✓ Sandbox created: {sandbox.sandbox_id}")
                print(f"🚀 Executing: {command}\n")

            # Write Python script to sandbox file system to avoid shell escaping issues
            # Extract Python code from shell command: python3 -c "CODE"
            if command.startswith('python3 -c "') and command.endswith('"'):
                script_content = command[len('python3 -c "'):-1]
            else:
                script_content = command

            # Write script to temp file
            sandbox.files.write("/tmp/ai_agent.py", script_content)

            # Execute with environment variable
            env_var_name = self.resolver.AGENT_KEY_MAP[agent]
            safe_credential = agent_credential.replace("'", "'\\''")
            exec_command = f"export {env_var_name}='{safe_credential}' && python3 /tmp/ai_agent.py"

            result = sandbox.commands.run(exec_command)

            # Get command result
            output = result.stdout if hasattr(result, 'stdout') else ""
            error = result.stderr if hasattr(result, 'stderr') and result.stderr else None
            exit_code = result.exit_code if hasattr(result, 'exit_code') else 0

            if self.verbose:
                if output:
                    print(f"\n[Output]\n{output}")
                if error:
                    print(f"\n[Error]\n{error}")
                print(f"\nExit code: {exit_code}")

            # Kill sandbox if auto-close enabled
            if auto_close:
                if self.verbose:
                    print("\n🔒 Auto-closing sandbox...")
                sandbox.kill()

            return {
                "success": exit_code == 0,
                "output": output,
                "error": error,
                "sandbox_id": sandbox.sandbox_id
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

        Uses Python API libraries to run AI agents since CLI tools may not be available.

        Args:
            agent: Agent name
            prompt: User prompt
            model: Optional model override
            auto_close: Whether auto-close is enabled

        Returns:
            Shell command to execute in sandbox
        """
        # Escape single quotes in prompt for shell and Python safety
        safe_prompt = prompt.replace("'", "'\\''").replace('"', '\\"')

        if agent == "claude":
            # Use Anthropic Python API
            model_str = f'"{model}"' if model else '"claude-3-5-sonnet-20241022"'
            return f'''python3 -c "
import os, anthropic
client = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])
response = client.messages.create(
    model={model_str},
    max_tokens=4096,
    messages=[{{'role': 'user', 'content': '{safe_prompt}'}}]
)
print(response.content[0].text)
"'''

        elif agent == "gemini":
            # Use Google Genai Python API (new library)
            model_str = f'"{model}"' if model else '"gemini-2.0-flash-exp"'
            return f'''python3 -c "
import os
from google import genai
client = genai.Client(api_key=os.environ['GEMINI_API_KEY'])
response = client.models.generate_content(
    model={model_str},
    contents='{safe_prompt}'
)
print(response.text)
"'''

        elif agent == "codex":
            # Use OpenAI Python API
            model_str = f'"{model}"' if model else '"gpt-4-turbo-preview"'
            return f'''python3 -c "
import os
from openai import OpenAI
client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
response = client.chat.completions.create(
    model={model_str},
    messages=[{{'role': 'user', 'content': '{safe_prompt}'}}]
)
print(response.choices[0].message.content)
"'''

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
