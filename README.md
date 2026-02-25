# Franz - Kafka-Based Ticketing Service

Franz is a distributed ticketing service built on Apache Kafka, designed to handle high-throughput event streaming for ticketing operations.

## About Apache Kafka

Apache Kafka is a distributed event streaming platform capable of handling trillions of events per day. Originally developed at LinkedIn, Kafka is used for building real-time data pipelines and streaming applications.

### Key Concepts

- **Topics**: Categories or feeds to which records are published
- **Producers**: Applications that publish data to Kafka topics
- **Consumers**: Applications that subscribe to topics and process published messages
- **Brokers**: Kafka servers that store data and serve clients
- **Partitions**: Topics are split into partitions for parallelism and scalability
- **Consumer Groups**: Groups of consumers that cooperate to consume data from topics

## Project Overview

Franz leverages Kafka's distributed architecture to provide a robust ticketing system that can:

- Handle high volumes of ticket creation and updates in real-time
- Ensure message durability and fault tolerance
- Scale horizontally to meet growing demand
- Process ticket events asynchronously
- Maintain event ordering within partitions

## Architecture

The Franz ticketing service uses Kafka as its central message broker, enabling:

- **Event-Driven Processing**: Ticket lifecycle events (creation, updates, assignments, closures) are published as Kafka messages
- **Decoupled Services**: Microservices communicate through Kafka topics without direct dependencies
- **Reliable Delivery**: Kafka's replication ensures no ticket events are lost
- **Real-time Analytics**: Stream processing enables real-time ticket metrics and monitoring

### Services

#### Absturz

A Go-based monitoring service that reads error messages from the `errors` Kafka topic and sends notifications to Discord via webhooks. The name "absturz" (German for "crash") reflects its purpose of reporting system issues.

**Features:**

- Minimal dependencies (kafka-go + godotenv)
- Rich Discord embed formatting
- Graceful shutdown handling
- Consumer group support for scalability

See [absturz/README.md](absturz/README.md) for detailed documentation.

#### Discord Aufbereitung

A Python-based microservice that consumes raw messages from the Discord bot, normalizes the data format, and produces structured tickets. The name "aufbereitung" (German for "processing" or "preparation") reflects its role in transforming raw input into formatted data.

**Features:**

- Consumes raw events from Kafka topic `discordMSG`
- Normalizes data mapping `username` → `contact` and `message` → `body`
- Produces formatted tickets to Kafka topic `tickets-formatted`
- Dead Letter Queue (DLQ) routing for malformed JSON to `tickets-formatted-dlq`
- Non-blocking asynchronous consumer/producer loop using `confluent-kafka`

See [discord-aufbereitung/README.md](discord-aufbereitung/README.md) for detailed documentation.

#### Mail Kummerkasten

A Python microservice that acts as an entry point for emails into the ticketing system, bringing multi-channel support to Franz.

**Features:**
- Connects to standard IMAP servers (or local mock servers)
- Periodically polls for unread emails and safely extracts the text body
- Transforms email metadata (sender, subject, body) into a structured JSON format
- Produces events to the `mailMSG` Kafka topic

See [mail-kummerkasten/README.md](mail-kummerkasten/README.md) for detailed documentation.

#### Mail Aufbereitung

A Python-based microservice that consumes raw email events from the mail entry point, normalizes the data format (including prepending the topic subject to the body), and produces structured tickets identically to the Discord equivalent.

**Features:**
- Consumes raw events from Kafka topic `mailMSG`
- Normalizes data mapping `sender` → `contact` and `message` → `body` while setting `origin` to `"Email"`
- Produces formatted tickets to Kafka topic `tickets-formatted`
- Dead Letter Queue (DLQ) routing for malformed JSON to `tickets-formatted-dlq`

See [mail-aufbereitung/README.md](mail-aufbereitung/README.md) for detailed documentation.

#### Discord Kummerkasten

A Discord bot (TypeScript/Node.js) that allows users to submit tickets directly from Discord using the `/ticket` slash command. The name "kummerkasten" (German for "suggestion box") reflects its purpose as a ticket submission interface.

**Features:**

- Discord slash command integration (`/ticket`)
- Publishes tickets to Kafka topic `discordMSG`
- JSON message format with username, message, and timestamp
- Ephemeral replies for user privacy

See [discord-kummerkasten/README.md](discord-kummerkasten/README.md) for detailed documentation.

#### Etikett

A Java/Spring Boot microservice that uses AI-powered classification to automatically label tickets with categories, priorities, and types. The name "etikett" (German for "label" or "tag") reflects its core function of adding structured metadata to tickets.

**Features:**

