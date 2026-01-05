# E2B Custom Template: Fork Terminal AI Agents

This directory contains the E2B template definition for running AI agents (Claude, Gemini, Codex) in isolated sandboxes.

## What This Template Provides

- **Python API Libraries**: anthropic, google-generativeai, openai
- **CLI Wrapper Scripts**: `claude`, `gemini`, `codex` commands
- **Environment**: Ubuntu 22.04 with Python 3, Node.js, and build tools

## CLI Wrappers

The wrapper scripts provide a CLI-like interface using the Python APIs:

```bash
# Claude
export ANTHROPIC_API_KEY="your-key"
claude -p "tell me a joke"

# Gemini
export GEMINI_API_KEY="your-key"
gemini -p "tell me a joke"

# Codex/OpenAI
export OPENAI_API_KEY="your-key"
codex -p "tell me a joke"
```

## Building the Template

### Prerequisites

1. **E2B Account**: Sign up at [e2b.dev](https://e2b.dev/)
2. **E2B API Key**: Get your API key from the dashboard
3. **E2B CLI**: Install with `npm install -g @e2b/cli`

### Build Steps

1. **Login to E2B**:
   ```bash
   e2b login
   ```

2. **Build and Push Template**:
   ```bash
   cd .claude/skills/fork-terminal/tools/e2b-template
   e2b template build
   ```

3. **Note the Template ID**:
   ```
   After building, E2B will output a template ID like:
   Template ID: fork-terminal-ai-agents-xxxxx
   ```

4. **Save Template ID**:
   ```bash
   echo "fork-terminal-ai-agents-xxxxx" > ../.e2b_template_id
   ```

## Alternative: Use Pre-built Template

If template building requires E2B Pro, you can use the base template with runtime installation:

```python
# In sandbox_backend.py
sandbox = Sandbox.create()  # Use base template
sandbox.commands.run("pip3 install anthropic google-generativeai openai")
# Then run agents
```

## Template Usage

Once built, the `sandbox_backend.py` will automatically use this template:

```python
from e2b import Sandbox

# Load template ID
template_id = Path(".e2b_template_id").read_text().strip()

# Create sandbox from template
sandbox = Sandbox.create(template=template_id)

# CLIs are now available!
result = sandbox.commands.run("export GEMINI_API_KEY='...' && gemini -p 'joke'")
```

## Updating the Template

To update the template with new dependencies or scripts:

1. Modify `Dockerfile` or `wrapper-scripts/*`
2. Rebuild: `e2b template build`
3. Update the template ID in `../.e2b_template_id`

## Troubleshooting

**Template build fails**:
- Check E2B CLI is installed: `e2b --version`
- Ensure you're logged in: `e2b login`
- Check account has template building permissions

**CLIs not working in sandbox**:
- Verify template ID is correct in `../.e2b_template_id`
- Check API keys are being injected correctly
- Test with base Sandbox and manual pip install first

## Cost Considerations

- **Template Storage**: E2B may charge for custom templates (check pricing)
- **Sandbox Runtime**: Billed per compute-second
- **API Calls**: Anthropic, Google, OpenAI charge per token

Using templates is more efficient than installing dependencies every time!
