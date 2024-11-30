import json
import logging
import psycopg2
from minio import Minio
from kafka import KafkaConsumer


DB_CONFIG = {
    "dbname": "simpleapi_database",
    "user": "postgres",
    "password": "postgres",
    # "host": "localhost",
    "host": "db",
    "port": 5432
}

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

        # 1
        if not MINIO_CLIENT.bucket_exists(bucket_name):
            MINIO_CLIENT.make_bucket(bucket_name)

        logging.info("writing on bucket..........")

        MINIO_CLIENT.fput_object(bucket_name, object_name, file_address)
        print(f"File {object_name} uploaded to MinIO bucket {bucket_name}.")
        
        # 2
        # with open(file_address, 'rb') as file_stream:
        #     if not MINIO_CLIENT.bucket_exists(bucket_name):
        #         MINIO_CLIENT.make_bucket(bucket_name)

        #     MINIO_CLIENT.put_object(
        #         bucket_name, object_name, file_stream, length=-1, part_size= size
        #     )
        #     print(f"File {object_name} uploaded to MinIO bucket {bucket_name}.")

    except FileNotFoundError:
        print(f"File not found at address: {file_address}")
    except Exception as e:
        print(f"Error processing message: {e}")