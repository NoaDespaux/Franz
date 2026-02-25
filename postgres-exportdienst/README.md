# Postgres Exportdienst

Postgres Exportdienst is a Go service that consumes labeled tickets from a Kafka topic and persists them into a PostgreSQL database.

The name "postgres-exportdienst" translates to "postgres export service" in German.

## Overview

1. **Consumes** labeled tickets from the `tickets-labeled` Kafka topic.
2. **Parses** the JSON payload into a structured ticket object.
3. **Inserts** each ticket as a row into the `tickets` PostgreSQL table.
4. **Creates** the table automatically on startup if it does not exist.

## Message Format

**Incoming (`tickets-labeled`):**

```json
{
  "formattedTicket": {
    "contact": "john.doe@example.com",
    "origin": "email",
    "date": 1771925400000,
    "body": "I want to see the user's phone number on the profile"
  },
  "category": "FRONT",
  "priority": "LOW",
  "type": "FEATURE_REQUEST"
}
```

## Database Schema

Table: `tickets`

| Column | Type | Description |
| ------ | ---- | ----------- |
| `id` | `SERIAL` | Auto-incremented primary key |
| `contact` | `TEXT` | Contact identifier (e.g. email) |
| `origin` | `TEXT` | Source channel (e.g. email, Discord) |
| `date` | `TIMESTAMPTZ` | Ticket date, converted from epoch milliseconds |
| `body` | `TEXT` | Ticket message body |
| `category` | `TEXT` | LLM-assigned category (e.g. `FRONT`, `BACK`) |
| `priority` | `TEXT` | LLM-assigned priority (e.g. `LOW`, `HIGH`) |
| `type` | `TEXT` | LLM-assigned type (e.g. `FEATURE_REQUEST`, `BUG`) |

## Environment Variables

| Variable | Description | Default |
| -------- | ----------- | ------- |
| `KAFKA_BROKERS` | Comma-separated list of Kafka brokers | `localhost:9092` |
| `KAFKA_TOPIC` | Topic to consume labeled tickets from | `tickets-labeled` |
| `CONSUMER_GROUP` | Kafka consumer group ID | `postgres-exportdienst` |
| `POSTGRES_DSN` | PostgreSQL connection string | `postgres://postgres:postgres@localhost:5432/tickets?sslmode=disable` |

## Running with Docker Compose

From the project root:

```bash
docker compose up -d --build postgres-exportdienst
```

> Requires `kafka` and `postgres` to be healthy first. Docker Compose handles this via `depends_on`.
