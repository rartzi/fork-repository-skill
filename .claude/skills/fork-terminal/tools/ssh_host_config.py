"""
SSH Host Configuration Manager

Loads and manages SSH host configurations from ~/.config/fork-terminal/ssh_hosts.yaml
Supports multiple named hosts with GPU settings and Samba share paths for file exchange.
"""

from pathlib import Path
from typing import Optional, Dict
from dataclasses import dataclass, field


@dataclass
class SambaShareConfig:
    """Configuration for Samba share file transfer"""
    local_mount: str  # Local mount path (e.g., /Volumes/DGX-Share)
    remote_path: str  # Remote path on host (e.g., /mnt/shared)

    def is_available(self) -> bool:
        """Check if the local mount is accessible"""
        return Path(self.local_mount).exists() and Path(self.local_mount).is_dir()


@dataclass
class SSHHostConfig:
    """Configuration for a single SSH host"""
    name: str
    hostname: str
    port: int = 22
    user: str = "root"
    key_path: Optional[str] = None
    gpu_enabled: bool = False
    cuda_path: Optional[str] = None
    samba_share: Optional[SambaShareConfig] = None
    environment: Dict[str, str] = field(default_factory=dict)

    def get_key_path(self) -> Optional[Path]:
        """Get expanded key path if configured"""
        if self.key_path:
            return Path(self.key_path).expanduser()
        return None


