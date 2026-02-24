# Discord Aufbereitung

A Python-based microservice that acts as a transformation layer (Normalizer) in the Franz ticketing architecture. 
The name "aufbereitung" translates to "processing" or "preparation" in German, accurately describing its purpose: preparing raw Discord messages for the core ticketing system.

## Overview

This service:
1. **Consumes** raw JSON events from the `discordMSG` Kafka topic (typically sent by the `discord-kummerkasten` bot).
2. **Transforms** the payloads into a normalized ticket format.
3. **Produces** the cleanly formatted tickets to the `tickets-formatted` topic.
4. **Routes** any malformed JSON messages to a Dead Letter Queue (`tickets-formatted-dlq`) to ensure fault tolerance and prevent data loss without crashing the consumer.

## Architecture Architecture

Flow of the service:
- Pulls from `discordMSG`
- Validates and Normalizes JSON
- Pushes success to `tickets-formatted`
- Pushes errors to `tickets-formatted-dlq`

## Environment Variables

| Variable | Description | Default |
| -------- | ----------- | ------- |
| `KAFKA_BROKER` | Kafka bootstrap server address | `localhost:9092` |
| `SOURCE_TOPIC` | Topic to consume raw messages from | `discordMSG` |
| `TARGET_TOPIC` | Topic to publish normalized tickets | `tickets-formatted` |
| `DLQ_TOPIC` | Topic to publish malformed messages/errors | `tickets-formatted-dlq` |
| `GROUP_ID` | Kafka consumer group ID | `discord-aufbereitung` |

## Payload Transformation Example

**Incoming Format (from Discord bot):**
```json
{
  "message": "I have an issue with my account",
  "username": "pontatot",
  "timestamp": "2026-02-24T08:32:23.255Z"
}
```

**Outgoing Format (Normalized Ticket):**
```json
{
  "contact": "pontatot",
  "origin": "Discord",
  "body": "I have an issue with my account",
  "date": "2026-02-24T08:32:23.255Z"
}
```

## Local Development

The service is written in Python using `asyncio` and `confluent-kafka` for high-performance non-blocking I/O.

To run it locally via Docker Compose (from the project root):
```bash
docker compose up -d --build discord-aufbereitung
```
