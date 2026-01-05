# E2B Custom Template: Fork Terminal AI Agents
# This Dockerfile creates an E2B template with AI agent CLIs pre-installed

FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/root/.local/bin:${PATH}"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    python3 \
    python3-pip \
    python3-venv \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 20.x (required for CLIs)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Install Python API libraries for AI agents (fallback when CLIs unavailable)
RUN pip3 install --no-cache-dir \
    anthropic>=0.39.0 \
    google-genai>=0.1.0 \
    openai>=1.0.0

# Install REAL CLI tools via npm
# Claude Code (official CLI from Anthropic)
RUN npm install -g @anthropic-ai/claude-code || \
    echo "⚠️  Claude Code CLI installation failed, will use Python API fallback"

# Gemini CLI (official CLI from Google)
RUN npm install -g @google/gemini-cli || \
    echo "⚠️  Gemini CLI installation failed, will use Python API fallback"

# Codex CLI (official CLI from OpenAI)
RUN npm install -g @openai/codex || \
    echo "⚠️  Codex CLI installation failed, will use Python API fallback"

# Note: Wrapper scripts removed - using real CLIs installed above
# The sandbox_backend.py will check CLI availability at runtime
# and fall back to Python APIs if CLIs are not available

# Set working directory
WORKDIR /home/user

# Metadata
LABEL description="E2B template with AI agent support (Claude, Gemini, Codex)"
LABEL version="1.0"
LABEL agents="claude,gemini,codex"
