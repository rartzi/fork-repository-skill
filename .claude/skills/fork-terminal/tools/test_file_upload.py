#!/usr/bin/env python3
"""
Test File Upload Functionality for E2B Sandboxes

Tests that local files can be uploaded to sandboxes and accessed by agents.
"""

import sys
import os
from pathlib import Path

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent))

from sandbox_backend import SandboxBackend


def test_file_upload():
    """Test uploading SKILL.MD to sandbox and analyzing it"""

    print("=" * 80)
    print("  TEST: File Upload to E2B Sandbox")
    print("=" * 80)

    # Change to the skill directory
    skill_dir = Path(__file__).parent.parent
    os.chdir(skill_dir)

    print(f"\n📂 Working directory: {os.getcwd()}")
    print(f"📄 Testing with file: SKILL.md")

    # Verify file exists
    if not Path("SKILL.md").exists():
        print("❌ SKILL.md not found in current directory")
        return False

    print(f"✓ File exists ({Path('SKILL.md').stat().st_size} bytes)")

    # Create sandbox backend
    backend = SandboxBackend(verbose=True)

    # Test prompt that references the local file
    prompt = "analyze my SKILL.md file and tell me what this skill does in one sentence"

    print(f"\n📝 Test Prompt:")
    print(f"   '{prompt}'")
    print()

    # Execute in sandbox with file upload
    result = backend.execute_agent(
        agent="gemini",
        prompt=prompt,
        auto_close=True,
        working_dir=str(skill_dir)
    )

    print("\n" + "=" * 80)
    print("  RESULT")
    print("=" * 80)

    if result["success"]:
        print(f"\n✅ SUCCESS")
        print(f"\n📤 File Upload: VERIFIED")
        print(f"🔍 Analysis Result:")
        print(f"\n{result['output']}\n")
        return True
    else:
        print(f"\n❌ FAILED")
        print(f"Error: {result.get('error', 'Unknown error')}")
        return False


if __name__ == "__main__":
    success = test_file_upload()
    sys.exit(0 if success else 1)
