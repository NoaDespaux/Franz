# Absturz

Absturz is a Go-based service that monitors multiple Dead Letter Queue (DLQ) topics in Kafka and reports errors to Discord via webhooks.

## Features

- Monitor multiple DLQ topics simultaneously
- Concurrent consumers for each topic
- Color-coded Discord notifications per topic
- Automatic topic name identification in alerts
- Graceful shutdown handling

## Prerequisites

- Go 1.21 or higher
- Access to a Kafka cluster
- Discord webhook URL

## Configuration

The service is configured via environment variables. Copy `.env.example` to `.env` and update the values:

```bash
cp .env.example .env
```

### Environment Variables

| Variable | Description | Default |
| -------- | ----------- | ------- |
| `KAFKA_BROKERS` | Comma-separated list of Kafka brokers | `localhost:9092` |
| `KAFKA_TOPICS` | Comma-separated list of DLQ topics to monitor | `dlq` |
| `CONSUMER_GROUP` | Kafka consumer group ID | `absturz` |
| `DISCORD_WEBHOOK_URL` | Discord webhook URL (required) | - |

**Example:**

```bash
KAFKA_BROKERS=kafka1:9092,kafka2:9092
KAFKA_TOPICS=discord-dlq,processing-dlq,enrichment-dlq
CONSUMER_GROUP=absturz
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

### Discord Webhook Setup

1. Go to your Discord server settings
2. Navigate to Integrations → Webhooks
3. Create a new webhook
4. Copy the webhook URL and set it as `DISCORD_WEBHOOK_URL`

## Running Locally

### Install Dependencies

```bash
go mod download
```

### Run the Service

```bash
go run main.go
```

## Docker

### Build the Image

```bash
docker build -t absturz .
```

### Run with Docker

```bash
docker run -it --rm \
  -e KAFKA_BROKERS=kafka:9092 \
  -e KAFKA_TOPICS=discord-dlq,processing-dlq \
  -e CONSUMER_GROUP=absturz \
  -e DISCORD_WEBHOOK_URL=your_webhook_url \
  absturz
```

### Run with Docker Compose

Add to your `docker-compose.yml`:

```yaml
absturz:
  build: ./absturz
  environment:
    - KAFKA_BROKERS=kafka:9092
    - KAFKA_TOPICS=discord-dlq,processing-dlq,enrichment-dlq
    - CONSUMER_GROUP=absturz
    - DISCORD_WEBHOOK_URL=${DISCORD_WEBHOOK_URL}
  depends_on:
    - kafka
  restart: unless-stopped
```

## How It Works

1. **Multi-Topic Monitoring**: Creates a separate consumer goroutine for each configured DLQ topic
2. **Concurrent Processing**: All topics are monitored simultaneously with independent Kafka readers
3. **Message Processing**: Reads messages from each configured topic
4. **Discord Notification**: Formats each message as a Discord embed with:
   - Topic name in the title
   - Color-coded by topic (auto-generated from topic name)
   - DLQ topic field showing the source
   - Message content (formatted as JSON if applicable)
5. **Offset Management**: Marks messages as processed after successful delivery
6. **Graceful Shutdown**: Properly closes all consumers on SIGINT/SIGTERM

## Message Format

Messages sent to Discord include:

- Title indicating the DLQ topic that failed (e.g., "⚠️ Processing Failed - discord-dlq")
- DLQ Topic field showing the source topic
- Message content (formatted as JSON if applicable, truncated to 1024 characters if needed)
- Timestamp of when the message was received
- Color-coded embed (unique color per topic, generated from topic name hash)

## Error Handling

- If Discord webhook fails, the error is logged but processing continues
- Each topic consumer handles errors independently
- Kafka consumer errors are logged to stdout
- Graceful shutdown waits for all consumer goroutines to complete

## Development

### Project Structure

```txt
absturz/
├── main.go           # Main application code
├── go.mod            # Go module definition
├── Dockerfile        # Docker build configuration
├── .env.example      # Example environment variables
└── README.md         # This file
```

### Dependencies

- [segmentio/kafka-go](https://github.com/segmentio/kafka-go) - Minimal Kafka client for Go

## License

This project is part of the Franz ecosystem.
