from flask import Flask, render_template, request, jsonify
import mysql.connector

app = Flask(__name__)

# MySQL 데이터베이스 연결 설정
from config import MYSQL_CONFIG

def get_db_connection():
    return mysql.connector.connect(
        host=MYSQL_CONFIG["host"],
        user=MYSQL_CONFIG["user"],
        password=MYSQL_CONFIG["password"],
        database=MYSQL_CONFIG["database"],
    )

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/data", methods=["GET"])
def get_data():
    date = request.args.get("date")
    namespace = request.args.get("namespace")

    query = """
        SELECT pod, cpu_recommendation, memory_recommendation
        FROM resource_recommendations
        WHERE updated_at LIKE %s AND namespace = %s
    """
    params = (f"{date}%", namespace)

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params)
        results = cursor.fetchall()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return jsonify(results)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

