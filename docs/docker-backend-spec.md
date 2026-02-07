# Docker Backend Spec

> Planning document for adding Docker as a 4th execution backend to the fork-terminal skill.

**Status:** Draft / Planning
**Branch:** `feature/docker-backend`

---

## Why Docker?

The fork-terminal skill currently supports three execution backends:

| Backend | Isolation | Cost | Offline | Custom Env | GPU |
|---------|-----------|------|---------|------------|-----|
| Local Terminal | None | Free | Yes | Your machine | Local |
| E2B Sandbox | Full VM | Paid | No | Fixed template | No |
| SSH Remote | Remote machine | Free | LAN only | Pre-configured | Yes |
| **Docker (new)** | **Container** | **Free** | **Yes** | **Custom Dockerfile** | **Via --gpus** |

### Docker fills the "free, offline, isolated, customizable" gap

- **Free isolation** -- Container-level isolation without E2B subscription costs
- **Offline** -- Works without internet (unlike E2B which requires cloud connectivity)
- **Reproducible environments** -- Dockerfile defines exact dependencies, shareable across team
- **Custom images per project** -- Not locked to a single E2B template; each project can have its own
- **CI/CD friendly** -- Same container runs locally and in pipelines
- **GPU passthrough** -- `docker run --gpus all` enables local GPU workloads
- **Fast startup** -- Cached images start in seconds vs E2B network latency

### When to use Docker vs other backends

| Scenario | Best Backend |
|----------|-------------|
| Quick trusted task | Local Terminal |
| Untrusted/experimental code (no local Docker) | E2B Sandbox |
| Remote GPU compute (DGX, cloud) | SSH Remote |
| **Isolated local execution, custom env** | **Docker** |
| **Reproducible dev environments** | **Docker** |
| **Offline isolated execution** | **Docker** |
| **Local GPU + isolation** | **Docker** |
| **CI/CD pipeline execution** | **Docker** |

---

## Architecture

### Trigger Keywords

```
"in docker"        -- "fork terminal use gemini in docker to <xyz>"
"use docker"       -- "fork terminal use docker to <xyz>"
"with docker"      -- "fork terminal with docker: python script.py"
"docker:"          -- "fork terminal docker: npm test"
```

### Command Routing

```
fork_terminal(command)
  |-- parse_command() detects "in docker" / "docker:" keywords
  |-- backend = "docker"
  +-- _execute_in_docker(agent, command, auto_close, image, working_dir)
```

### Integration Points

1. **parse_command()** in `fork_terminal.py` -- Add Docker backend detection (similar to E2B sandbox pattern)
2. **New file: `docker_backend.py`** -- Docker execution logic
3. **New cookbook: `cookbook/docker.md`** -- Instructions for Docker execution
4. **SKILL.md** -- Add Docker section to cookbook routing
5. **README.md** -- Document Docker backend

### Docker Backend Class

```python
# tools/docker_backend.py

class DockerBackend:
    """Execute commands and AI agents in Docker containers."""

    def __init__(self, verbose=False):
        self.verbose = verbose
        self._verify_docker()

    def _verify_docker(self):
        """Check Docker daemon is running."""
        # subprocess: docker info

    def execute(self, prompt, agent=None, image=None,
                auto_close=True, working_dir=None, gpu=False):
        """
        Execute in Docker container.

        Args:
            prompt: Command or agent prompt
            agent: "claude", "gemini", "codex", or None (raw CLI)
            image: Docker image to use (default: fork-terminal-agents)
            auto_close: Remove container after execution
            working_dir: Mount as /workspace in container
            gpu: Enable GPU passthrough (--gpus all)

        Returns:
            dict with success, output, error, container_id
        """
```

---

## Docker Image Strategy

### Option A: Single Pre-Built Image (Recommended for v1)

Similar to the E2B template approach -- one image with all CLIs pre-installed.

```dockerfile
# Dockerfile.agents
FROM node:20-slim

# Install AI CLIs
RUN npm install -g @anthropic-ai/claude-code
RUN npm install -g @google/gemini-cli
RUN npm install -g @openai/codex

# Install Python
RUN apt-get update && apt-get install -y python3 python3-pip

# Working directory
WORKDIR /workspace
```

**Pros:** Fast startup (cached), simple, mirrors E2B approach
**Cons:** Large image, all-or-nothing

### Option B: Per-Agent Images (Future)

