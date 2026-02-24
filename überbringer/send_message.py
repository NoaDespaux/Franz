#!/usr/bin/env python3
"""
Simple Kafka message sender
Edit the variables below to change what you send
"""

# ========== EDIT THESE ==========
DEFAULT_TOPIC = "discordMSG"
DEFAULT_MESSAGE = "Hello from Kafka!"
KAFKA_SERVER = "localhost:9092"
# ================================

from kafka import KafkaProducer

def send_message():
    topic = input(f"Topic to send to (default: {DEFAULT_TOPIC}): ").strip()
    if not topic:
        topic = DEFAULT_TOPIC
    
    producer = KafkaProducer(bootstrap_servers=KAFKA_SERVER)
    
    print(f"✓ Sending to topic '{topic}'")
    print("Type your messages below (Ctrl+C to stop)\n")
    
    try:
        while True:
            message = input(f"Message (default: {DEFAULT_MESSAGE}): ").strip()
            if not message:
                message = DEFAULT_MESSAGE
            
            # Send the message
            producer.send(topic, message.encode('utf-8'))
            producer.flush()
            
            print(f"✓ Sent: {message}\n")
    except KeyboardInterrupt:
        print("\n\n✓ Stopped sending")
    finally:
        producer.close()

if __name__ == "__main__":
    send_message()
