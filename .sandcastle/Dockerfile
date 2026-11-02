# Sandbox image for the AFK runner: Sandcastle's own Dockerfile plus uv and
# Python for this project. Rebuild after editing: npm run sandcastle:build-image
FROM node:22-bookworm

RUN apt-get update && apt-get install -y \
  git \
  curl \
  jq \
  && rm -rf /var/lib/apt/lists/*

# Same uv version as the Validation workflow (.github/workflows/validation.yml).
COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /uvx /usr/local/bin/

# Build-args for UID/GID alignment: sandcastle docker build-image
# defaults these to the host user's UID/GID so image-built files
# and bind-mounted files share an owner without runtime chown.
ARG AGENT_UID=1000
ARG AGENT_GID=1000

# Rename the base image's "node" user to "agent" and align UID/GID.
RUN groupmod -o -g $AGENT_GID node && usermod -o -u $AGENT_UID -g $AGENT_GID -d /home/agent -m -l agent node
USER ${AGENT_UID}:${AGENT_GID}

RUN curl -fsSL https://claude.ai/install.sh | bash
ENV PATH="/home/agent/.local/bin:$PATH"

# The virtual environment lives in the container, not in the bind-mounted
# worktree: it stays Linux-only and off the Windows filesystem. Copy mode
# because the uv cache and the environment sit on different filesystems.
ENV UV_PROJECT_ENVIRONMENT=/home/agent/.venv \
  UV_LINK_MODE=copy
RUN uv python install 3.13

WORKDIR /home/agent

# In worktree sandbox mode, Sandcastle bind-mounts the git worktree at /home/agent/workspace
# and overrides the working directory to /home/agent/workspace at container start.
ENTRYPOINT ["sleep", "infinity"]
