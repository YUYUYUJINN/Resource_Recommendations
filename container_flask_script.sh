podman stop $(podman ps | grep flask | awk '{print $1}')

podman build -t flask-resource-app /root/flask-container/.

podman run -d -p 5000:5000 flask-resource-app
