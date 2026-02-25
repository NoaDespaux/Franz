import json
import logging
import asyncio
import os
from datetime import datetime, timezone
from confluent_kafka import Consumer, Producer, KafkaError

# --- Logging configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Validation constants ---
MAX_SENDER_LENGTH = 150
MAX_MESSAGE_LENGTH = 5000
MIN_MESSAGE_LENGTH = 1

# --- Kafka configuration via environment variables ---
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'localhost:9092')
SOURCE_TOPIC = os.getenv('SOURCE_TOPIC', 'mailMSG')
TARGET_TOPIC = os.getenv('TARGET_TOPIC', 'tickets-formatted')
DLQ_TOPIC = os.getenv('DLQ_TOPIC', 'tickets-formatted-dlq')
GROUP_ID = os.getenv('GROUP_ID', 'mail-aufbereitung')

def delivery_report(err, msg):
    """Async callback invoked on each delivery acknowledgement from the broker Producer."""
    if err is not None:
        logger.error(f"[Producer] Message delivery failed: {err}")
    else:
        logger.debug(f"[Producer] Message delivered to {msg.topic()} [{msg.partition()}]")

def validate_and_sanitize_input(raw_json: dict) -> tuple[str, str, str, str]:
    """Validates and sanitizes input data from mail-kummerkasten.
    
    Args:
        raw_json: Raw message data from Email
        
    Returns:
        Tuple of (sender, subject, message, timestamp)
        
    Raises:
        ValueError: If validation fails
    """
    # Validate sender
    sender = raw_json.get('sender')
    if not sender:
        raise ValueError("Missing required field: 'sender'")
    if not isinstance(sender, str):
        raise ValueError(f"Invalid sender type: expected str, got {type(sender).__name__}")
    sender = sender.strip()
    if not sender:
        raise ValueError("Sender cannot be empty or whitespace only")
    if len(sender) > MAX_SENDER_LENGTH:
        raise ValueError(f"Sender exceeds maximum length of {MAX_SENDER_LENGTH} characters")
    
    # Validate subject (allow empty subject but ensure it's a string)
    subject = raw_json.get('subject', '')
    if not isinstance(subject, str):
        raise ValueError(f"Invalid subject type: expected str, got {type(subject).__name__}")
    subject = subject.strip()

    # Validate message
    message = raw_json.get('message')
    if not message:
        raise ValueError("Missing required field: 'message'")
    if not isinstance(message, str):
        raise ValueError(f"Invalid message type: expected str, got {type(message).__name__}")
    message = message.strip()
    if len(message) < MIN_MESSAGE_LENGTH:
        raise ValueError(f"Message is too short (minimum {MIN_MESSAGE_LENGTH} character)")
    if len(message) > MAX_MESSAGE_LENGTH:
        raise ValueError(f"Message exceeds maximum length of {MAX_MESSAGE_LENGTH} characters")
    
    # Validate and parse timestamp
    timestamp_str = raw_json.get('timestamp')
    if not timestamp_str:
        raise ValueError("Missing required field: 'timestamp'")
    if not isinstance(timestamp_str, str):
        raise ValueError(f"Invalid timestamp type: expected str, got {type(timestamp_str).__name__}")
    # Validate ISO 8601 format by attempting to parse it
    try:
        datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
    except ValueError as e:
        raise ValueError(f"Invalid timestamp format (expected ISO 8601): {e}")
    
    return sender, subject, message, timestamp_str

def transform_payload(raw_json: dict) -> dict:
    """Transforms raw Email event to normalized ticket format.
    
    Args:
        raw_json: Raw message data from Email
        
    Returns:
        Normalized ticket dictionary
        
    Raises:
        ValueError: If validation or transformation fails
    """
    sender, subject, message, timestamp_str = validate_and_sanitize_input(raw_json)
    
    # Prefix the message with the subject if one exists
    combined_body = f"[{subject}]\n\n{message}" if subject else message

    return {
        'contact': sender,
        'origin': 'Email',
        'body': combined_body,
        'date': timestamp_str
    }

async def consume_and_transform():
    """Async loop for Kafka consumption and production."""
    
    consumer_conf = {
        'bootstrap.servers': KAFKA_BROKER,
        'group.id': GROUP_ID,
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': False
    }
    
    producer_conf = {
        'bootstrap.servers': KAFKA_BROKER
    }

    consumer = Consumer(consumer_conf)
    producer = Producer(producer_conf)

    consumer.subscribe([SOURCE_TOPIC])
    logger.info(f"Service started. Listening to topic: '{SOURCE_TOPIC}'...")

    loop = asyncio.get_running_loop()

    try:
        while True:
            msg = await loop.run_in_executor(None, consumer.poll, 1.0)
            
            producer.poll(0)

            if msg is None:
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    # End of partition (not an error)
                    continue
                else:
                    logger.error(f"[Consumer] Error: {msg.error()}")
                    continue

            raw_value = ""
            try:
                raw_value = msg.value().decode('utf-8')
                raw_json = json.loads(raw_value)
                
                normalized_json = transform_payload(raw_json)
                
                producer.produce(
                    topic=TARGET_TOPIC,
                    value=json.dumps(normalized_json).encode('utf-8'),
                    callback=delivery_report
                )
                
                consumer.commit(msg, asynchronous=False)
                logger.info(f"[Transformation] Message transformed from {normalized_json['contact']}")

            except json.JSONDecodeError as decode_err:
                # Malformed JSON intercepted, route to DLQ
                logger.error(f"[Transformation] Malformed JSON: {decode_err} | Sending to DLQ")
                dlq_msg = {
                    "error": str(decode_err),
                    "error_type": "json_decode_error",
                    "raw_value": raw_value,
                    "time": datetime.now(timezone.utc).isoformat()
                }
                producer.produce(topic=DLQ_TOPIC, value=json.dumps(dlq_msg).encode('utf-8'), callback=delivery_report)
                consumer.commit(msg, asynchronous=False)
            except ValueError as val_err:
                # Validation error intercepted, route to DLQ
                logger.error(f"[Transformation] Validation error: {val_err} | Sending to DLQ")
                dlq_msg = {
                    "error": str(val_err),
                    "error_type": "validation_error",
                    "raw_value": raw_value,
                    "time": datetime.now(timezone.utc).isoformat()
                }
                producer.produce(topic=DLQ_TOPIC, value=json.dumps(dlq_msg).encode('utf-8'), callback=delivery_report)
                consumer.commit(msg, asynchronous=False)
            except Exception as e:
                # Unexpected error intercepted, route to DLQ
                logger.error(f"[Transformation] Unexpected error: {e} | Sending to DLQ")
                dlq_msg = {
                    "error": str(e),
                    "error_type": "unexpected_error",
                    "raw_value": raw_value,
                    "time": datetime.now(timezone.utc).isoformat()
                }
                producer.produce(topic=DLQ_TOPIC, value=json.dumps(dlq_msg).encode('utf-8'), callback=delivery_report)
                consumer.commit(msg, asynchronous=False)

    except asyncio.CancelledError:
        logger.info("Shutdown requested by system.")
    finally:
        logger.info("Flushing pending messages and closing connections gracefully...")
        # Ensure in-memory buffers are sent to Kafka
        producer.flush(timeout=10)
        consumer.close()

if __name__ == '__main__':
    try:
        asyncio.run(consume_and_transform())
    except KeyboardInterrupt:
        logger.info("Manual interruption (Ctrl+C). Service stopped.")
