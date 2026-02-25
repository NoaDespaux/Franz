# Etikett

Etikett is a Java/Spring Boot service that automatically labels formatted tickets using a local LLM (Ollama). It consumes tickets from a Kafka topic, classifies them by category, priority, and type, then publishes the enriched result to a downstream topic.

The name "etikett" translates to "label" in German.

## Overview

1. **Consumes** formatted tickets from the `tickets-formatted` Kafka topic.
2. **Classifies** each ticket by sending the body to a local Ollama LLM instance.
3. **Produces** labeled tickets to the `tickets-labeled` topic.
4. **Routes** invalid or unclassifiable tickets to a Dead Letter Queue (`tickets-labeled-dlq`).

## Message Formats

**Incoming (`tickets-formatted`):**

```json
{
  "contact": "john.doe@example.com",
  "origin": "email",
  "date": 1771925400000,
  "body": "I want to see the user's phone number on the profile"
}
```

**Outgoing (`tickets-labeled`):**

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

## Environment Variables

| Variable | Description | Default |
| -------- | ----------- | ------- |
| `OLLAMA_BASE_URL` | Ollama API base URL | - |
| `OLLAMA_MODEL` | Model name to use for classification | - |
| `OLLAMA_TEMPERATURE` | Sampling temperature | - |
| `OLLAMA_MAX_TOKENS` | Maximum tokens in LLM response | - |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka bootstrap server address | - |
| `KAFKA_CONSUMER_GROUP_ID` | Kafka consumer group ID | `etikett` |
| `KAFKA_CONSUMER_AUTO_OFFSET_RESET` | Offset reset policy | `earliest` |
| `KAFKA_TOPIC_INPUT` | Topic to consume formatted tickets from | `tickets-formatted` |
| `KAFKA_TOPIC_OUTPUT` | Topic to publish labeled tickets to | `tickets-labeled` |
| `KAFKA_TOPIC_DLQ` | Topic for failed/invalid tickets | `tickets-labeled-dlq` |

## Running with Docker Compose

From the project root:

```bash
docker compose up -d --build etikett
```

> Requires `kafka` and `ollama` to be healthy first. Docker Compose handles this via `depends_on`.

## Building Locally

```bash
./mvnw clean package -DskipTests
java -jar target/*.jar
```