Separate lightweight images per agent.

```
fork-terminal/claude:latest   -- Claude Code only
fork-terminal/gemini:latest   -- Gemini CLI only
fork-terminal/codex:latest    -- Codex CLI only
fork-terminal/base:latest     -- Python/Node only (raw CLI)
```

**Pros:** Smaller per-image, faster pull for single agent
**Cons:** More images to maintain

### Option C: User-Provided Images

Allow users to specify custom Docker images.

```
"fork terminal in docker (my-custom-image) use claude to <xyz>"
```

**Pros:** Maximum flexibility
**Cons:** User must ensure CLIs are installed

### Recommendation

Start with **Option A** for simplicity. Add Option C as an override. Consider Option B later if image size becomes an issue.

---

## Credential Handling

API keys must be injected into containers without baking them into images.

```python
# Inject as environment variables at runtime
docker run \
    -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
    -e GEMINI_API_KEY=$GEMINI_API_KEY \
    -e OPENAI_API_KEY=$OPENAI_API_KEY \
    fork-terminal-agents \
    claude -p "your prompt"
```

Uses the same `CredentialResolver` waterfall as other backends -- only the relevant agent's key is injected.

---

## Volume Mounts

```python
# Mount working directory as /workspace
docker run \
    -v $(pwd):/workspace \
    -w /workspace \
    fork-terminal-agents \
    python script.py
```

### Mount Strategy

| Mount | Container Path | Purpose |
|-------|---------------|---------|
| Working directory | `/workspace` | Code access (read/write) |
| Output directory | `/workspace/docker-output` | Captured output files |
| SSH keys | Not mounted | Security -- no SSH key exposure |
| .env files | Not mounted | Security -- use -e flags instead |

---

## GPU Support

```python
# Enable GPU passthrough
docker run --gpus all \
    fork-terminal-agents \
    python train.py
```

Requires:
- NVIDIA Container Toolkit installed
- `--gpu` flag in fork-terminal command or auto-detected

Trigger: `"fork terminal in docker with gpu: python train.py"`

---

## Auto-Close Behavior

| Mode | Docker Behavior |
|------|----------------|
| auto-close | `docker run --rm` -- container removed after execution, output captured |
| interactive | `docker run -it` -- container stays running, user can interact |

---

## Implementation Phases

### Phase 1: Core Docker Backend
- [ ] `docker_backend.py` with basic execute()
- [ ] parse_command() Docker detection
- [ ] Single pre-built Dockerfile
- [ ] Credential injection via -e flags
- [ ] Working directory mount
- [ ] Auto-close with output capture
- [ ] Cookbook: `cookbook/docker.md`

### Phase 2: Enhanced Features
- [ ] GPU passthrough support
- [ ] Custom image override
- [ ] Interactive mode (docker exec)
- [ ] Health check for Docker daemon
- [ ] Image auto-build if not present

### Phase 3: Advanced
- [ ] Per-agent images (Option B)
- [ ] Docker Compose for multi-agent scenarios
- [ ] Volume caching for node_modules/pip packages
- [ ] Network isolation options
- [ ] Resource limits (CPU, memory)

---

## Backend Comparison (Updated)

| Aspect | Local | E2B Sandbox | SSH Remote | Docker |
|--------|-------|-------------|------------|--------|
| **Speed** | Instant | ~2-5s latency | Network latency | ~1-2s (cached) |
| **Cost** | Free | E2B costs | Free (your HW) | Free |
| **Isolation** | None | Full VM | Full remote | Container |
| **Offline** | Yes | No | LAN only | Yes |
| **GPU** | Local | No | Remote | Local (nvidia-docker) |
| **Custom Env** | Your machine | Fixed template | Pre-configured | Dockerfile |
| **Reproducible** | No | Template-based | No | Yes (Dockerfile) |
| **CI/CD Ready** | No | No | No | Yes |
| **Use Case** | Dev tasks | Experimental | Heavy compute | Isolated + custom |

---

## Open Questions

1. **Image registry** -- Should we publish the pre-built image to Docker Hub / GHCR?
2. **Image auto-build** -- Should fork-terminal auto-build the image on first use if not found?
3. **Compose integration** -- Should we support docker-compose for multi-agent scenarios?
4. **Rootless Docker** -- Should we support rootless Docker for enhanced security?
5. **Podman support** -- Should we also support Podman as an alternative container runtime?
