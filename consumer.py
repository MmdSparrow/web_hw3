import json
import logging
import psycopg2
from minio import Minio
from kafka import KafkaConsumer
from kafka import KafkaProducer


DB_CONFIG = {
    "dbname": "simpleapi_database",
    "user": "postgres",
    "password": "postgres",
    "host": "db",
    "port": 5432
}

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

KAFKA_BROKER = "kafka:9092"
logging.info(KAFKA_BROKER)
KAFKA_TOPIC = "file_topic"
DLQ = "dead_letter"
GROUP_ID = "group1"
RETRY_LIMIT = 3

MINIO_CLIENT = Minio(
    "minio:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False
)

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    linger_ms=0,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

consumer = KafkaConsumer(
    KAFKA_TOPIC,
    bootstrap_servers=KAFKA_BROKER,
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    group_id=GROUP_ID,
    auto_offset_reset="earliest"
)

for message in consumer:
    retry_count = 0
    while retry_count < RETRY_LIMIT:
        try:
            data = message.value
            file_address = data["file_address"]
            file_id = data["file_id"]
            bucket_name = data["bucket_name"]
            object_name = data["object_name"]
            file_id = data["file_id"]
            etag = data["etag"]
            size = int(data["size"])

            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            update_query = """
            UPDATE file_metadata
            SET file_size = %s, etag = %s
            WHERE file_id = %s;
            """
            logging.info("writing on databse..........")
            cur.execute(
                update_query,
                (size, etag, file_id)
            )
            conn.commit()
            cur.close()
            conn.close()

            if not MINIO_CLIENT.bucket_exists(bucket_name):
                MINIO_CLIENT.make_bucket(bucket_name)

            logging.info("writing on bucket..........")

            MINIO_CLIENT.fput_object(bucket_name, object_name, file_address)
            print(f"File {object_name} uploaded to MinIO bucket {bucket_name}.")
        
        except FileNotFoundError:
            print(f"File not found at address: {file_address}")
            break
        except Exception as e:
            retry_count += 1
            print(f"Error processing message: {e}. Retry {retry_count}/{RETRY_LIMIT}")

    else:
        print(f"Max retries reached. Sending message to '{DLQ}': {message}")
        producer.send(DLQ, value=data)
        producer.flush()