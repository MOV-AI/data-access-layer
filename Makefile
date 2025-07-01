PY_SRC_DIR := dal/
PYTHON_SOURCE_FILES := $(shell find $(PY_SRC_DIR) -type f -name "*.py")

dist_py: $(PYTHON_SOURCE_FILES) pyproject.toml
	IN_CONTAINER_MOUNT_POINT="/__w/workspace/src"; \
	DOCKER_IMAGE="registry.cloud.mov.ai/devops/py-buildserver:latest"; \
	docker run --rm -t -v "$$(pwd)":$$IN_CONTAINER_MOUNT_POINT "$$DOCKER_IMAGE" bash -c "cd $$IN_CONTAINER_MOUNT_POINT; python3 -m build --outdir dist_py"

# alias target for convenience
py: dist_py

clean_py:
	sudo rm -rf dist_py data_access_layer.egg-info/

clean: clean_py
