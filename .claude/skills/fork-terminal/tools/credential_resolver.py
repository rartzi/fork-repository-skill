"""
Credential Resolution with Waterfall Priority

Resolves credentials for AI agents using a priority-based waterfall:
1. Environment variables (highest priority)
2. System keychain (macOS/Windows/Linux)
3. .env file
4. Tool-specific config files (lowest priority)
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Optional


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

        # 2. Check system keychain
        credential = self._get_from_keychain(key_name)
        if credential:
            if verbose:
                print(f"✓ Found {key_name} in system keychain")
            return credential

        # 3. Check .env file
        credential = self._get_from_env_file(key_name)
        if credential:
            if verbose:
                print(f"✓ Found {key_name} in .env file")
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
            f"  2. System keychain\n"
            f"  3. .env file\n"
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
        except CredentialNotFoundError as e:
            print(f"  {agent}: Not found")
