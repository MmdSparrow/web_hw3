import json
from kafka import KafkaConsumer
from minio import Minio

KAFKA_BROKER = "localhost:9092"
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

        # Open the file as a stream
        with open(file_address, 'rb') as file_stream:
            # Ensure the bucket exists in MinIO
            if not MINIO_CLIENT.bucket_exists(bucket_name):
                MINIO_CLIENT.make_bucket(bucket_name)

            # Upload the file stream to MinIO
            MINIO_CLIENT.put_object(
                bucket_name, object_name, file_stream, length=-1, part_size=10*1024*1024
            )
            print(f"File {object_name} uploaded to MinIO bucket {bucket_name}.")
    except FileNotFoundError:
        print(f"File not found at address: {file_address}")
    except Exception as e:
        print(f"Error processing message: {e}")
