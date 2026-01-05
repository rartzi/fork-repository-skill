# E2B Base Template: Fork Terminal (Raw CLI Only)
# Lightweight template for raw CLI commands (no AI agents)

FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/root/.local/bin:${PATH}"

# Install essential system tools
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    python3 \
    python3-pip \
    python3-venv \
    build-essential \
    jq \
    vim \
    nano \
    htop \
    tree \
    zip \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /home/user

# Metadata
LABEL description="E2B base template for raw CLI commands (no AI agents)"
LABEL version="1.0"
LABEL template="base"
