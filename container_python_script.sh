podman build -t python-container /root/python-container/.

podman run -it --rm \
  --name python-container \
  -v /root/python-container/main.py:/app/main.py:ro \
  --network=host \
  python-container
