#!/bin/bash
# Build E2B Template for Fork Terminal AI Agents

set -e

echo "======================================================================"
echo "Building E2B Template: Fork Terminal AI Agents"
echo "======================================================================"

# Check if E2B CLI is installed
if ! command -v e2b &> /dev/null; then
    echo "❌ E2B CLI not found"
    echo ""
    echo "Install it with:"
    echo "  npm install -g @e2b/cli"
    echo ""
    echo "Or using npx (no install needed):"
    echo "  npx -y @e2b/cli template build"
    exit 1
fi

# Check if logged in
if ! e2b auth whoami &> /dev/null; then
    echo "❌ Not logged in to E2B"
    echo ""
    echo "Login with:"
    echo "  e2b login"
    exit 1
fi

echo "✓ E2B CLI found: $(e2b --version)"
echo "✓ Logged in as: $(e2b auth whoami)"
echo ""

# Build template
echo "📦 Building template from Dockerfile..."
echo ""

e2b template build --name "fork-terminal-ai-agents"

echo ""
echo "======================================================================"
echo "Template Build Complete!"
echo "======================================================================"
echo ""
echo "Next steps:"
echo "1. Copy the template ID from above"
echo "2. Save it: echo 'TEMPLATE_ID' > ../.e2b_template_id"
echo "3. Test it: cd .. && python3 test_template.py"
echo ""
