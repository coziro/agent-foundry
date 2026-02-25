FROM ghcr.io/astral-sh/uv:0.9.2-python3.12-bookworm

RUN apt-get update && apt-get install -y \
    tmux \
    curl \
    git \
    vim \
    tree \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

