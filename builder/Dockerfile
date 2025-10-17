FROM ubuntu:24.04
LABEL authors="gryt.dev"
LABEL description="Gryt CI Pipeline Runner with standard build tools"

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install essential build packages and tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Python and pip
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    # Build essentials
    build-essential \
    gcc \
    g++ \
    make \
    cmake \
    # Version control
    git \
    git-lfs \
    # Common utilities
    curl \
    wget \
    ca-certificates \
    gnupg \
    lsb-release \
    unzip \
    zip \
    tar \
    # Node.js and npm (for JS/TS projects)
    nodejs \
    npm \
    # Additional useful tools
    jq \
    sqlite3 \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

# Create a working directory
WORKDIR /workspace

# Copy gryt source from local context and install it
# Note: When building, run from the parent directory with:
# docker build -f builder/Dockerfile -t ghcr.io/epyklab/gryt/pipeline:latest .
COPY gryt.dev /tmp/gryt-source

# Install gryt package (--break-system-packages is safe in containers)
RUN cd /tmp/gryt-source && \
    pip3 install --no-cache-dir --break-system-packages . && \
    rm -rf /tmp/gryt-source

# Verify gryt installation
RUN gryt --help

# Reset entrypoint - the executor will provide the command
ENTRYPOINT []
CMD ["/bin/bash"]
