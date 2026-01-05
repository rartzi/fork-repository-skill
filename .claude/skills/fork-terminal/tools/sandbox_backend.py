"""
E2B Sandbox Backend

Provides isolated execution environment for AI agents using E2B sandboxes.
Supports Claude Code, Gemini CLI, and Codex CLI in secure cloud containers.
"""

import os
import sys
import re
from pathlib import Path
from typing import Optional, List, Dict
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

    def _detect_file_references(self, prompt: str, working_dir: str = None) -> List[Dict[str, str]]:
        """
        Detect file references in the prompt

        Args:
            prompt: The user's prompt
            working_dir: Current working directory (defaults to cwd)

        Returns:
            List of dicts with 'local_path' and 'sandbox_path' keys
        """
        if working_dir is None:
            working_dir = os.getcwd()

        file_refs = []

        # Pattern 1: Common file extensions
        file_patterns = [
            r'\b([a-zA-Z0-9_\-/.]+\.(?:md|py|js|ts|tsx|jsx|json|yaml|yml|txt|csv|html|css|sh|bash))\b',
            r'\b([A-Z][A-Z0-9_]+\.md)\b',  # UPPERCASE.md files like SKILL.MD, README.MD
            r'\b(my\s+)?([a-zA-Z0-9_\-]+\.[a-zA-Z0-9]+)\b',  # "my file.txt" pattern
        ]

        for pattern in file_patterns:
            matches = re.findall(pattern, prompt, re.IGNORECASE)
            for match in matches:
                # Handle tuple matches from groups
                filename = match if isinstance(match, str) else match[-1]
                filename = filename.strip()

                if not filename:
                    continue

                # Security: Prevent path traversal attacks
                if '..' in filename or filename.startswith('/'):
                    if self.verbose:
                        print(f"⚠️  Skipping suspicious file path: {filename}")
                    continue

                # Try to resolve the file path
                local_path = Path(working_dir) / filename

                # Also try without "my " prefix if present
                if not local_path.exists() and filename.lower().startswith("my "):
                    filename = filename[3:].strip()
                    local_path = Path(working_dir) / filename

                # Check if file exists locally
                if local_path.exists() and local_path.is_file():
                    sandbox_path = f"/home/user/{local_path.name}"

                    # Avoid duplicates
                    if not any(ref['local_path'] == str(local_path) for ref in file_refs):
                        file_refs.append({
                            'local_path': str(local_path),
                            'sandbox_path': sandbox_path,
                            'original_ref': filename
                        })

        return file_refs

    def _upload_files_to_sandbox(self, sandbox, file_refs: List[Dict[str, str]]) -> Dict[str, str]:
        """
        Upload files to the sandbox

        Args:
            sandbox: E2B sandbox instance
            file_refs: List of file reference dicts from _detect_file_references

        Returns:
            Dict mapping original references to sandbox paths
        """
        path_mapping = {}

        for ref in file_refs:
            local_path = ref['local_path']
            sandbox_path = ref['sandbox_path']
            original_ref = ref['original_ref']

            try:
                # Read local file
                with open(local_path, 'r') as f:
                    content = f.read()

                # Upload to sandbox
                sandbox.files.write(sandbox_path, content)

                if self.verbose:
                    print(f"📤 Uploaded: {local_path} → {sandbox_path}")

                # Map original reference to sandbox path
                path_mapping[original_ref] = sandbox_path
                path_mapping[local_path] = sandbox_path

            except Exception as e:
                if self.verbose:
                    print(f"⚠️  Failed to upload {local_path}: {e}")

        return path_mapping

    def _rewrite_prompt_with_sandbox_paths(self, prompt: str, path_mapping: Dict[str, str]) -> str:
        """
        Rewrite the prompt to use sandbox paths

        Args:
            prompt: Original prompt
            path_mapping: Dict mapping local paths to sandbox paths

        Returns:
            Rewritten prompt with sandbox paths
        """
        rewritten = prompt

        # Sort by length (longest first) to avoid partial replacements
        for original_ref in sorted(path_mapping.keys(), key=len, reverse=True):
            sandbox_path = path_mapping[original_ref]

            # Replace various forms of the reference
            rewritten = rewritten.replace(f"my {original_ref}", sandbox_path)
            rewritten = rewritten.replace(original_ref, sandbox_path)

        return rewritten

    def _download_output_files(self, sandbox, output_dir: str) -> List[str]:
        """
        Download output files from sandbox to local directory

        Args:
            sandbox: E2B sandbox instance
            output_dir: Local directory to save files

        Returns:
            List of local file paths that were downloaded
        """
        downloaded_files = []
        sandbox_output_dir = "/home/user/output"

        try:
            # Check if output directory exists in sandbox
            result = sandbox.commands.run(f"test -d {sandbox_output_dir} && echo exists || echo missing")
            if "missing" in result.stdout:
                if self.verbose:
                    print(f"ℹ️  No output directory in sandbox ({sandbox_output_dir})")
                return downloaded_files

            # List all files in output directory recursively
            result = sandbox.commands.run(f"find {sandbox_output_dir} -type f")
            if result.exit_code != 0 or not result.stdout.strip():
                if self.verbose:
                    print(f"ℹ️  No files in sandbox output directory")
                return downloaded_files

            file_paths = result.stdout.strip().split('\n')

            # Create local output directory
            local_output_path = Path(output_dir)
            local_output_path.mkdir(parents=True, exist_ok=True)

            if self.verbose:
                print(f"\n📥 Downloading {len(file_paths)} file(s) from sandbox...")

            # Download each file
            for sandbox_file_path in file_paths:
                sandbox_file_path = sandbox_file_path.strip()
                if not sandbox_file_path:
                    continue

                try:
                    # Security: Validate file is within output directory
                    if not sandbox_file_path.startswith(f"{sandbox_output_dir}/"):
                        if self.verbose:
                            print(f"   ⚠️  Skipping file outside output directory: {sandbox_file_path}")
                        continue

                    # Get relative path from /home/user/output/
                    relative_path = sandbox_file_path.replace(f"{sandbox_output_dir}/", "")

                    # Security: Prevent directory traversal in relative path
                    if '..' in relative_path or relative_path.startswith('/'):
                        if self.verbose:
                            print(f"   ⚠️  Skipping suspicious path: {relative_path}")
                        continue

                    # Create local file path
                    local_file_path = local_output_path / relative_path
                    local_file_path.parent.mkdir(parents=True, exist_ok=True)

                    # Read file content from sandbox
                    content = sandbox.files.read(sandbox_file_path)

                    # Write to local file
                    with open(local_file_path, 'w') as f:
                        f.write(content)

                    downloaded_files.append(str(local_file_path))

                    if self.verbose:
                        print(f"   ✓ {sandbox_file_path} → {local_file_path}")

                except Exception as e:
                    if self.verbose:
                        print(f"   ⚠️  Failed to download {sandbox_file_path}: {e}")

            if self.verbose and downloaded_files:
                print(f"\n✅ Downloaded {len(downloaded_files)} file(s) to {output_dir}/")

        except Exception as e:
            if self.verbose:
                print(f"⚠️  Error during file download: {e}")

        return downloaded_files

    def execute_agent(
        self,
        agent: str,
        prompt: str,
        auto_close: bool = False,
        model: Optional[str] = None,
        working_dir: Optional[str] = None,
        download_output: bool = True,
        output_dir: str = "./sandbox-output"
    ) -> dict:
        """
        Execute an AI agent in an isolated E2B sandbox

        Args:
            agent: Agent name ("claude", "gemini", "codex")
            prompt: The prompt/task for the agent
            auto_close: Close sandbox after execution
            model: Optional model override
            working_dir: Working directory to resolve file paths (defaults to cwd)
            download_output: Download files from /home/user/output/ after execution (default: True)
            output_dir: Local directory to save downloaded files (default: ./sandbox-output)

        Returns:
            Dictionary with execution results:
            {
                "success": bool,
                "output": str,
                "error": Optional[str],
                "sandbox_id": str,
                "downloaded_files": List[str]  # Local paths of downloaded files
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
                "sandbox_id": None,
                "downloaded_files": []
            }

        # Detect file references in prompt
        file_refs = self._detect_file_references(prompt, working_dir)

        if file_refs and self.verbose:
            print(f"\n📁 Detected {len(file_refs)} local file(s) referenced in prompt")

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

            # Upload local files to sandbox if any were detected
            path_mapping = {}
            sandbox_file_paths = []
            if file_refs:
                path_mapping = self._upload_files_to_sandbox(sandbox, file_refs)
                # Rewrite prompt to use sandbox paths
                prompt = self._rewrite_prompt_with_sandbox_paths(prompt, path_mapping)
                # Collect sandbox file paths for reading in the agent command
                sandbox_file_paths = [ref['sandbox_path'] for ref in file_refs]

            # Get agent-specific command (now with potentially rewritten prompt and file paths)
            command = self._build_agent_command(agent, prompt, model, auto_close, sandbox_file_paths)

            if self.verbose:
                print(f"🚀 Executing: python3 /tmp/ai_agent.py\n")

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

            # Download output files if enabled
            downloaded_files = []
            if download_output:
                downloaded_files = self._download_output_files(sandbox, output_dir)

            # Kill sandbox if auto-close enabled
            if auto_close:
                if self.verbose:
                    print("\n🔒 Auto-closing sandbox...")
                sandbox.kill()

            return {
                "success": exit_code == 0,
                "output": output,
                "error": error,
                "sandbox_id": sandbox.sandbox_id,
                "downloaded_files": downloaded_files
            }

        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": f"Sandbox execution failed: {str(e)}",
                "sandbox_id": None,
                "downloaded_files": []
            }

    def _build_agent_command(
        self,
        agent: str,
        prompt: str,
        model: Optional[str],
        auto_close: bool,
        file_paths: Optional[List[str]] = None
    ) -> str:
        """
        Build the command to run the agent in the sandbox

        Uses Python API libraries to run AI agents since CLI tools may not be available.

        Args:
            agent: Agent name
            prompt: User prompt
            model: Optional model override
            auto_close: Whether auto-close is enabled
            file_paths: List of file paths in sandbox to read and include in prompt

        Returns:
            Shell command to execute in sandbox
        """
        # Build file reading logic if files are present
        file_reading_code = ""
        if file_paths:
            file_reading_code = "\n# Read file contents\nfile_contents = {}\n"
            for path in file_paths:
                file_reading_code += f"""
