#!/usr/bin/env python3
"""
Environment Setup for Fork Terminal Skill

Ensures a virtual environment exists with all required dependencies.
Creates one automatically if missing. Prefers uv if available for speed.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

# Directory where this script lives (tools/)
TOOLS_DIR = Path(__file__).parent.resolve()
VENV_DIR = TOOLS_DIR / ".venv"
REQUIREMENTS_FILE = TOOLS_DIR / "requirements.txt"

# Marker file to track if dependencies are installed
DEPS_MARKER = VENV_DIR / ".deps_installed"


def get_venv_python() -> Path:
    """Get path to Python in the virtual environment"""
    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def get_venv_pip() -> Path:
    """Get path to pip in the virtual environment"""
    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "pip.exe"
    return VENV_DIR / "bin" / "pip"


def has_uv() -> bool:
    """Check if uv is available"""
    return shutil.which("uv") is not None


def is_running_in_venv() -> bool:
    """Check if we're already running in the skill's venv"""
    current_venv = os.environ.get("VIRTUAL_ENV", "")
    return current_venv == str(VENV_DIR)


def venv_exists() -> bool:
    """Check if virtual environment exists and is valid"""
    return get_venv_python().exists()


def deps_installed() -> bool:
    """Check if dependencies have been installed"""
    if not DEPS_MARKER.exists():
        return False

    # Check if requirements.txt is newer than marker
    if REQUIREMENTS_FILE.exists():
        req_mtime = REQUIREMENTS_FILE.stat().st_mtime
        marker_mtime = DEPS_MARKER.stat().st_mtime
        if req_mtime > marker_mtime:
            return False

    return True


def create_venv_with_uv() -> bool:
    """Create virtual environment using uv (fast)"""
    print(f"📦 Creating virtual environment with uv at {VENV_DIR}...")
    try:
        subprocess.run(
            ["uv", "venv", str(VENV_DIR)],
            check=True,
            capture_output=True,
            text=True
        )
        print("✅ Virtual environment created (uv)")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create virtual environment with uv: {e.stderr}")
        return False


def create_venv_with_venv() -> bool:
    """Create virtual environment using standard venv"""
    print(f"📦 Creating virtual environment with venv at {VENV_DIR}...")
    try:
        subprocess.run(
            [sys.executable, "-m", "venv", str(VENV_DIR)],
            check=True,
            capture_output=True,
            text=True
        )
        print("✅ Virtual environment created (venv)")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create virtual environment: {e.stderr}")
        return False


def create_venv() -> bool:
    """Create virtual environment, preferring uv if available"""
    if has_uv():
        return create_venv_with_uv()
    return create_venv_with_venv()


def install_dependencies_with_uv() -> bool:
    """Install dependencies using uv (fast)"""
    print(f"📥 Installing dependencies with uv from {REQUIREMENTS_FILE.name}...")
    try:
        result = subprocess.run(
            ["uv", "pip", "install", "-r", str(REQUIREMENTS_FILE), "-p", str(get_venv_python())],
            check=True,
            capture_output=True,
            text=True
        )
        DEPS_MARKER.touch()
        print("✅ Dependencies installed (uv)")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies with uv:")
        print(e.stderr)
        return False


def install_dependencies_with_pip() -> bool:
    """Install dependencies using pip"""
    print(f"📥 Installing dependencies with pip from {REQUIREMENTS_FILE.name}...")
    pip_path = get_venv_pip()

    try:
        # Upgrade pip first
        subprocess.run(
            [str(pip_path), "install", "--upgrade", "pip"],
            check=True,
            capture_output=True,
            text=True
        )

        # Install requirements
        result = subprocess.run(
            [str(pip_path), "install", "-r", str(REQUIREMENTS_FILE)],
            check=True,
            capture_output=True,
            text=True
        )

        DEPS_MARKER.touch()
        print("✅ Dependencies installed (pip)")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies with pip:")
        print(e.stderr)
        return False


def install_dependencies() -> bool:
    """Install dependencies from requirements.txt, preferring uv if available"""
    if not REQUIREMENTS_FILE.exists():
        print("⚠️  No requirements.txt found, skipping dependency installation")
        DEPS_MARKER.touch()
        return True

    if has_uv():
        return install_dependencies_with_uv()
    return install_dependencies_with_pip()


def ensure_environment() -> tuple[bool, Path]:
    """
    Ensure virtual environment exists with all dependencies.

    Returns:
        Tuple of (success, python_path)
    """
    # Check if venv exists
    if not venv_exists():
        if not create_venv():
            return False, Path()

    # Check if deps are installed
    if not deps_installed():
        if not install_dependencies():
            return False, Path()

    return True, get_venv_python()


def run_in_venv(script_path: str, args: list[str] = None) -> int:
    """
    Run a Python script in the skill's virtual environment.

    Args:
        script_path: Path to the script to run
        args: Command line arguments

    Returns:
        Exit code from the script
    """
    if args is None:
        args = []

    # Ensure environment is ready
    success, python_path = ensure_environment()
    if not success:
        return 1

    # Run the script
    cmd = [str(python_path), script_path] + args
    result = subprocess.run(cmd)
    return result.returncode


def activate_venv():
    """
    Activate the virtual environment for the current process.

    This modifies sys.path and environment variables to use the venv.
    Should be called at the start of scripts that need the venv.
    """
    if is_running_in_venv():
        return True

    # Ensure environment exists
    success, python_path = ensure_environment()
    if not success:
        return False

    # Get the site-packages directory
    if sys.platform == "win32":
        site_packages = VENV_DIR / "Lib" / "site-packages"
    else:
        # Find the python version directory
        lib_dir = VENV_DIR / "lib"
        if lib_dir.exists():
            python_dirs = list(lib_dir.glob("python*"))
            if python_dirs:
                site_packages = python_dirs[0] / "site-packages"
            else:
                print("❌ Could not find site-packages in venv")
                return False
        else:
            print("❌ Virtual environment lib directory not found")
            return False

    if not site_packages.exists():
        print(f"❌ Site-packages not found: {site_packages}")
        return False

    # Add to sys.path at the beginning
    site_packages_str = str(site_packages)
    if site_packages_str not in sys.path:
        sys.path.insert(0, site_packages_str)

    # Set environment variable
    os.environ["VIRTUAL_ENV"] = str(VENV_DIR)

    return True


if __name__ == "__main__":
    # When run directly, ensure environment is set up
    print(f"🔧 Fork Terminal Environment Setup")
    print(f"   Tools dir: {TOOLS_DIR}")
    print(f"   Using: {'uv' if has_uv() else 'pip'}")
    print()

    success, python_path = ensure_environment()
    if success:
        print(f"\n✅ Environment ready: {python_path}")
        sys.exit(0)
    else:
        print("\n❌ Failed to set up environment")
        sys.exit(1)
