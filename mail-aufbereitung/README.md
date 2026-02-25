# Mail Aufbereitung Service

The `mail-aufbereitung` service is a Python-based microservice that acts as the transformation layer for incoming emails. It consumes raw email events from Kafka, normalizes them into a standard ticket format, and produces them to the central ticketing topic.

This service is the email equivalent of `discord-aufbereitung`.

## Features

- **Kafka Consumer:** Listens to the `mailMSG` topic for raw email JSON payloads.
- **Validation & Sanitization:** Ensures that required fields (`sender`, `message`, `timestamp`) are present and valid.
- **Data Normalization:** Maps the email-specific fields to the generic ticket format:
  - `sender` → `contact`
  - `subject` + `message` → `body` (Subject is prepended to the body)
  - Sets `origin` hardcoded to `"Email"`
- **Kafka Producer:** Publishes the normalized ticket to the `tickets-formatted` topic.
- **Dead Letter Queue (DLQ):** Routes malformed JSON or invalid payloads to `tickets-formatted-dlq` to prevent consumer blocking.

## Architecture

1.  **Source Topic:** `mailMSG`
2.  **Service:** `mail-aufbereitung` (Python script using `confluent-kafka` and `asyncio`).
3.  **Target Topic:** `tickets-formatted`
4.  **DLQ Topic:** `tickets-formatted-dlq`

### Payload Transformation Example

**Input (from `mailMSG`):**
```json
{
  "sender": "client@example.com",
  "subject": "[TICKET] Billing Issue",
  "message": "Hello,\nI have an issue with my latest invoice.",
  "timestamp": "2026-02-25T10:00:00.000Z"
}
```

**Output (to `tickets-formatted`):**
```json
{
  "contact": "client@example.com",
  "origin": "Email",
  "body": "[[TICKET] Billing Issue]\n\nHello,\nI have an issue with my latest invoice.",
  "date": "2026-02-25T10:00:00.000Z"
}
```

## Configuration

Environment variables are used to configure the Kafka connections:

| Environment Variable | Description | Default Value |
| :--- | :--- | :--- |
| `KAFKA_BROKER` | Address of the Kafka broker. | `localhost:9092` |
| `SOURCE_TOPIC` | Kafka topic to consume raw emails from. | `mailMSG` |
| `TARGET_TOPIC` | Kafka topic where formatted tickets will be published. | `tickets-formatted` |
| `DLQ_TOPIC` | Kafka topic for messages that fail validation/parsing. | `tickets-formatted-dlq` |
| `GROUP_ID` | Kafka consumer group ID for this service. | `mail-aufbereitung` |

## Local Development

1. Ensure the Kafka broker and `mail-kummerkasten` are running.
2. Build and start this service via Docker Compose:
   ```bash
   docker compose up -d --build mail-aufbereitung
   ```
3. Test the flow by sending a mock email (using `send_test_mail.py` in the `mail-kummerkasten` folder) and check the logs:
   ```bash
   docker compose logs -f mail-aufbereitung
   ```