class SSHHostConfigManager:
    """Manages SSH host configurations"""

    DEFAULT_CONFIG_PATH = "~/.config/fork-terminal/ssh_hosts.yaml"

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the config manager.

        Args:
            config_path: Path to config file (defaults to ~/.config/fork-terminal/ssh_hosts.yaml)
        """
        self.config_path = Path(config_path or self.DEFAULT_CONFIG_PATH).expanduser()
        self._hosts: Dict[str, SSHHostConfig] = {}
        self._loaded = False

    def _ensure_loaded(self):
        """Load config if not already loaded"""
        if not self._loaded:
            self.load()

    def load(self) -> bool:
        """
        Load SSH host configurations from YAML file.

        Returns:
            True if config was loaded successfully, False if file doesn't exist
        """
        self._hosts = {}
        self._loaded = True

        if not self.config_path.exists():
            return False

        try:
            import yaml
        except ImportError:
            raise ImportError(
                "PyYAML is required for SSH host configuration.\n"
                "Install with: pip install pyyaml"
            )

        try:
            with open(self.config_path) as f:
                data = yaml.safe_load(f)

            if not data or "hosts" not in data:
                return False

            for name, host_data in data.get("hosts", {}).items():
                if not isinstance(host_data, dict):
                    continue

                # Parse Samba share config if present
                samba_share = None
                if "samba_share" in host_data and host_data["samba_share"]:
                    samba_data = host_data["samba_share"]
                    if isinstance(samba_data, dict) and "local_mount" in samba_data and "remote_path" in samba_data:
                        samba_share = SambaShareConfig(
                            local_mount=samba_data["local_mount"],
                            remote_path=samba_data["remote_path"]
                        )

                self._hosts[name.lower()] = SSHHostConfig(
                    name=name,
                    hostname=host_data.get("hostname", ""),
                    port=host_data.get("port", 22),
                    user=host_data.get("user", "root"),
                    key_path=host_data.get("key_path"),
                    gpu_enabled=host_data.get("gpu_enabled", False),
                    cuda_path=host_data.get("cuda_path"),
                    samba_share=samba_share,
                    environment=host_data.get("environment", {})
                )

            return True

        except Exception as e:
            print(f"Warning: Failed to load SSH config: {e}")
            return False

    def save(self) -> bool:
        """
        Save current host configurations to YAML file.

        Returns:
            True if saved successfully
        """
        try:
            import yaml
        except ImportError:
            raise ImportError(
                "PyYAML is required for SSH host configuration.\n"
                "Install with: pip install pyyaml"
            )

        # Ensure config directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Build data structure
        data = {"hosts": {}}
        for name, host in self._hosts.items():
            host_data = {
                "hostname": host.hostname,
                "port": host.port,
                "user": host.user,
            }

            if host.key_path:
                host_data["key_path"] = host.key_path
            if host.gpu_enabled:
                host_data["gpu_enabled"] = True
            if host.cuda_path:
                host_data["cuda_path"] = host.cuda_path
            if host.samba_share:
                host_data["samba_share"] = {
                    "local_mount": host.samba_share.local_mount,
                    "remote_path": host.samba_share.remote_path
                }
            if host.environment:
                host_data["environment"] = host.environment

            data["hosts"][host.name] = host_data

        try:
            with open(self.config_path, "w") as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
            return True
        except Exception as e:
            print(f"Error saving SSH config: {e}")
            return False

    def get_host(self, name: str) -> Optional[SSHHostConfig]:
        """
        Get configuration for a named host.

        Args:
            name: Host name (case-insensitive)

        Returns:
            SSHHostConfig or None if not found
        """
        self._ensure_loaded()
        return self._hosts.get(name.lower())

    def list_hosts(self) -> list[str]:
        """
        List all configured host names.

        Returns:
            List of host names
        """
        self._ensure_loaded()
        return list(self._hosts.keys())

    def add_host(self, config: SSHHostConfig) -> None:
        """
        Add or update a host configuration.

        Args:
            config: Host configuration to add
        """
        self._ensure_loaded()
        self._hosts[config.name.lower()] = config

    def remove_host(self, name: str) -> bool:
        """
        Remove a host configuration.

        Args:
            name: Host name to remove

        Returns:
            True if removed, False if not found
        """
        self._ensure_loaded()
        name_lower = name.lower()
        if name_lower in self._hosts:
            del self._hosts[name_lower]
            return True
        return False

    def host_exists(self, name: str) -> bool:
        """
        Check if a host is configured.

        Args:
            name: Host name to check

        Returns:
            True if host exists
        """
        self._ensure_loaded()
        return name.lower() in self._hosts


def get_host_config(name: str) -> Optional[SSHHostConfig]:
    """
    Convenience function to get a host configuration.

    Args:
        name: Host name

    Returns:
        SSHHostConfig or None
    """
    manager = SSHHostConfigManager()
    return manager.get_host(name)


def create_example_config() -> str:
    """
    Generate example configuration YAML content.

    Returns:
        Example YAML configuration string
    """
    return """# SSH Host Configuration for Fork Terminal
# Location: ~/.config/fork-terminal/ssh_hosts.yaml

hosts:
  # Example: NVIDIA DGX Workstation
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

  # Example: Remote workstation
  workstation:
    hostname: workstation.local
    port: 22
    user: developer
    key_path: ~/.ssh/id_ed25519
    gpu_enabled: false
    environment:
      PATH: "/opt/tools/bin:$PATH"
"""


if __name__ == "__main__":
    # Test configuration loading
    print("SSH Host Configuration Manager")
    print("=" * 40)

    manager = SSHHostConfigManager()

    if manager.load():
        print(f"Loaded config from: {manager.config_path}")
        hosts = manager.list_hosts()
        if hosts:
            print(f"\nConfigured hosts: {', '.join(hosts)}")
            for name in hosts:
                host = manager.get_host(name)
                if host:
                    print(f"\n  {name}:")
                    print(f"    hostname: {host.hostname}")
                    print(f"    user: {host.user}@{host.port}")
                    print(f"    gpu_enabled: {host.gpu_enabled}")
                    if host.samba_share:
                        print(f"    samba: {host.samba_share.local_mount} -> {host.samba_share.remote_path}")
        else:
            print("No hosts configured.")
    else:
        print(f"No config file found at: {manager.config_path}")
        print("\nExample configuration:")
        print(create_example_config())
