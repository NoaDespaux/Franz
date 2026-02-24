import imaplib
import email
import email.policy
import json
import logging
import os
import time
from datetime import datetime, timezone
from confluent_kafka import Producer

# --- Logging configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- IMAP & Kafka configuration ---
IMAP_SERVER = os.getenv('IMAP_SERVER', 'imap.gmail.com')
IMAP_PORT = int(os.getenv('IMAP_PORT', 993))
IMAP_USER = os.getenv('IMAP_USER', 'contact@my-project.com')
IMAP_PASS = os.getenv('IMAP_PASS', 'password_or_app_password')
POLL_INTERVAL = int(os.getenv('POLL_INTERVAL', 10))

KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'localhost:9092')
TARGET_TOPIC = os.getenv('TARGET_TOPIC', 'mailMSG')

def delivery_report(err, msg):
    if err is not None:
        logger.error(f"[Kafka] Message delivery failed: {err}")
    else:
        logger.info(f"[Kafka] Email delivered to {msg.topic()} [{msg.partition()}]")

def get_text_body(email_message):
    """Extracts the text body of the email."""
    body = ""
    if email_message.is_multipart():
        for part in email_message.walk():
            content_type = part.get_content_type()
            disposition = str(part.get("Content-Disposition"))
            # Look for the text part
            if content_type == "text/plain" and "attachment" not in disposition:
                try:
                    body = part.get_payload(decode=True).decode()
                    break
                except Exception as e:
                    logger.warning(f"Body decoding error: {e}")
    else:
        try:
            body = email_message.get_payload(decode=True).decode()
        except Exception as e:
            logger.warning(f"Body decoding error: {e}")
    return body.strip()

def process_emails():
    # Kafka Producer configuration
    producer = Producer({'bootstrap.servers': KAFKA_BROKER})
    
    logger.info(f"Connecting to IMAP server {IMAP_SERVER}:{IMAP_PORT}...")
    try:
        use_ssl = os.getenv('IMAP_SSL', 'true').lower() == 'true'
        if use_ssl:
            mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        else:
            mail = imaplib.IMAP4(IMAP_SERVER, IMAP_PORT)
        mail.login(IMAP_USER, IMAP_PASS)
        logger.info("IMAP connection successful.")
    except Exception as e:
        logger.error(f"Unable to connect to IMAP: {e}")
        return

    while True:
        try:
            # Select the inbox
            mail.select('INBOX')
            
            # Search only for UNREAD emails (UNSEEN)
            status, messages = mail.search(None, 'UNSEEN')
            
            if status == 'OK':
                mail_ids = messages[0].split()
                if mail_ids:
                    logger.info(f"{len(mail_ids)} new email(s) found.")
                    
                for mail_id in mail_ids:
                    # Fetch the entire email. The (RFC822) action automatically marks the email as "Read"
                    status, msg_data = mail.fetch(mail_id, '(RFC822)')
                    
                    if status == 'OK':
                        for response_part in msg_data:
                            if isinstance(response_part, tuple):
                                # Parsing the email
                                email_msg = email.message_from_bytes(response_part[1], policy=email.policy.default)
                                
                                sender = email_msg.get('From')
                                subject = email_msg.get('Subject', '')
                                date_str = email_msg.get('Date')
                                content = get_text_body(email_msg)
                                
                                # Formatting payload for Kafka
                                payload = {
                                    "sender": sender,
                                    "subject": subject,
                                    "message": content,
                                    "timestamp": datetime.now(timezone.utc).isoformat()
                                }
                                
                                logger.info(f"Transferring email from {sender} to Kafka...")
                                
                                # Kafka publication
                                producer.produce(
                                    topic=TARGET_TOPIC,
                                    value=json.dumps(payload).encode('utf-8'),
                                    callback=delivery_report
                                )
                                producer.poll(0)
                                
        except Exception as e:
            logger.error(f"Error during polling loop: {e}")
            # Reconnection logic could be added here in case of connection error
            
        # Push any remaining Kafka messages
        producer.flush(timeout=1)
        
        # Wait before the next check
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    try:
        process_emails()
    except KeyboardInterrupt:
        logger.info("Stopping Mail SIM service.")
