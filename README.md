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

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.x (for client applications)

### Running the Service

Start the Kafka infrastructure using Docker Compose:

```bash
docker-compose up -d
```

This will start:

- Kafka broker(s)
- Any additional supporting services

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
