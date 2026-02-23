#!/usr/bin/env python3
"""
Simple Kafka message sender
Edit the variables below to change what you send
"""

# ========== EDIT THESE ==========
TOPIC = "messages"
MESSAGE = "Hello from Kafka!"
KAFKA_SERVER = "localhost:9092"
# ================================

from kafka import KafkaProducer

def send_message():
    producer = KafkaProducer(bootstrap_servers=KAFKA_SERVER)
    
    # Send the message
    producer.send(TOPIC, MESSAGE.encode('utf-8'))
    producer.flush()
    
    print(f"✓ Sent to topic '{TOPIC}': {MESSAGE}")
    
    producer.close()

if __name__ == "__main__":
    send_message()
