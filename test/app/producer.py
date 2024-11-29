from kafka import KafkaProducer
import time

def main():
    # Connect to Kafka
    producer = KafkaProducer(bootstrap_servers='kafka:9092')  # 'kafka' is the service name in Docker Compose
    topic = "test_topic"

    # Send messages in a loop
    for i in range(10):
        message = f"Message {i}"
        producer.send(topic, message.encode('utf-8'))
        print(f"Sent: {message}")
        time.sleep(1)

    producer.flush()
    producer.close()
    print("Producer finished.")

if __name__ == "__main__":
    main()
