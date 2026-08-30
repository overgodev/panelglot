# `docker build`/`docker run --gpus` only makes sense on x86_64 hosts here —
# see Dockerfile's arm64 branch (CPU-only, no CUDA available on that arch).
UNAME_M := $(shell uname -m)
ifeq ($(UNAME_M),$(filter $(UNAME_M),x86_64 amd64))
GPU_FLAGS := --gpus all
else
GPU_FLAGS :=
endif

build-image:
	docker rmi manga-image-translator || true
	docker build . --tag=manga-image-translator

run-web-server:
	docker run $(GPU_FLAGS) -p 5003:5003 --ipc=host --rm manga-image-translator \
		--verbose \
		--use-gpu \
		--host=0.0.0.0 \
		--port=5003 \
		--entrypoint python \
		-v ./result:/app/result \
		-v ./server/main.py:/app/server/main.py \
		-v ./server/core/instance.py:/app/server/core/instance.py \
		zyddnys/manga-image-translator:main \
		server/main.py --verbose --start-instance --host=0.0.0.0 --port=5003 --use-gpu
