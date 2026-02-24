#!/usr/bin/env python3
"""
Simple Kafka message reader
Edit the variables below to change what you read
"""

# ========== EDIT THESE ==========
DEFAULT_TOPIC = "discordMSG"
KAFKA_SERVER = "localhost:9092"
GROUP_ID = "Überbringer"
# ================================

from kafka import KafkaConsumer

def read_messages():
    topic = input(f"Topic to listen to (default: {DEFAULT_TOPIC}): ").strip()
    if not topic:
        topic = DEFAULT_TOPIC
    
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=KAFKA_SERVER,
        group_id=GROUP_ID,
        auto_offset_reset='earliest',  # Start from beginning if no offset stored
        enable_auto_commit=True,
        value_deserializer=lambda m: m.decode('utf-8')
    )
    
    print(f"✓ Listening to topic '{topic}'...")
    print("Press Ctrl+C to stop\n")
    
    try:
        for message in consumer:
            print(f"[{message.partition}:{message.offset}] {message.value}")
    except KeyboardInterrupt:
        print("\n\n✓ Stopped listening")
    finally:
        consumer.close()

if __name__ == "__main__":
    read_messages()
