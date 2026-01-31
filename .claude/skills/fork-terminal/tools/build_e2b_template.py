#!/usr/bin/env python3
"""
Build Custom E2B Template with AI Agent CLIs

Creates an E2B sandbox template with Claude Code, Gemini CLI, and Codex CLI pre-installed.
This template can then be used to spawn sandboxes with these tools already available.
"""

import os
import sys
from pathlib import Path

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent))

from credential_resolver import CredentialResolver, CredentialNotFoundError


def build_template():
    """Build custom E2B template with AI agent CLIs installed"""

    print("="*70)
    print("Building Custom E2B Template: Fork Terminal AI Agents")
    print("="*70)

    # Ensure E2B SDK is available
    try:
        from e2b import Sandbox
    except ImportError:
        print("\n❌ E2B SDK not installed.")
        print("Install it with: pip install -r requirements.txt")
        sys.exit(1)

    # Resolve E2B API key
    resolver = CredentialResolver()
    try:
        e2b_key = resolver.get_credential("e2b", verbose=True)
        os.environ['E2B_API_KEY'] = e2b_key
    except CredentialNotFoundError as e:
        print(f"\n❌ {e}")
        sys.exit(1)

    print("\n" + "="*70)
    print("Step 1: Creating base sandbox for template building")
    print("="*70)

    # Create a base sandbox for installing tools
    sandbox = Sandbox.create()
    print(f"✓ Base sandbox created: {sandbox.sandbox_id}")

    print("\n" + "="*70)
    print("Step 2: Installing AI Agent CLIs in sandbox")
    print("="*70)

    # Installation script for all AI agent CLIs
    install_script = """
#!/bin/bash
set -e

echo "📦 Updating system packages..."
apt-get update -qq
apt-get install -y -qq curl wget git python3 python3-pip nodejs npm > /dev/null 2>&1

echo "✓ System packages installed"

# Install Claude Code CLI
echo "📦 Installing Claude Code CLI..."
if ! command -v claude &> /dev/null; then
    # Claude Code installation (assuming official install method)
    npm install -g @anthropic-ai/claude-code 2>/dev/null || \
    pip3 install anthropic-claude-code 2>/dev/null || \
    curl -fsSL https://claude.ai/install-cli.sh | bash 2>/dev/null || \
    echo "⚠️  Claude Code CLI installation method not available - will use API fallback"
fi
if command -v claude &> /dev/null; then
    echo "✓ Claude Code CLI installed: $(claude --version 2>/dev/null || echo 'version unknown')"
else
    echo "⚠️  Claude Code CLI not installed - will use alternative method"
fi

# Install Gemini CLI
echo "📦 Installing Gemini CLI..."
if ! command -v gemini &> /dev/null; then
    # Gemini CLI installation (check official installation)
    npm install -g @google/generative-ai-cli 2>/dev/null || \
    pip3 install google-generativeai-cli 2>/dev/null || \
    echo "⚠️  Gemini CLI installation method not available - will use API fallback"
fi
if command -v gemini &> /dev/null; then
    echo "✓ Gemini CLI installed: $(gemini --version 2>/dev/null || echo 'version unknown')"
else
    echo "⚠️  Gemini CLI not installed - will use alternative method"
fi

# Install Codex CLI
echo "📦 Installing Codex/OpenAI CLI..."
if ! command -v codex &> /dev/null; then
    # OpenAI CLI installation
    pip3 install openai-cli 2>/dev/null || \
    npm install -g openai-cli 2>/dev/null || \
    echo "⚠️  Codex CLI installation method not available - will use API fallback"
fi
if command -v codex &> /dev/null; then
    echo "✓ Codex CLI installed: $(codex --version 2>/dev/null || echo 'version unknown')"
else
    echo "⚠️  Codex CLI not installed - will use alternative method"
fi

# Install Python API libraries as fallback
echo "📦 Installing Python API libraries (fallback)..."
pip3 install -q anthropic google-generativeai openai

echo ""
echo "✅ Installation complete!"
echo ""
echo "Installed tools:"
command -v claude &> /dev/null && echo "  ✓ claude: $(which claude)" || echo "  ✗ claude (using anthropic API)"
command -v gemini &> /dev/null && echo "  ✓ gemini: $(which gemini)" || echo "  ✗ gemini (using google-generativeai API)"
command -v codex &> /dev/null && echo "  ✓ codex: $(which codex)" || echo "  ✗ codex (using openai API)"
echo "  ✓ Python APIs: anthropic, google-generativeai, openai"
"""

    print("\n📝 Running installation script in sandbox...\n")

    # Write installation script to sandbox (E2B sandbox /tmp is isolated)
    sandbox.files.write("/tmp/install_agents.sh", install_script)  # nosec B108

    # Make it executable and run it
    result = sandbox.commands.run("chmod +x /tmp/install_agents.sh && /tmp/install_agents.sh")

    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(f"[stderr] {result.stderr}")

    if result.exit_code != 0:
        print(f"\n⚠️  Installation completed with exit code {result.exit_code}")
        print("Some CLIs may not be available, but API fallbacks are installed.")
    else:
        print("\n✅ All installations successful!")

    print("\n" + "="*70)
    print("Step 3: Creating E2B template from configured sandbox")
    print("="*70)

    # Note: E2B template creation from existing sandbox
    # This requires E2B's template builder API which may differ
    print("\n⚠️  IMPORTANT: E2B template creation requires:")
    print("1. E2B Pro/Team account with template building permissions")
    print("2. Using E2B's template builder API or CLI")
    print("3. Saving the template ID for reuse")

    print(f"\nCurrent sandbox ID: {sandbox.sandbox_id}")
    print("\nTo create a template from this sandbox:")
    print(f"1. Keep this sandbox running (don't kill it)")
    print(f"2. Use E2B dashboard or CLI to save sandbox as template")
    print(f"3. Name the template: 'fork-terminal-ai-agents'")
    print(f"4. Save the template ID to: .e2b_template_id")

    print("\nPress Enter when you've created the template, or Ctrl+C to cancel...")
    try:
        input()

        template_id = input("\nEnter the template ID you created: ").strip()
        if template_id:
            # Save template ID to file
            template_file = Path(__file__).parent / ".e2b_template_id"
            template_file.write_text(template_id)
            print(f"\n✅ Template ID saved to: {template_file}")
            print(f"Template ID: {template_id}")

    except KeyboardInterrupt:
        print("\n\n⚠️  Template creation cancelled")

    finally:
        print(f"\n🔒 Cleaning up sandbox...")
        sandbox.kill()
        print("✓ Sandbox terminated")

    print("\n" + "="*70)
    print("Template Building Process Complete!")
    print("="*70)
    print("\nNext steps:")
    print("1. Verify template ID is saved in .e2b_template_id")
    print("2. Test the template with: python test_template.py")
    print("3. Update sandbox_backend.py to use the template")


if __name__ == "__main__":
    try:
        build_template()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
