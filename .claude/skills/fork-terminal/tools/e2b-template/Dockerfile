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
    nodejs \
    npm \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python API libraries for AI agents
# These provide programmatic access to the AI services
RUN pip3 install --no-cache-dir \
    anthropic \
    google-genai \
    openai

# Note: CLI tools for Claude Code, Gemini, and Codex
# These are typically installed per-user and may require different approaches
# For now, we ensure the Python APIs are available for programmatic access

# Create wrapper scripts that can use either CLI or API
# These wrappers will check for CLI tools and fall back to API if needed

COPY wrapper-scripts/claude /usr/local/bin/claude
COPY wrapper-scripts/gemini /usr/local/bin/gemini
COPY wrapper-scripts/codex /usr/local/bin/codex

RUN chmod +x /usr/local/bin/claude /usr/local/bin/gemini /usr/local/bin/codex

# Set working directory
WORKDIR /home/user

# Metadata
LABEL description="E2B template with AI agent support (Claude, Gemini, Codex)"
LABEL version="1.0"
LABEL agents="claude,gemini,codex"
