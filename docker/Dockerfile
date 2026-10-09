FROM debian:12

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    gcc-arm-linux-gnueabihf \
    binutils-arm-linux-gnueabihf \
    bison \
    flex \
    bc \
    libssl-dev \
    libgnutls28-dev \
    libelf-dev \
    libncurses-dev \
    libfdt-dev \
    device-tree-compiler \
    python3 \
    python3-setuptools \
    python3-pyelftools \
    swig \
    git \
    make \
    file \
    wget \
    ca-certificates \
    xz-utils \
    u-boot-tools \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /work
