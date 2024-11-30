import json
import logging
from kafka import KafkaConsumer
from minio import Minio

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

KAFKA_BROKER = "kafka:9092"
logging.info(KAFKA_BROKER)
KAFKA_TOPIC = "file_topic"

MINIO_CLIENT = Minio(
    "minio:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False
)

consumer = KafkaConsumer(
    KAFKA_TOPIC,
    bootstrap_servers=KAFKA_BROKER,
    value_deserializer=lambda m: json.loads(m.decode("utf-8"))
)

for message in consumer:
    try:
        data = message.value
        file_address = data["file_address"]
        bucket_name = data["bucket_name"]
        object_name = data["object_name"]

        with open(file_address, 'rb') as file_stream:
            if not MINIO_CLIENT.bucket_exists(bucket_name):
                MINIO_CLIENT.make_bucket(bucket_name)

            MINIO_CLIENT.put_object(
                bucket_name, object_name, file_stream, length=-1, part_size=10*1024*1024
            )
            print(f"File {object_name} uploaded to MinIO bucket {bucket_name}.")
    except FileNotFoundError:
        print(f"File not found at address: {file_address}")
    except Exception as e:
        print(f"Error processing message: {e}")
