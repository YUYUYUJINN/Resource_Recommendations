import requests
import mysql.connector
import subprocess
from datetime import datetime, timedelta

# Update /etc/hosts
def update_dns(ip, hostname):
    entry = f"{ip} {hostname}\n"
    hosts_file = "/etc/hosts"

    try:
        # Check if the entry already exists
        with open(hosts_file, "r") as f:
            if entry.strip() in f.read():
                print(f"DNS entry '{entry.strip()}' already exists.")
                return

        # Add the entry to /etc/hosts
        with open(hosts_file, "a") as f:
            f.write(entry)
        print(f"Added DNS entry: {entry.strip()}")
		
		
    except PermissionError:
        print("Permission denied: Run the script with sudo or administrator privileges.")

# Prometheus Query Helper with Basic Auth
class PrometheusClient:
    def __init__(self, prometheus_url, username, password):
        self.url = prometheus_url
        self.auth = (username, password)

    def query(self, promql):
        response = requests.get(
            f"{self.url}/api/v1/query",
            params={"query": promql},
            auth=self.auth,
            verify=False  # Skip SSL verification if necessary
        )
        if response.status_code == 200:
            return response.json().get("data", {}).get("result", [])
        else:
            raise Exception(f"Prometheus query failed: {response.text}")

# Database Helper
class MySQLClient:
    def __init__(self, host, user, password, database):
        self.connection = mysql.connector.connect(
            host=host, user=user, password=password, database=database
        )
        self.cursor = self.connection.cursor()

    def save_recommendation(self, namespace, pod, cpu, memory):
        query = """
        INSERT INTO resource_recommendations (namespace, pod, cpu_recommendation, memory_recommendation, updated_at)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE cpu_recommendation=VALUES(cpu_recommendation), memory_recommendation=VALUES(memory_recommendation), updated_at=VALUES(updated_at)
        """
        self.cursor.execute(query, (namespace, pod, cpu, memory, datetime.now()))
        self.connection.commit()

    def close(self):
        self.cursor.close()
        self.connection.close()

# Main Logic
def main():
    # DNS Configuration
    DNS_IP = "192.168.2.154"
    DNS_HOSTNAME = "prometheus-k8s-openshift-monitoring.apps.cluster01.okd.openclab.com"

    # Update DNS
    update_dns(DNS_IP, DNS_HOSTNAME)

    # Prometheus Configuration
    PROMETHEUS_URL = f"https://{DNS_HOSTNAME}"
    PROMETHEUS_AUTH = {
        "basicAuthUser": "internal",
        "basicAuthPassword": "MqXYKdgpfGtbK7DO7Mblkt/Gnf4gX3p+tVnWYWxdPjBmK1ut7chsbcKgL6ptg7R/IZkTG+iK2VYv2TLE5DtzVQ2U62bxoxQSxWUZJGpDqAyiHcD6IE39UPo3tu2MmrxtBeRwb644Sk0s831uNKHBWkkna3be1gdy7IyNZ88tb8qruFy4Qp5crucls7uTeS5mcWHu6JiP1WaW7NqWdnro9JZIgF3vZIiqxmdpbbZTyM2bKdaSqlnRUm8ElWHiVeNke72Dp6sP0kYBfQqPkBTPkE0iaA9uyQ9MjGlB2yDSSac/oqTEFHSEk9XZA12gI8jPSTSmk9ojY2tTeb42rcz7"
    }

    # MySQL Configuration
    MYSQL_CONFIG = {
        "host": "192.168.1.250",
        "user": "root",
        "password": "test123",
        "database": "recommendations",
    }

    # Prometheus Queries
    QUERY_CPU = """
    quantile_over_time(0.95, sum by (namespace, pod) (
        rate(container_cpu_usage_seconds_total{namespace!~'.*openshift.*'}[1m])
    )[1w:5m]) * on (namespace, pod) group_left() kube_pod_status_phase{phase="Running"}
    """
    QUERY_MEMORY = """
    quantile_over_time(0.95, max by (namespace, pod) (
        container_memory_usage_bytes{namespace!~'.*openshift.*'}
    )[1w:5m]) * on (namespace, pod) group_left() kube_pod_status_phase{phase="Running"}
    """

    # Initialize Clients
    prom_client = PrometheusClient(
        PROMETHEUS_URL,
        PROMETHEUS_AUTH["basicAuthUser"],
        PROMETHEUS_AUTH["basicAuthPassword"],
    )
    db_client = MySQLClient(**MYSQL_CONFIG)

    try:
	
        # Fetch CPU and Memory Data
        cpu_data = prom_client.query(QUERY_CPU)
        memory_data = prom_client.query(QUERY_MEMORY)

        # Map data by namespace and pod
        cpu_data_map = {f"{item['metric']['namespace']}/{item['metric']['pod']}": item["value"][1] for item in cpu_data}
        memory_data_map = {f"{item['metric']['namespace']}/{item['metric']['pod']}": item["value"][1] for item in memory_data}

        # Process and Save Recommendations
        for key in cpu_data_map.keys() & memory_data_map.keys():
            namespace, pod = key.split("/")

            # Apply Minimum Recommendations
            cpu_recommendation = max(float(cpu_data_map[key]), 0.05)
            memory_recommendation = max(float(memory_data_map[key]) / (1024 ** 3), 0.05)  # Convert bytes to GiB

	    # Save to DB
            db_client.save_recommendation(namespace, pod, cpu_recommendation, memory_recommendation)
            print(f"Saved recommendation for {namespace}/{pod}: CPU={cpu_recommendation}, Memory={memory_recommendation} GiB")

    finally:
        db_client.close()

if __name__ == "__main__":
    main()
