import psycopg2
import json
from kafka import KafkaProducer
from flask import Flask, request, jsonify

app = Flask(__name__)

DB_CONFIG = {
    "dbname": "simpleapi_database",
    "user": "postgres",
    "password": "postgres",
    "host": "db",
    "port": 5432
}

KAFKA_BROKER = "9092"
KAFKA_TOPIC = "file_topic"

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

@app.route('/upload', methods=['POST'])
def upload_simpleapi_database():
    data = request.json
    file_address = data.get("file_address")
    file_id = data.get("file_id")
    bucket_name = data.get("bucket_name")
    object_name = data.get("object_name")

    if not all([file_address, file_id, bucket_name, object_name]):
        return jsonify({"error": "All fields are required"}), 400

    try:
        # Store metadata in PostgreSQL
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO simpleapi_database (file_address, file_id, bucket_name, object_name) VALUES (%s, %s, %s, %s)",
            (file_address, file_id, bucket_name, object_name)
        )
        conn.commit()
        cur.close()
        conn.close()

        # Publish to Kafka
        producer.send(KAFKA_TOPIC, data)

        return jsonify({"message": "File metadata stored and sent to Kafka"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
