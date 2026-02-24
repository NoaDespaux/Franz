# Discord Kummerkasten Bot

A Discord bot that allows users to submit tickets via a `/ticket` command. The tickets are published to a Kafka topic for processing.

## Features

- `/ticket` slash command for submitting tickets
- Sends ticket data (message, username, timestamp) to Kafka topic `discordMSG`
- JSON formatted messages for easy processing

## Prerequisites

- Node.js 18+ and npm
- Discord Bot Token and Application Client ID
- Running Kafka broker

## Setup

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment Variables

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
DISCORD_TOKEN=your_discord_bot_token_here
DISCORD_CLIENT_ID=your_discord_application_client_id_here
KAFKA_BROKER=localhost:9092
KAFKA_TOPIC=discordMSG
```

### 3. Create Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to the "Bot" section and create a bot
4. Copy the bot token to `DISCORD_TOKEN`
5. Copy the Application ID to `DISCORD_CLIENT_ID`
6. Enable these Privileged Gateway Intents:
   - Server Members Intent (optional)
   - Message Content Intent (optional)
7. Go to OAuth2 > URL Generator
8. Select scopes: `bot`, `applications.commands`
9. Select permissions: `Send Messages`, `Use Slash Commands`
10. Use the generated URL to invite the bot to your server

## Build and Run

### Development

```bash
npm run dev
```

### Production

```bash
npm run build
npm start
```

### Deploy Commands Separately (Optional)

If you need to manually deploy slash commands:

```bash
npm run deploy
```

## Usage

Once the bot is running and invited to your server:

1. Type `/ticket` in any channel
2. Enter your ticket message
3. Submit the command
4. The bot will confirm the ticket submission

The bot sends the following JSON to the Kafka topic `discordMSG`:

```json
{
  "message": "The ticket message content",
  "username": "discord_username",
  "timestamp": "2026-02-23T12:34:56.789Z"
}
```

## Architecture

- **src/index.ts**: Main bot file with Discord client and command handling
- **src/kafka.ts**: Kafka producer setup and message sending
- **src/deploy-commands.ts**: Standalone script for deploying slash commands

## Kafka Topic

- **Topic Name**: `discordMSG`
- **Message Format**: JSON
- **Fields**:
  - `message`: The ticket content
  - `username`: Discord username of the submitter
  - `timestamp`: ISO 8601 timestamp of submission

## License

MIT
