FROM ghcr.io/astral-sh/uv:0.9.2-python3.12-bookworm

RUN apt-get update && apt-get install -y \
    tmux \
    curl \
    git \
    vim \
    tree \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash user
USER user

# install claude code
RUN curl -fsSL https://claude.ai/install.sh | bash
ENV PATH="/home/user/.local/bin:${PATH}"