try:
    with open('{path}', 'r') as f:
        file_contents['{path}'] = f.read()
except Exception as e:
    file_contents['{path}'] = f'[Error reading file: {{e}}]'
"""
            # Update prompt to include file contents
            file_reading_code += """
# Build enhanced prompt with file contents
enhanced_prompt = prompt
for path, content in file_contents.items():
    # Find references to this file in prompt and replace with content
    file_marker = f"<FILE: {path}>\\n{content}\\n</FILE>\\n\\n"
    enhanced_prompt = enhanced_prompt.replace(path, file_marker)
"""

        # Escape single quotes in prompt for shell and Python safety
        safe_prompt = prompt.replace("'", "'\\''").replace('"', '\\"')

        # Choose prompt variable based on whether files are present
        prompt_var = "enhanced_prompt" if file_paths else "prompt"

        if agent == "claude":
            # Use Anthropic Python API
            model_str = f'"{model}"' if model else '"claude-3-5-sonnet-20241022"'
            script = f"""import os, anthropic
prompt = {repr(safe_prompt)}
{file_reading_code}
client = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])
response = client.messages.create(
    model={model_str},
    max_tokens=4096,
    messages=[{{'role': 'user', 'content': {prompt_var}}}]
)
print(response.content[0].text)
"""
            return f'python3 -c "{script}"'

        elif agent == "gemini":
            # Use Google Genai Python API (new library)
            model_str = f'"{model}"' if model else '"gemini-2.0-flash-exp"'
            script = f"""import os
from google import genai
prompt = {repr(safe_prompt)}
{file_reading_code}
client = genai.Client(api_key=os.environ['GEMINI_API_KEY'])
response = client.models.generate_content(
    model={model_str},
    contents={prompt_var}
)
print(response.text)
"""
            return f'python3 -c "{script}"'

        elif agent == "codex":
            # Use OpenAI Python API
            model_str = f'"{model}"' if model else '"gpt-4-turbo-preview"'
            script = f"""import os
from openai import OpenAI
prompt = {repr(safe_prompt)}
{file_reading_code}
client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
response = client.chat.completions.create(
    model={model_str},
    messages=[{{'role': 'user', 'content': {prompt_var}}}]
)
print(response.choices[0].message.content)
"""
            return f'python3 -c "{script}"'

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
