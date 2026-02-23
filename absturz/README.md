# Absturz

Absturz is a Go-based service that reads error messages from a Kafka topic and reports them to Discord via webhooks. The name "Absturz" is German for "crash" or "failure", reflecting its purpose of handling and reporting issues.

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
| `KAFKA_TOPIC` | Kafka topic to consume from | `dlz` |
| `CONSUMER_GROUP` | Kafka consumer group ID | `absturz` |
| `DISCORD_WEBHOOK_URL` | Discord webhook URL (required) | - |

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
  -e KAFKA_TOPIC=dlq \
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
    - KAFKA_TOPIC=dlq
    - CONSUMER_GROUP=absturz
    - DISCORD_WEBHOOK_URL=${DISCORD_WEBHOOK_URL}
  depends_on:
    - kafka
  restart: unless-stopped
```

## How It Works

1. **Kafka Consumer**: Connects to Kafka using the Sarama library and joins a consumer group
2. **Message Processing**: Reads messages from the configured topic
3. **Discord Notification**: Formats each message as a Discord embed and sends it via webhook
4. **Offset Management**: Marks messages as processed after successful delivery

## Message Format

Messages sent to Discord include:

- Title indicating an issue was reported
- Message content (truncated to 1024 characters if needed)
- Timestamp of when the message was received
- Color-coded embed (red for errors)

## Error Handling

- If Discord webhook fails, the error is logged but processing continues
- Kafka consumer errors are logged to stdout
- Graceful shutdown on SIGINT/SIGTERM signals

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
