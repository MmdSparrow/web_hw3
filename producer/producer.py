import os
import json
import psycopg2
from kafka import KafkaProducer
from flask import Flask, request

app = Flask(__name__)

DB_CONFIG = {
    "dbname": "file_metadata",
    "user": "user",
    "password": "password",
    "host": "postgres",
    "port": 5432,
}

producer = KafkaProducer(
    bootstrap_servers="kafka:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)


def store_metadata(file_id, file_address, bucket_name, object_name):
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO file_metadata (file_id, file_address, bucket_name, object_name) VALUES (%s, %s, %s, %s)",
        (file_id, file_address, bucket_name, object_name),
    )
    connection.commit()
    cursor.close()
    connection.close()


@app.route("/send-file", methods=["POST"])
def send_file():
    data = request.json
    file_id = data["file_id"]
    file_address = data["file_address"]
    bucket_name = data["bucket_name"]
    object_name = data["object_name"]

    # Store metadata in PostgreSQL
    store_metadata(file_id, file_address, bucket_name, object_name)

    # Send message to Kafka
    producer.send("file-topic", value=data)

    return {"status": "success"}, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
