# syntax=docker/dockerfile:1

# `docker build`/`docker buildx build` sets TARGETARCH automatically to match
# the build's target platform (the host arch for a normal same-machine build;
# whatever `--platform` says for a cross-build) — no manual flag needed for
# the common case of "build on the machine you'll run it on."
ARG TARGETARCH

# --- Base image selection, per architecture -----------------------------
# amd64 (Windows/Linux on x86_64 with an Nvidia GPU): CUDA-enabled PyTorch
#   image — this is the fast, GPU-accelerated path.
# arm64 (Apple Silicon Macs, ARM Linux/servers): there is no consumer CUDA on
#   this arch, and Docker Desktop on Mac can't pass Metal/MPS through to a
#   Linux container anyway, so this path is CPU-only. Use a slim base and a
#   CPU-only PyTorch wheel to keep the image (and its resident RAM) small.
FROM pytorch/pytorch:2.5.1-cuda11.8-cudnn9-runtime AS base-amd64
FROM python:3.11-slim AS base-arm64

FROM base-${TARGETARCH} AS base
ARG TARGETARCH

WORKDIR /app

# Avoid caching pip wheels / .pyc files in the image layers — pure size/RAM
# waste for a container that's built once and run many times.
ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Etc/UTC

# Install pip dependencies

COPY requirements.txt /app/requirements.txt

RUN apt-get update --yes \
        && apt-get install --no-install-recommends --yes g++ wget ffmpeg libsm6 libxext6 gimp libvulkan1 \
        && if [ "$TARGETARCH" = "amd64" ]; then \
                wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb \
                && dpkg -i cuda-keyring_1.1-1_all.deb \
                && rm -f cuda-keyring_1.1-1_all.deb \
                && apt-get update --yes \
                && apt-get install --no-install-recommends --yes libcudnn8=8*-1+cuda11.8 libcudnn8-dev=8*-1+cuda11.8; \
           fi \
        && if [ "$TARGETARCH" = "arm64" ]; then \
                pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu; \
           fi \
        && pip install -r /app/requirements.txt \
        && apt-get remove g++ wget --yes \
        && apt-get autoremove --yes \
        && rm -rf /var/lib/apt/lists/* /var/cache/apt

COPY . /app

# Prepare models
RUN --mount=type=cache,target=/.cache/models \
    cp -rn /.cache/models/. /app/models/ || true && \
    python -u scripts/docker_prepare.py --continue-on-error && \
    cp -rn /app/models/. /.cache/models/ || true

RUN rm -rf /tmp && mkdir /tmp && chmod 1777 /tmp

# Add /app to Python module path. MALLOC_ARENA_MAX caps glibc's per-thread
# malloc arenas — without it, the mix of multi-threaded BLAS/OpenCV calls and
# worker processes in the translation pipeline can multiply resident memory
# several times over for no throughput benefit. Safe on both the GPU and
# CPU-only paths.
ENV PYTHONPATH="/app" \
    MALLOC_ARENA_MAX=2

WORKDIR /app

ENTRYPOINT ["python", "-m", "manga_translator"]