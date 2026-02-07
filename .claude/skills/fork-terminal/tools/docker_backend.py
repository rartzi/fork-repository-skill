#!/usr/bin/env python3
"""Docker backend for fork-terminal: execute commands and AI agents in Docker containers."""

import os
import shlex
import subprocess
import sys
from pathlib import Path

# Ensure tools directory is on path for imports
tools_dir = Path(__file__).parent
if str(tools_dir) not in sys.path:
    sys.path.insert(0, str(tools_dir))

try:
    from credential_resolver import CredentialResolver
except ImportError:
    CredentialResolver = None

# Docker image name for the pre-built agents image
DOCKER_IMAGE = "fork-terminal-agents"
DOCKERFILE_PATH = Path(__file__).parent / "Dockerfile.agents"


class DockerBackend:
    """Execute commands and AI agents in Docker containers."""

    def __init__(self, verbose=False):
        self.verbose = verbose
        self._docker_available = None

    def _log(self, msg: str):
        if self.verbose:
            print(msg)

    def _is_docker_available(self) -> bool:
        """Check if Docker daemon is running."""
        if self._docker_available is not None:
            return self._docker_available
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            self._docker_available = result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self._docker_available = False
        return self._docker_available

    def _image_exists(self) -> bool:
        """Check if the fork-terminal-agents image exists locally."""
        try:
            result = subprocess.run(
                ["docker", "image", "inspect", DOCKER_IMAGE],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _build_image(self) -> bool:
        """Auto-build the Docker image from Dockerfile.agents."""
        if not DOCKERFILE_PATH.exists():
            self._log(f"❌ Dockerfile not found: {DOCKERFILE_PATH}")
            return False

        self._log(f"🔨 Building Docker image '{DOCKER_IMAGE}' (first run)...")
        self._log(f"   Dockerfile: {DOCKERFILE_PATH}")

        try:
            result = subprocess.run(
                [
                    "docker", "build",
                    "-t", DOCKER_IMAGE,
                    "-f", str(DOCKERFILE_PATH),
                    str(DOCKERFILE_PATH.parent),
                ],
                capture_output=True,
                text=True,
                timeout=600,  # 10 min timeout for build
            )
            if result.returncode == 0:
                self._log(f"✅ Image '{DOCKER_IMAGE}' built successfully")
                return True
            else:
                self._log(f"❌ Image build failed:\n{result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            self._log("❌ Image build timed out (10 min)")
            return False

    def _resolve_agent_env(self, agent: str) -> dict:
        """Resolve API key for the agent using CredentialResolver waterfall.

        Resolution order: env vars -> .env file -> macOS Keychain -> config files.
        """
        env_map = {
            "claude": "ANTHROPIC_API_KEY",
            "claude-code": "ANTHROPIC_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "codex": "OPENAI_API_KEY",
        }

        env_vars = {}
        if not agent:
            return env_vars

        # Normalize agent name for CredentialResolver lookup
        resolver_agent = "claude" if agent == "claude-code" else agent

        # Try CredentialResolver waterfall (env -> keychain -> .env -> config)
        if CredentialResolver is not None:
            try:
                resolver = CredentialResolver()
                key_value = resolver.get_credential(resolver_agent, verbose=self.verbose)
                key_name = env_map.get(agent)
                if key_value and key_name:
                    env_vars[key_name] = key_value
                    return env_vars
            except Exception as e:
                self._log(f"⚠️  CredentialResolver failed: {e}")

        # Fallback: direct env var lookup
        if agent in env_map:
            key_name = env_map[agent]
            key_value = os.environ.get(key_name)
            if key_value:
                env_vars[key_name] = key_value
            else:
                self._log(f"⚠️  {key_name} not found in environment or keychain")

        return env_vars

    def _build_agent_command(self, agent: str, prompt: str, auto_close: bool) -> str:
        """Build the CLI command for the specified agent."""
        quoted = shlex.quote(prompt)

        if agent == "codex":
            # Codex requires explicit login; pipe the API key from env var
            login_cmd = "echo $OPENAI_API_KEY | codex login --with-api-key 2>/dev/null"
            if auto_close:
                return f"{login_cmd} && codex exec --full-auto --sandbox danger-full-access --skip-git-repo-check {quoted}"
            else:
                return f"{login_cmd} && codex {quoted}"
        elif agent == "gemini":
            if auto_close:
                return f"gemini -y -p {quoted}"
            else:
                return f"gemini {quoted}"
        elif agent in ("claude", "claude-code"):
            if auto_close:
                return f"claude -p --dangerously-skip-permissions {quoted}"
            else:
                return f"claude {quoted}"
        else:
            # Raw command
            return prompt

    def execute(
        self,
        prompt: str,
        agent: str = None,
        auto_close: bool = True,
        working_dir: str = None,
        gpu: bool = False,
    ) -> dict:
        """
        Execute a command or AI agent in a Docker container.

        Args:
            prompt: Command or agent prompt.
            agent: Agent name ("claude", "gemini", "codex") or None for raw CLI.
            auto_close: Remove container after execution (--rm).
            working_dir: Local directory to mount as /workspace.
            gpu: Enable GPU passthrough (--gpus all).

        Returns:
            dict with keys: success, output, error, container_id
        """
        result = {
            "success": False,
            "output": "",
            "error": "",
            "container_id": None,
        }

        # Check Docker is available
        if not self._is_docker_available():
            result["error"] = "Docker daemon is not running or not installed."
            return result

        # Ensure image exists, auto-build if needed
        if not self._image_exists():
            self._log(f"📦 Image '{DOCKER_IMAGE}' not found locally.")
            if not self._build_image():
                result["error"] = (
                    f"Docker image '{DOCKER_IMAGE}' not found and auto-build failed.\n"
                    f"Build manually: docker build -t {DOCKER_IMAGE} "
                    f"-f {DOCKERFILE_PATH} {DOCKERFILE_PATH.parent}"
                )
                return result

        # Build the command to run inside the container
        if agent:
            container_cmd = self._build_agent_command(agent, prompt, auto_close)
        else:
            container_cmd = prompt

        # Build docker run arguments
        docker_args = ["docker", "run"]

        if auto_close:
            docker_args.append("--rm")

        # Interactive TTY for non-auto-close
        if not auto_close:
            docker_args.extend(["-it"])

        # GPU passthrough
        if gpu:
            docker_args.extend(["--gpus", "all"])

        # Mount working directory
        if working_dir:
            docker_args.extend(["-v", f"{working_dir}:/workspace", "-w", "/workspace"])

        # Inject agent credentials as environment variables
        env_vars = self._resolve_agent_env(agent)
        for key, value in env_vars.items():
            docker_args.extend(["-e", f"{key}={value}"])

        # Image and command
        docker_args.append(DOCKER_IMAGE)
        docker_args.extend(["bash", "-c", container_cmd])

        self._log(f"🐳 Running in Docker container...")
        if agent:
            self._log(f"   Agent: {agent}")
        self._log(f"   Command: {container_cmd}")
        if gpu:
            self._log(f"   GPU: enabled")

        try:
            proc = subprocess.run(
                docker_args,
                capture_output=True,
                text=True,
                timeout=600,  # 10 min timeout
            )

            result["output"] = proc.stdout.strip()
            if proc.returncode == 0:
                result["success"] = True
            else:
                result["error"] = proc.stderr.strip()
                # Still mark as success if there's output (some agents write to stderr)
                if result["output"]:
                    result["success"] = True

        except subprocess.TimeoutExpired:
            result["error"] = "Docker execution timed out (10 min)"
        except Exception as e:
            result["error"] = str(e)

        return result