- Consumes formatted tickets from Kafka topic `tickets-formatted`
- Uses Ollama LLM (llama3.1) for intelligent ticket classification
- Automatically assigns category, priority, and type labels
- Produces labeled tickets to Kafka topic `tickets-labeled`
- Dead Letter Queue (DLQ) routing for invalid tickets to `tickets-labeled-dlq`
- Validates ticket body length for reliable classification

#### Postgres Exportdienst

A Go-based data export service that persists labeled tickets from Kafka into a PostgreSQL database for long-term storage and querying. The name "postgres-exportdienst" (German for "postgres export service") reflects its role in exporting and archiving ticket data to PostgreSQL.

**Features:**

- Consumes fully labeled tickets from Kafka topic `tickets-labeled`
- Persists all ticket data to PostgreSQL for durability and reporting
- Automatically creates the tickets table on startup

See [postgres-exportdienst/README.md](postgres-exportdienst/README.md) for detailed documentation.

#### Discord Exportdienst

A TypeScript/Node.js Discord bot that creates dedicated channels for labeled tickets, enabling team collaboration directly within Discord. The name "discord-exportdienst" (German for "discord export service") reflects its role in exporting ticket data to Discord for collaborative resolution.

**Features:**

- Consumes fully labeled tickets from Kafka topic `tickets-labeled`
- Smart category routing: automatically routes bug tickets and feature requests to separate Discord categories
- Creates a new Discord channel for each ticket
- Posts embeds with ticket details (contact, origin, category, priority, type)
- Color-codes tickets based on priority (High/Critical = Red, Medium = Yellow, Low = Green)
- Sanitized channel naming for Discord compatibility
- Graceful error handling and shutdown

See [discord-exportdienst/README.md](discord-exportdienst/README.md) for detailed documentation.

### Database Schema

The tickets table is automatically created in PostgreSQL with the following structure:

```sql
CREATE TABLE IF NOT EXISTS tickets (
    id       SERIAL PRIMARY KEY,
    contact  TEXT        NOT NULL,
    origin   TEXT        NOT NULL,
    date     TIMESTAMPTZ NOT NULL,
    body     TEXT        NOT NULL,
    category TEXT        NOT NULL,
    priority TEXT        NOT NULL,
    type     TEXT        NOT NULL
)
```

#### Armaturenbrett API

A Python-based lightweight FastAPI microservice that queries the PostgreSQL database where tickets are archived. The name "armaturenbrett" (German for "dashboard") groups the visualization components together.

**Features:**
- Exposes `GET /api/tickets` for paginated access to the ticket feed.
- Exposes `GET /api/kpis` to dynamically compute PostgreSQL aggregations (Counts by priority, category, origin).
- Fully documented via auto-generated Swagger UI.

See [armaturenbrett-api/README.md](armaturenbrett-api/README.md) for detailed documentation.

#### Armaturenbrett UI

A Next.js frontend interface styled with Tailwind CSS and Shadcn UI components. It serves as the primary visual entry point for administrators to view and analyze tickets.

**Features:**
- Polling mechanism to auto-refresh data seamlessly.
- Visual representations utilizing `recharts` for priorities, categories, and platforms.
- Responsive data table containing the live feed of correctly formatted tickets.

See [armaturenbrett-ui/README.md](armaturenbrett-ui/README.md) for detailed documentation.

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.x (for client applications)
- Discord webhook URL (for error reporting via absturz)

### Running the Service

1. Copy the environment example file and configure it:

    ```bash
    cp .env.example .env
    # Edit .env and add your Discord webhook URL and bot credentials
    ```

2. Start the Kafka infrastructure using Docker Compose:

    ```bash
    docker compose up -d
    ```

This will start:

- **Kafka broker** - Message streaming platform
- **absturz** - Error reporting service that sends Kafka error messages to Discord
- **discord-kummerkasten** - Discord bot for ticket submission from Discord servers

## Use Cases

Franz's Kafka-based architecture supports various ticketing scenarios:

- **Customer Support**: Track and route support tickets across teams
- **Issue Tracking**: Manage bug reports and feature requests
- **Service Desk**: Handle IT service requests and incidents
- **Event Registration**: Process event tickets and attendee management

## Benefits of Using Kafka

- **Scalability**: Easily scale to millions of tickets
- **Durability**: All ticket events are persisted and replicated
- **Performance**: Low-latency message processing
- **Integration**: Connect with various systems through Kafka connectors
- **Event Sourcing**: Complete audit trail of all ticket state changes

## Contributing

This project is part of a streaming data architecture course demonstrating practical Kafka implementations for ticketing services.

---

*Named after Franz Kafka, because sometimes dealing with tickets feels like navigating a bureaucratic labyrinth.*
