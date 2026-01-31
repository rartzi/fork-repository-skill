"""
SSH Backend for Fork Terminal

Provides remote command execution and AI agent deployment on SSH-accessible machines.
Optimized for NVIDIA DGX and GPU workstations.

Features:
- SSH connection via Paramiko with key-based authentication
- Connection pooling for performance
- GPU detection via nvidia-smi
- File transfer via Samba share (primary) or SFTP (fallback)
- Remote AI agent execution (claude, gemini, codex)
- API key injection at runtime (never stored on remote)
"""

import sys
import shlex
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass

# Add tools directory to path for imports
tools_dir = Path(__file__).parent
if str(tools_dir) not in sys.path:
    sys.path.insert(0, str(tools_dir))

from credential_resolver import CredentialResolver, CredentialNotFoundError
from ssh_host_config import SSHHostConfigManager, SSHHostConfig


@dataclass
class GPUInfo:
    """Information about a GPU"""
    index: int
    name: str
    memory_total: str
    memory_used: str
    utilization: str


class SSHBackend:
    """Manages SSH connections and remote execution"""

    def __init__(self, verbose: bool = True):
        """
        Initialize SSH backend.

        Args:
            verbose: Print status messages
        """
        self.verbose = verbose
        self.resolver = CredentialResolver()
        self.config_manager = SSHHostConfigManager()
        self._connections: Dict[str, "paramiko.SSHClient"] = {}  # Connection pool
        self._ensure_paramiko_available()

    def _ensure_paramiko_available(self):
        """Ensure Paramiko SSH library is installed"""
        try:
            import paramiko
            self.paramiko = paramiko
        except ImportError:
            print("SSH backend not installed.")
            print("\nTo use SSH backend, install dependencies:")
            print("  pip install paramiko")
            sys.exit(1)

    def _get_connection(self, host_config: SSHHostConfig) -> "paramiko.SSHClient":
        """
        Get or create an SSH connection for a host.

        Uses connection pooling for performance.

        Args:
            host_config: Host configuration

        Returns:
            Connected SSHClient
        """
        host_key = f"{host_config.user}@{host_config.hostname}:{host_config.port}"

        # Check for existing connection
        if host_key in self._connections:
            client = self._connections[host_key]
            # Verify connection is still active
            try:
                transport = client.get_transport()
                if transport and transport.is_active():
                    return client
            except Exception:  # nosec B110 - connection check failure is expected for stale connections
                pass
            # Connection dead, remove from pool
            del self._connections[host_key]

        # Create new connection
        client = self.paramiko.SSHClient()

        # Load system host keys
        client.load_system_host_keys()
        # Also load from known_hosts
        known_hosts = Path.home() / ".ssh" / "known_hosts"
        if known_hosts.exists():
            try:
                client.load_host_keys(str(known_hosts))
            except Exception:  # nosec B110 - non-critical: system keys already loaded
                pass

        # Set policy to reject unknown hosts (security)
        client.set_missing_host_key_policy(self.paramiko.RejectPolicy())

        # Resolve SSH key
        try:
            key_path, _ = self.resolver.get_ssh_key_path(
                explicit_path=None,
                host_config_path=host_config.key_path,
                verbose=self.verbose
            )
        except CredentialNotFoundError as e:
            raise ConnectionError(f"SSH key not found: {e}")

        # Check if key needs passphrase
        passphrase = None
        if self.resolver.check_ssh_key_encrypted(key_path):
            passphrase = self.resolver.get_ssh_passphrase(key_path, verbose=self.verbose)
            if not passphrase:
                raise ConnectionError(
                    f"SSH key {key_path} is encrypted but passphrase not found in keychain.\n"
                    "Add passphrase to keychain with:\n"
                    f"  ssh-add --apple-use-keychain {key_path}"
                )

        # Connect
        if self.verbose:
            print(f"Connecting to {host_config.user}@{host_config.hostname}...")

        try:
            client.connect(
                hostname=host_config.hostname,
                port=host_config.port,
                username=host_config.user,
                key_filename=str(key_path),
                passphrase=passphrase,
                timeout=30,
                allow_agent=True,
                look_for_keys=False
            )
        except self.paramiko.ssh_exception.SSHException as e:
            raise ConnectionError(f"SSH connection failed: {e}")

        # Store in pool
        self._connections[host_key] = client

        if self.verbose:
            print(f"Connected to {host_config.hostname}")

        return client

    def _close_connection(self, host_config: SSHHostConfig):
        """Close connection for a host"""
        host_key = f"{host_config.user}@{host_config.hostname}:{host_config.port}"
        if host_key in self._connections:
            try:
                self._connections[host_key].close()
            except Exception:  # nosec B110 - best-effort cleanup, connection may already be dead
                pass
            del self._connections[host_key]

    def close_all_connections(self):
        """Close all pooled connections"""
        for client in self._connections.values():
            try:
                client.close()
            except Exception:  # nosec B110 - best-effort cleanup during shutdown
                pass
        self._connections.clear()

    def _run_command(
        self,
        client: "paramiko.SSHClient",
        command: str,
        environment: Optional[Dict[str, str]] = None,
        timeout: int = 300
    ) -> Tuple[int, str, str]:
        """
        Run a command on the remote host.

        Args:
            client: SSH client
            command: Command to run
            environment: Optional environment variables
            timeout: Command timeout in seconds

        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        # Ensure basic PATH includes common directories for standard commands
        # This handles cases where non-interactive SSH shells have minimal PATH
        default_path = "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
        path_setup = f"export PATH={default_path}:$PATH"

        # Build environment prefix
        env_parts = [path_setup]  # Start with default PATH
        if environment:
            for k, v in environment.items():
                # Don't quote values that contain shell variables like $PATH
                # as we want them to expand
                if "$" in v:
                    env_parts.append(f"export {k}={v}")
                else:
                    env_parts.append(f"export {k}={shlex.quote(v)}")

        env_prefix = " && ".join(env_parts) + " && "
        full_command = f"{env_prefix}{command}"

        try:
            # Security note: This is intentional remote command execution.
            # Environment values (except shell variables) are sanitized with shlex.quote.
            # The command itself comes from user input and is executed as intended.
            _, stdout, stderr = client.exec_command(full_command, timeout=timeout)  # nosec B601
            exit_code = stdout.channel.recv_exit_status()
            stdout_text = stdout.read().decode("utf-8", errors="replace")
            stderr_text = stderr.read().decode("utf-8", errors="replace")
            return exit_code, stdout_text, stderr_text
        except Exception as e:
            return 1, "", str(e)

    def detect_gpus(self, host_config: SSHHostConfig) -> List[GPUInfo]:
        """
        Detect GPUs on the remote host using nvidia-smi.

        Args:
            host_config: Host configuration

        Returns:
            List of GPUInfo objects
        """
        if not host_config.gpu_enabled:
            return []

        try:
            client = self._get_connection(host_config)
            exit_code, stdout, stderr = self._run_command(
                client,
                "nvidia-smi --query-gpu=index,name,memory.total,memory.used,utilization.gpu --format=csv,noheader,nounits"
            )

            if exit_code != 0:
                if self.verbose:
                    print(f"  GPU detection failed: {stderr}")
                return []

            gpus = []
            for line in stdout.strip().split("\n"):
                if not line.strip():
                    continue
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 5:
                    gpus.append(GPUInfo(
                        index=int(parts[0]),
                        name=parts[1],
                        memory_total=f"{parts[2]} MiB",
                        memory_used=f"{parts[3]} MiB",
                        utilization=f"{parts[4]}%"
                    ))

            return gpus

        except Exception as e:
            if self.verbose:
                print(f"  GPU detection error: {e}")
            return []

    def _transfer_file_samba(
        self,
        host_config: SSHHostConfig,
        local_path: Path,
        direction: str = "upload"
    ) -> Optional[str]:
        """
        Transfer file using Samba share.

        Args:
            host_config: Host configuration with samba_share configured
            local_path: Path to local file
            direction: "upload" or "download"

        Returns:
            Remote path if successful, None if failed
        """
        if not host_config.samba_share:
            return None

        samba = host_config.samba_share
        if not samba.is_available():
            if self.verbose:
                print(f"  Samba share not mounted: {samba.local_mount}")
            return None

        try:
            if direction == "upload":
                # Copy to local mount (which is shared with remote)
                dest_path = Path(samba.local_mount) / local_path.name

                # Security: Prevent path traversal
                if ".." in str(local_path) or ".." in local_path.name:
                    if self.verbose:
                        print(f"  Skipping suspicious path: {local_path}")
                    return None

                import shutil
                shutil.copy2(local_path, dest_path)

                # Return the remote path
                remote_path = f"{samba.remote_path}/{local_path.name}"
                if self.verbose:
                    print(f"  Copied via Samba: {local_path.name} -> {remote_path}")
                return remote_path

            else:  # download
                # File should already be in the shared directory
                local_file = Path(samba.local_mount) / local_path.name
                if local_file.exists():
                    return str(local_file)
                return None

        except Exception as e:
            if self.verbose:
                print(f"  Samba transfer failed: {e}")
            return None

    def _transfer_file_sftp(
        self,
        client: "paramiko.SSHClient",
        local_path: Path,
        remote_path: str,
        direction: str = "upload"
    ) -> bool:
        """
        Transfer file using SFTP.

        Args:
            client: SSH client
            local_path: Path to local file
            remote_path: Path on remote host
            direction: "upload" or "download"

        Returns:
            True if successful
        """
        try:
            sftp = client.open_sftp()
            try:
                if direction == "upload":
                    sftp.put(str(local_path), remote_path)
                    if self.verbose:
                        print(f"  SFTP uploaded: {local_path.name} -> {remote_path}")
                else:  # download
                    sftp.get(remote_path, str(local_path))
                    if self.verbose:
                        print(f"  SFTP downloaded: {remote_path} -> {local_path.name}")
                return True
            finally:
                sftp.close()
        except Exception as e:
            if self.verbose:
                print(f"  SFTP transfer failed: {e}")
            return False

    def upload_file(
        self,
        host_config: SSHHostConfig,
        local_path: Path,
        remote_dir: str = "/tmp"  # nosec B108 - remote temp dir is appropriate for SSH uploads
    ) -> Optional[str]:
        """
        Upload a file to the remote host.

        Uses Samba share if available, falls back to SFTP.

        Args:
            host_config: Host configuration
            local_path: Path to local file
            remote_dir: Remote directory for SFTP fallback (on remote host)

        Returns:
            Remote path if successful, None if failed
        """
        # Security check
        if not local_path.exists() or not local_path.is_file():
            if self.verbose:
                print(f"  File not found: {local_path}")
            return None

        if ".." in str(local_path):
            if self.verbose:
                print(f"  Skipping suspicious path: {local_path}")
            return None

        # Try Samba first
        if host_config.samba_share:
            remote_path = self._transfer_file_samba(host_config, local_path, "upload")
            if remote_path:
                return remote_path

        # Fallback to SFTP
        client = self._get_connection(host_config)
        remote_path = f"{remote_dir}/{local_path.name}"
        if self._transfer_file_sftp(client, local_path, remote_path, "upload"):
            return remote_path

        return None

    def _build_agent_command(
        self,
        agent: str,
        prompt: str,
        model: Optional[str] = None,
        file_paths: Optional[List[str]] = None
    ) -> str:
        """
        Build command for AI agent execution.

        Args:
            agent: Agent name ("claude", "gemini", "codex")
            prompt: User prompt
            model: Optional model override
            file_paths: Optional list of remote file paths

        Returns:
            Shell command string
        """
        # Handle file context
        if file_paths:
            file_list = ", ".join([Path(fp).name for fp in file_paths])
            file_context = f"\n\nFiles available: {file_list}"
            prompt = prompt + file_context

        # Escape prompt for shell
        safe_prompt = shlex.quote(prompt)

        if agent == "claude":
            model_flag = f"--model {model}" if model else ""
            return f"claude -p --dangerously-skip-permissions {safe_prompt} {model_flag}".strip()

        elif agent == "gemini":
            model_flag = f"--model {model}" if model else ""
            return f"gemini -y -p {safe_prompt} {model_flag}".strip()

        elif agent == "codex":
            return f"codex exec --full-auto --sandbox danger-full-access --skip-git-repo-check {safe_prompt}".strip()

        else:
            raise ValueError(f"Unknown agent: {agent}")

    def execute(
        self,
        host_name: str,
        prompt: str,
        agent: Optional[str] = None,
        model: Optional[str] = None,
        working_dir: Optional[str] = None,
        auto_close: bool = True
    ) -> dict:
        """
        Execute a command or AI agent on a remote SSH host.

        Args:
            host_name: Name of configured SSH host
            prompt: The command or prompt to execute
            agent: Agent name ("claude", "gemini", "codex") or None for raw command
            model: Optional model override for agents
            working_dir: Local working directory for file resolution
            auto_close: Close connection after execution (default: True)

        Returns:
            Dictionary with execution results
        """
        result = {
            "success": False,
            "output": "",
            "error": None,
            "host": host_name,
            "gpu_info": [],
            "files_transferred": []
        }

        # Load host configuration
        host_config = self.config_manager.get_host(host_name)
        if not host_config:
            result["error"] = f"SSH host '{host_name}' not configured.\n"
            result["error"] += f"Add it to: {self.config_manager.config_path}"
            return result

        try:
            if self.verbose:
                print(f"\nSSH Execution on {host_name}")
                print(f"  Host: {host_config.user}@{host_config.hostname}:{host_config.port}")

            # Connect
            client = self._get_connection(host_config)

            # Detect GPUs if enabled
            if host_config.gpu_enabled:
                gpus = self.detect_gpus(host_config)
                result["gpu_info"] = gpus
                if gpus and self.verbose:
                    print(f"  GPUs detected: {len(gpus)}")
                    for gpu in gpus:
                        print(f"    [{gpu.index}] {gpu.name} - {gpu.memory_used}/{gpu.memory_total} ({gpu.utilization})")

            # Build environment
            env = dict(host_config.environment)

            # Add CUDA path if configured
            if host_config.cuda_path:
                existing_path = env.get("PATH", "$PATH")
                env["PATH"] = f"{host_config.cuda_path}/bin:{existing_path}"
                env["LD_LIBRARY_PATH"] = f"{host_config.cuda_path}/lib64:$LD_LIBRARY_PATH"

            # Handle agent execution
            if agent:
                if self.verbose:
                    print(f"  Agent: {agent}")
                    print(f"  Prompt: {prompt[:100]}..." if len(prompt) > 100 else f"  Prompt: {prompt}")

                # Resolve agent credential
                try:
                    api_key = self.resolver.get_credential(agent, verbose=False)
                except CredentialNotFoundError as e:
                    result["error"] = str(e)
                    return result

                # Inject API key into environment
                key_name = self.resolver.AGENT_KEY_MAP[agent]
                env[key_name] = api_key

                # For codex, also set OPENAI_API_KEY
                if agent == "codex":
                    env["OPENAI_API_KEY"] = api_key

                # Build agent command
                command = self._build_agent_command(agent, prompt, model)

            else:
                # Raw command execution
                command = prompt
                if self.verbose:
                    print(f"  Command: {command}")

            # Execute
            if self.verbose:
                print(f"\n  Executing...")

            exit_code, stdout, stderr = self._run_command(
                client,
                command,
                environment=env,
                timeout=300
            )

            result["success"] = exit_code == 0
            result["output"] = stdout
            if stderr:
                result["error"] = stderr

            if self.verbose:
                if stdout:
                    print(f"\n[Output]\n{stdout}")
                if stderr:
                    print(f"\n[Error]\n{stderr}")
                print(f"\nExit code: {exit_code}")

        except Exception as e:
            result["error"] = f"SSH execution failed: {str(e)}"
            if self.verbose:
                print(f"  Error: {e}")

        finally:
            if auto_close:
                self._close_connection(host_config)

        return result


def execute_on_ssh(
    host_name: str,
    prompt: str,
    agent: Optional[str] = None,
    verbose: bool = True
) -> dict:
    """
    Convenience function to execute on SSH host.

    Args:
        host_name: Name of configured SSH host
        prompt: Command or prompt to execute
        agent: Optional agent name
        verbose: Print status messages

    Returns:
        Execution result dictionary
    """
    backend = SSHBackend(verbose=verbose)
    return backend.execute(host_name, prompt, agent=agent)


if __name__ == "__main__":
    # Test SSH backend
    import sys

    if len(sys.argv) < 3:
        print("Usage: python ssh_backend.py <host> <command>")
        print("       python ssh_backend.py <host> --agent <agent> <prompt>")
        print()
        print("Examples:")
        print("  python ssh_backend.py dgx hostname")
        print("  python ssh_backend.py dgx nvidia-smi")
        print("  python ssh_backend.py dgx --agent claude 'explain python decorators'")
        print()

        # Show configured hosts
        config_manager = SSHHostConfigManager()
        hosts = config_manager.list_hosts()
        if hosts:
            print(f"Configured hosts: {', '.join(hosts)}")
        else:
            print(f"No hosts configured in: {config_manager.config_path}")
            print("\nCreate config file with:")
            from ssh_host_config import create_example_config
            print(create_example_config())
        sys.exit(1)

    host_name = sys.argv[1]
    agent = None
    prompt_args = sys.argv[2:]

    # Check for --agent flag
    if "--agent" in prompt_args:
        idx = prompt_args.index("--agent")
        if idx + 1 < len(prompt_args):
            agent = prompt_args[idx + 1]
            prompt_args = prompt_args[:idx] + prompt_args[idx + 2:]

    prompt = " ".join(prompt_args)

    print(f"Testing SSH execution: {host_name}")
    if agent:
        print(f"Agent: {agent}")
    print(f"Command: {prompt}")
    print()

    result = execute_on_ssh(host_name, prompt, agent=agent)

    print("\n" + "=" * 60)
    print("RESULT:")
    print("=" * 60)
    print(f"Success: {result['success']}")
    print(f"Host: {result['host']}")
    if result['gpu_info']:
        print(f"GPUs: {len(result['gpu_info'])}")
    if result['output']:
        print(f"\nOutput:\n{result['output']}")
    if result['error']:
        print(f"\nError:\n{result['error']}")
