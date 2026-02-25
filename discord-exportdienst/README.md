# Discord Exportdienst

Discord Exportdienst is a Discord bot that consumes labeled tickets from a Kafka topic and creates dedicated Discord channels for each ticket within a specified category.

The name "discord-exportdienst" translates to "discord export service" in German.

## Features

- Consumes labeled tickets from the `tickets-labeled` Kafka topic
- Creates a new Discord channel for each ticket
- **Smart category routing**: Automatically routes tickets to different categories based on type:
  - Bug tickets → Bug category
  - Feature requests → Feature category
  - Other types → Skipped (not created)
- Posts clean embeds with ticket details (minimal emojis)
- Color-codes tickets based on priority (High/Critical = Red, Medium = Yellow, Low = Green)
- Sanitizes channel names for Discord compatibility
- Graceful shutdown handling

## How It Works

1. **Connects to Discord** using a bot token and waits for the ready event.
2. **Subscribes to Kafka** topic `tickets-labeled` (configurable).
3. **Processes each ticket** by:
   - Determining if the ticket is a bug or feature request
   - Creating a new text channel in the appropriate category
   - Naming it `{category}-{priority}-{contact}-{counter}` (e.g., `bug-high-johndoe-1`)
   - Setting the channel topic with ticket metadata
   - Posting a clean embed with all ticket details
4. **Color codes priorities** for visual differentiation
5. **Skips tickets** that are neither bugs nor features (logs a warning)

## Kafka Message Format

**Incoming (`tickets-labeled`):**

```json
{
  "formattedTicket": {
    "contact": "username",
    "origin": "Discord",
    "date": "2024-01-01T12:00:00Z",
    "body": "Ticket message content"
  },
  "category": "Technical",
  "priority": "High",
  "type": "Bug"
}
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DISCORD_TOKEN` | Discord bot token | **Required** |
| `DISCORD_GUILD_ID` | Discord server (guild) ID | **Required** |

| `DISCORD_CATEGORY_BUG_ID` | Category ID for bug tickets | **Required** |
| `DISCORD_CATEGORY_FEATURE_ID` | Category ID for feature request tickets | **Required** |
| `KAFKA_BROKERS` | Comma-separated list of Kafka brokers | `localhost:9092` |
| `KAFKA_TOPIC` | Topic to consume labeled tickets from | `tickets-labeled` |
| `CONSUMER_GROUP` | Kafka consumer group ID | `discord-exportdienst` |

## Discord Bot Setup

1. **Create a Discord Application** at https://discord.com/developers/applications
2. **Create a Bot** and copy the token
3. **Enable Intents**: Enable "Server Members Intent" and "Message Content Intent"
4. **Invite the Bot** to your server with proper permissions:
   - `MANAGE_CHANNELS` - Required to create channels
   - `SEND_MESSAGES` - Required to post ticket details
   - `EMBED_LINKS` - Required for rich embeds

   Use this permission calculator: `permissions=268436480`

5. **Get IDs**:
   - **Guild ID**: Enable Developer Mode in Discord, right-click your server → Copy ID
   - **Category IDs**: Right-click each category (Bug, Feature) → Copy ID
     - Create two categories in your Discord server (e.g., "🐛 Bugs", "✨ Features")
     - Copy each category's ID for the corresponding environment variable

## Running Locally

1. Install dependencies:
   ```bash
   npm install
   ```

2. Create a `.env` file:
   ```env
   DISCORD_TOKEN=your_bot_token_here
   DISCORD_GUILD_ID=your_guild_id_here
   DISCORD_CATEGORY_ID=your_category_id_here
   KAFKA_BROKERS=localhost:9092
   KAFKA_TOPIC=tickets-labeled
   CONSUMER_GROUP=discord-exportdienst
   ```

3. Build and run:
   ```bash
   npm run build
   npm start
   ```

## Running with Docker

Build and run the service:

```bash
docker compose up -d --build discord-exportdienst
```

## Channel Naming

Channels are created with names in the format:
- `{category}-{priority}-{contact}-{counter}`
- **Category**: Technical area (e.g., `back`, `front`, `infra`, `mobile`)
- **Priority**: Ticket priority (e.g., `high`, `medium`, `low`, `critical`)
- **Contact**: User who submitted the ticket (sanitized)
- **Counter**: Increments for each ticket from the same contact with the same category and priority
- All parts are sanitized to lowercase alphanumeric, hyphens, and underscores
- Truncated to 100 characters maximum

Examples:
- `back-high-johndoe-1` → Backend, High priority, from johndoe (first ticket)
- `back-high-johndoe-2` → Backend, High priority, from johndoe (second ticket)
- `front-low-alice-1` → Frontend, Low priority, from alice
- `infra-medium-bob-1` → Infrastructure, Medium priority, from bob
- `mobile-critical-charlie-1` → Mobile, Critical priority, from charlie

## Notes

- Discord has rate limits on channel creation (~50 channels per day for most servers)
- Channels are created in the specified category only
- Old channels are NOT automatically deleted or archived
- The bot must have appropriate permissions in the target category
