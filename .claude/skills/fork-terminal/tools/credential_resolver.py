"""
Credential Resolution with Waterfall Priority

Resolves credentials for AI agents using a priority-based waterfall:
1. Environment variables (highest priority)
2. .env file
3. System keychain (macOS/Windows/Linux)
4. Tool-specific config files (lowest priority)

SSH Key Resolution Waterfall:
1. Explicit key_path parameter
2. Host config key_path from ssh_hosts.yaml
3. SSH_DEFAULT_KEY_PATH environment variable
4. ~/.ssh/id_ed25519 (preferred)
5. ~/.ssh/id_rsa (fallback)
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Optional, Tuple


class CredentialNotFoundError(Exception):
    """Raised when a credential cannot be found in any source"""
    pass


class CredentialResolver:
    """Resolves credentials using waterfall priority system"""

    # Map agent names to their credential environment variable names
    AGENT_KEY_MAP = {
        "claude": "ANTHROPIC_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "codex": "OPENAI_API_KEY",
        "e2b": "E2B_API_KEY"
    }

    # Map agents to their config file locations
    CONFIG_PATHS = {
        "claude": "~/.anthropic/api_key",
        "gemini": "~/.config/gemini/credentials.json",
        "codex": "~/.openai/api_key",
        "e2b": "~/.e2b/api_key"
    }

    def get_credential(self, agent: str, verbose: bool = True) -> str:
        """
        Waterfall resolution for agent credentials

        Args:
            agent: Agent name ("claude", "gemini", "codex", "e2b")
            verbose: Print resolution status messages

        Returns:
            The credential value

        Raises:
            ValueError: If agent is unknown
            CredentialNotFoundError: If credential not found in any source
        """
        key_name = self.AGENT_KEY_MAP.get(agent)
        if not key_name:
            raise ValueError(
                f"Unknown agent: {agent}. "
                f"Supported: {', '.join(self.AGENT_KEY_MAP.keys())}"
            )

        # 1. Check environment variable
        credential = os.getenv(key_name)
        if credential:
            if verbose:
                print(f"✓ Found {key_name} in environment variables")
            return credential

        # 2. Check .env file
        credential = self._get_from_env_file(key_name)
        if credential:
            if verbose:
                print(f"✓ Found {key_name} in .env file")
            return credential

        # 3. Check system keychain
        credential = self._get_from_keychain(key_name)
        if credential:
            if verbose:
                print(f"✓ Found {key_name} in system keychain")
            return credential

        # 4. Check tool-specific config files
        credential = self._get_from_config_file(agent, key_name)
        if credential:
            if verbose:
                print(f"✓ Found {key_name} in {self.CONFIG_PATHS[agent]}")
            return credential

        # Not found in any source
        raise CredentialNotFoundError(
            f"Credential not found for {agent} ({key_name}).\n"
            f"Checked:\n"
            f"  1. Environment variable: ${key_name}\n"
            f"  2. .env file\n"
            f"  3. System keychain\n"
            f"  4. Config file: {self.CONFIG_PATHS.get(agent, 'N/A')}\n\n"
            f"Please set {key_name} in one of these locations."
        )

    def _get_from_keychain(self, key_name: str) -> Optional[str]:
        """Get credential from system keychain (macOS/Windows/Linux)"""
        try:
            if sys.platform == "darwin":  # macOS
                result = subprocess.run(
                    ["security", "find-generic-password", "-s", key_name, "-w"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    return result.stdout.strip()

            elif sys.platform == "win32":  # Windows
                # TODO: Implement Windows Credential Manager integration
                # Could use: https://github.com/jaraco/keyring
                pass

            else:  # Linux
                # TODO: Implement Linux Secret Service integration
                # Could use: https://github.com/jaraco/keyring
                pass

        except Exception:
            # Silently fail and try next source
            pass

        return None

    def _get_from_env_file(self, key_name: str) -> Optional[str]:
        """Get credential from .env file in current directory"""
        env_path = Path(".env")
        if not env_path.exists():
            return None

        try:
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if not line or line.startswith("#"):
                        continue
                    # Check for key=value format
                    if line.startswith(f"{key_name}="):
                        value = line.split("=", 1)[1].strip()
                        # Remove quotes if present
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        if value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        # Don't return placeholder values
                        if "your_" in value.lower() or "_here" in value.lower():
                            continue
                        return value
        except Exception:
            # Silently fail and try next source
            pass

        return None

    def _get_from_config_file(self, agent: str, key_name: str) -> Optional[str]:
        """Get credential from tool-specific config file"""
        config_path_str = self.CONFIG_PATHS.get(agent)
        if not config_path_str:
            return None

        config_path = Path(config_path_str).expanduser()
        if not config_path.exists():
            return None

        try:
            if config_path.suffix == ".json":
                # JSON file (e.g., Gemini)
                with open(config_path) as f:
                    data = json.load(f)
                    # Try multiple possible JSON key names
                    return (
                        data.get("api_key") or
                        data.get(key_name) or
                        data.get(key_name.lower())
                    )
            else:
                # Plain text file
                content = config_path.read_text().strip()
                # Don't return placeholder values
                if "your_" in content.lower() or "_here" in content.lower():
                    return None
                return content
        except Exception:
            # Silently fail - credential not available from this source
            pass

        return None

    def get_all_available_credentials(self) -> dict[str, bool]:
        """
        Check which credentials are available

        Returns:
            Dictionary mapping agent names to availability (True/False)
        """
        available = {}
        for agent in self.AGENT_KEY_MAP.keys():
            try:
                self.get_credential(agent, verbose=False)
                available[agent] = True
            except CredentialNotFoundError:
                available[agent] = False
        return available

    # SSH Key Resolution Methods

    def get_ssh_key_path(
        self,
        explicit_path: Optional[str] = None,
        host_config_path: Optional[str] = None,
        verbose: bool = True
    ) -> Tuple[Path, str]:
        """
        Waterfall resolution for SSH private key path.

        Priority order:
        1. Explicit key_path parameter
        2. Host config key_path (from ssh_hosts.yaml)
        3. SSH_DEFAULT_KEY_PATH environment variable
        4. ~/.ssh/id_ed25519 (preferred)
        5. ~/.ssh/id_rsa (fallback)

        Args:
            explicit_path: Explicitly provided key path (highest priority)
            host_config_path: Key path from SSH host config
            verbose: Print resolution status messages

        Returns:
            Tuple of (Path to SSH key, source description)

        Raises:
            CredentialNotFoundError: If no valid SSH key found
        """
        # 1. Explicit key path
        if explicit_path:
            key_path = Path(explicit_path).expanduser()
            if key_path.exists():
                if verbose:
                    print(f"  Using explicit SSH key: {key_path}")
                return key_path, "explicit parameter"

        # 2. Host config key path
        if host_config_path:
            key_path = Path(host_config_path).expanduser()
            if key_path.exists():
                if verbose:
                    print(f"  Using host config SSH key: {key_path}")
                return key_path, "host config"

        # 3. SSH_DEFAULT_KEY_PATH environment variable
        env_key_path = os.getenv("SSH_DEFAULT_KEY_PATH")
        if env_key_path:
            key_path = Path(env_key_path).expanduser()
            if key_path.exists():
                if verbose:
                    print(f"  Using SSH key from SSH_DEFAULT_KEY_PATH: {key_path}")
                return key_path, "SSH_DEFAULT_KEY_PATH env var"

        # 4. Default SSH key locations
        ssh_dir = Path.home() / ".ssh"

        # Try ed25519 first (preferred)
        ed25519_key = ssh_dir / "id_ed25519"
        if ed25519_key.exists():
            if verbose:
                print(f"  Using default SSH key: {ed25519_key}")
            return ed25519_key, "~/.ssh/id_ed25519"

        # Try RSA as fallback
        rsa_key = ssh_dir / "id_rsa"
        if rsa_key.exists():
            if verbose:
                print(f"  Using default SSH key: {rsa_key}")
            return rsa_key, "~/.ssh/id_rsa"

        # No key found
        raise CredentialNotFoundError(
            "SSH private key not found.\n"
            "Checked locations:\n"
            f"  1. Explicit key_path: {explicit_path or 'not provided'}\n"
            f"  2. Host config key_path: {host_config_path or 'not provided'}\n"
            f"  3. SSH_DEFAULT_KEY_PATH env var: {env_key_path or 'not set'}\n"
            f"  4. ~/.ssh/id_ed25519: not found\n"
            f"  5. ~/.ssh/id_rsa: not found\n\n"
            "Please configure an SSH key in one of these locations."
        )

    def get_ssh_passphrase(
        self,
        key_path: Path,
        verbose: bool = True
    ) -> Optional[str]:
        """
        Get SSH key passphrase from system keychain (macOS).

        On macOS, SSH passphrases can be stored in the keychain.
        This method attempts to retrieve them.

        Args:
            key_path: Path to the SSH private key
            verbose: Print resolution status messages

        Returns:
            Passphrase string or None if not found/not needed
        """
        if sys.platform != "darwin":
            # Only macOS keychain integration is implemented
            return None

        try:
            # macOS stores SSH passphrases with the key path as the "account"
            # and "SSH" as the service name
            result = subprocess.run(
                [
                    "security", "find-generic-password",
                    "-s", "SSH",
                    "-a", str(key_path),
                    "-w"
                ],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                passphrase = result.stdout.strip()
                if passphrase:
                    if verbose:
                        print(f"  Found SSH passphrase in keychain for: {key_path.name}")
                    return passphrase

        except Exception:
            # Silently fail - key may not require passphrase
            pass

        return None

    def check_ssh_key_encrypted(self, key_path: Path) -> bool:
        """
        Check if an SSH private key is encrypted (requires passphrase).

        Args:
            key_path: Path to the SSH private key

        Returns:
            True if key is encrypted, False otherwise
        """
        try:
            content = key_path.read_text()
            # Check for encryption markers in OpenSSH format
            return "ENCRYPTED" in content or "Proc-Type: 4,ENCRYPTED" in content
        except Exception:
            return False

    def validate_ssh_key(self, key_path: Path, passphrase: Optional[str] = None) -> bool:
        """
        Validate that an SSH key is usable.

        Args:
            key_path: Path to the SSH private key
            passphrase: Optional passphrase for encrypted keys

        Returns:
            True if key is valid and usable
        """
        try:
            # Use ssh-keygen to check key validity
            cmd = ["ssh-keygen", "-y", "-f", str(key_path)]

            if passphrase:
                # Pass passphrase via stdin
                result = subprocess.run(
                    cmd,
                    input=passphrase,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
            else:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=5
                )

            return result.returncode == 0

        except Exception:
            return False


# Convenience function for quick resolution
def get_credential(agent: str) -> str:
    """
    Quick credential resolution

    Args:
        agent: Agent name ("claude", "gemini", "codex", "e2b")

    Returns:
        The credential value

    Raises:
        CredentialNotFoundError: If credential not found
    """
    resolver = CredentialResolver()
    return resolver.get_credential(agent)


if __name__ == "__main__":
    # Test credential resolution
    print("Testing credential resolution...\n")

    resolver = CredentialResolver()
    available = resolver.get_all_available_credentials()

    print("Available credentials:")
    for agent, is_available in available.items():
        status = "✓" if is_available else "✗"
        print(f"  {status} {agent.upper()}: {is_available}")

    print("\nTrying to resolve each credential:")
    for agent in resolver.AGENT_KEY_MAP.keys():
        try:
            credential = resolver.get_credential(agent)
            print(f"  {agent}: {credential[:10]}..." if len(credential) > 10 else f"  {agent}: {credential}")
        except CredentialNotFoundError:
            print(f"  {agent}: Not found")

    # Test SSH key resolution
    print("\nTesting SSH key resolution:")
    try:
        key_path, source = resolver.get_ssh_key_path()
        print(f"  SSH key found: {key_path}")
        print(f"  Source: {source}")
        if resolver.check_ssh_key_encrypted(key_path):
            print("  Key is encrypted (passphrase required)")
            passphrase = resolver.get_ssh_passphrase(key_path)
            if passphrase:
                print("  Passphrase found in keychain")
            else:
                print("  Passphrase not found in keychain")
        else:
            print("  Key is not encrypted")
    except CredentialNotFoundError:
        print("  No SSH key found")
