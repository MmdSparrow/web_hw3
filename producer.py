import psycopg2
import json
from logging import log
import logging
from kafka import KafkaProducer
from flask import Flask, request, jsonify

app = Flask(__name__)

DB_CONFIG = {
    "dbname": "simpleapi_database",
    "user": "postgres",
    "password": "postgres",
    # "host": "localhost",
    "host": "db",
    "port": 5432
}

KAFKA_BROKER = "kafka:9092"
logging.INFO(KAFKA_BROKER)
KAFKA_TOPIC = "file_topic_moz"

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    linger_ms=0,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

def on_send_success(record_metadata):
    print(record_metadata.topic)
    print(record_metadata.partition)
    print(record_metadata.offset)

def on_send_error(excp):
    print(excp)
    log.error('I am an errback', exc_info=excp)

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
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO file_metadata (file_address, file_id, bucket_name, object_name) VALUES (%s, %s, %s, %s)",
            (file_address, file_id, bucket_name, object_name)
        )
        conn.commit()
        cur.close()
        conn.close()

        producer.send(KAFKA_TOPIC, value=data).add_callback(on_send_success).add_errback(on_send_error)
        # producer.flush(timeout=10)
        producer.flush()

        return jsonify({"message": "File metadata stored and sent to Kafka"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    # finally:
    #     producer.close()
    #     # producer.close(timeout=5)
    #     logging.info("Kafka producer closed.")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
