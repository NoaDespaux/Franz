import json
import logging
import asyncio
import os
from datetime import datetime
from confluent_kafka import Consumer, Producer, KafkaError

# --- Configuration des logs ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Configuration Kafka via Variables d'Environnement ---
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'localhost:9092')
SOURCE_TOPIC = os.getenv('SOURCE_TOPIC', 'discordMSG')
TARGET_TOPIC = os.getenv('TARGET_TOPIC', 'tickets-formatted')
DLQ_TOPIC = os.getenv('DLQ_TOPIC', 'tickets-formatted-dlq')
GROUP_ID = os.getenv('GROUP_ID', 'discord-aufbereitung')

def delivery_report(err, msg):
    """Callback asynchrone appelé à chaque validation de livraison au broker par le Producer."""
    if err is not None:
        logger.error(f"[Producer] Échec d'envoi du message: {err}")
    else:
        logger.debug(f"[Producer] Message livré sur {msg.topic()} [{msg.partition()}]")

def transform_payload(raw_json: dict) -> dict:
    """Transforme l'événement brut Discord au format normalisé attendu."""
    
    # Récupération sécurisée des données adaptées au nouveau JSON
    auteur = raw_json.get('username')
    contenu = raw_json.get('message')
    
    if not auteur or not contenu:
        raise ValueError("Champs obligatoires manquants: 'username' ou 'message'")
    
    # Formattage et vérification de la date
    # Si la date n'est pas fournie, on utilise l'instant présent par défaut
    date_str = raw_json.get('timestamp')
    if not date_str:
        date_str = datetime.utcnow().isoformat()
    
    # Mapping cible
    return {
        'contact': auteur,
        'origin': 'Discord',
        'body': contenu,
        'date': date_str
    }

async def consume_and_transform():
    """Boucle asynchrone de consommation et production Kafka."""
    
    consumer_conf = {
        'bootstrap.servers': KAFKA_BROKER,
        'group.id': GROUP_ID,
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': False # Contrôle manuel des Offsets 
    }
    
    producer_conf = {
        'bootstrap.servers': KAFKA_BROKER
    }

    consumer = Consumer(consumer_conf)
    producer = Producer(producer_conf)

    consumer.subscribe([SOURCE_TOPIC])
    logger.info(f"Micro-service démarré. À l'écoute du topic: '{SOURCE_TOPIC}'...")

    loop = asyncio.get_running_loop()

    try:
        while True:
            # Poll non-bloquant depuis un executor afin de conserver la nature asynchrone de l'Event Loop
            msg = await loop.run_in_executor(None, consumer.poll, 1.0)
            
            # Servir les "callbacks" du Producer (traite le retour d'accusé de réception des messages produits)
            producer.poll(0)

            if msg is None:
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    # Fin de partition (ce n'est pas une anomalie)
                    continue
                else:
                    logger.error(f"[Consumer] Erreur: {msg.error()}")
                    continue

            raw_value = ""
            try:
                # 1. Lecture / Extraction
                raw_value = msg.value().decode('utf-8')
                raw_json = json.loads(raw_value)
                
                # 2. Transformation
                normalized_json = transform_payload(raw_json)
                
                # 3. Production asynchrone vers le nouveau Topic
                producer.produce(
                    topic=TARGET_TOPIC,
                    value=json.dumps(normalized_json).encode('utf-8'),
                    callback=delivery_report
                )
                
                # 4. Enregistrement (commit) synchronisé après un succès
                consumer.commit(msg, asynchronous=False)
                logger.info(f"[Transformation] Message transformé depuis {normalized_json['contact']}")

            except json.JSONDecodeError as decode_err:
                # Erreur interceptée si le JSON est malformé, on route vers la DLQ (TF-DLQ)
                logger.error(f"[Transformation] JSON malformé: {decode_err} | Envoi vers DLQ")
                dlq_msg = {"error": str(decode_err), "raw_value": raw_value, "time": datetime.utcnow().isoformat()}
                producer.produce(topic=DLQ_TOPIC, value=json.dumps(dlq_msg).encode('utf-8'), callback=delivery_report)
                consumer.commit(msg, asynchronous=False)
            except Exception as e:
                logger.error(f"[Transformation] Erreur inattendue: {e} | Envoi vers DLQ")
                dlq_msg = {"error": str(e), "raw_value": raw_value, "time": datetime.utcnow().isoformat()}
                producer.produce(topic=DLQ_TOPIC, value=json.dumps(dlq_msg).encode('utf-8'), callback=delivery_report)
                consumer.commit(msg, asynchronous=False)

    except asyncio.CancelledError:
        logger.info("Arrêt demandé par le système.")
    finally:
        logger.info("Flush des messages persistants et fermeture propre des connexions...")
        # S'assurer que les buffers en mémoire soient bien envoyés à Kafka
        producer.flush(timeout=5)
        consumer.close()

if __name__ == '__main__':
    try:
        asyncio.run(consume_and_transform())
    except KeyboardInterrupt:
        logger.info("Interruption manuelle (Ctrl+C). Service arrêté.")
