build-image:
	docker rmi manga-image-translator || true
	docker build . --tag=manga-image-translator

run-web-server:
	docker run --gpus all -p 5003:5003 --ipc=host --rm manga-image-translator \
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
