podman run -d \
  --name=mysql-container \
  -e MYSQL_ROOT_PASSWORD=test123 \
  -v /var/lib/mysql-data:/var/lib/mysql \
  -p 3306:3306 \
  mysql:latest

# --- mysql install ---
# podman run -d \
#   --name=mysql-container \
#   -e MYSQL_ROOT_PASSWORD=test123 \
#   -e MYSQL_DATABASE=recommendations \
#   -e MYSQL_USER=recommender \
#   -e MYSQL_PASSWORD=test123 \
#   -v /var/lib/mysql-data:/var/lib/mysql \
#   -p 3306:3306 \
#   mysql:latest
