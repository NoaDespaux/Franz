import { Client, GatewayIntentBits, TextChannel, CategoryChannel, ChannelType, EmbedBuilder } from 'discord.js';
import { startKafkaConsumer, stopKafkaConsumer } from './kafka';
import * as dotenv from 'dotenv';

dotenv.config();

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
  ],
});

interface LabeledTicket {
  formattedTicket: {
    contact: string;
    origin: string;
    date: string;
    body: string;
  };
  category: string;
  priority: string;
  type: string;
}

async function createTicketChannel(ticket: LabeledTicket): Promise<void> {
  if (!client.user) {
    console.error('Discord client not ready');
    return;
  }

  const guildId = process.env.DISCORD_GUILD_ID;
  
  // Determine which category to use based on ticket type
  const ticketType = ticket.type.toLowerCase();
  let categoryId: string | undefined;
  
  if (ticketType.includes('bug')) {
    categoryId = process.env.DISCORD_CATEGORY_BUG_ID;
  } else if (ticketType.includes('feature')) {
    categoryId = process.env.DISCORD_CATEGORY_FEATURE_ID;
  } else {
    console.warn(`Ticket type "${ticket.type}" is neither bug nor feature. Skipping channel creation.`);
    return;
  }

  if (!guildId || !categoryId) {
    console.error('Missing DISCORD_GUILD_ID or category ID environment variables');
    console.error(`Ticket type: ${ticket.type}, Category ID: ${categoryId}`);
    return;
  }

  try {
    const guild = await client.guilds.fetch(guildId);
    const category = await guild.channels.fetch(categoryId) as CategoryChannel;

    if (!category || category.type !== ChannelType.GuildCategory) {
      console.error('Invalid category ID or category not found');
      return;
    }

    // Build channel name: category-priority-contact-counter
    const sanitizedCategory = ticket.category.toLowerCase().replace(/[^a-z0-9-_]/g, '-');
    const sanitizedPriority = ticket.priority.toLowerCase().replace(/[^a-z0-9-_]/g, '-');
    const sanitizedContact = ticket.formattedTicket.contact.toLowerCase().replace(/[^a-z0-9-_]/g, '-');
    const baseChannelName = `${sanitizedCategory}-${sanitizedPriority}-${sanitizedContact}`;
    
    // Find existing channels with the same base name to determine counter
    const existingChannels = category.children.cache.filter(ch => 
      ch.name.startsWith(baseChannelName + '-')
    );
    
    const counter = existingChannels.size + 1;
    const channelName = `${baseChannelName}-${counter}`.substring(0, 100);

    // Create the channel
    const channel = await guild.channels.create({
      name: channelName,
      type: ChannelType.GuildText,
      parent: category.id,
      topic: `Ticket from ${ticket.formattedTicket.contact} - ${ticket.category} | ${ticket.priority} | ${ticket.type}`,
    });

    console.log(`Created channel: ${channel.name}`);

    // Post the ticket details as an embed
    const embed = new EmbedBuilder()
      .setTitle('New Ticket')
      .setColor(getPriorityColor(ticket.priority))
      .addFields(
        { name: 'Contact', value: ticket.formattedTicket.contact, inline: true },
        { name: 'Origin', value: ticket.formattedTicket.origin, inline: true },
        { name: 'Date', value: new Date(ticket.formattedTicket.date).toLocaleString(), inline: false },
        { name: 'Category', value: ticket.category, inline: true },
        { name: 'Priority', value: ticket.priority, inline: true },
        { name: 'Type', value: ticket.type, inline: true },
        { name: 'Message', value: ticket.formattedTicket.body.length > 1024 
          ? ticket.formattedTicket.body.substring(0, 1021) + '...' 
          : ticket.formattedTicket.body, 
          inline: false 
        }
      )
      .setTimestamp(new Date(ticket.formattedTicket.date));

    await channel.send({ embeds: [embed] });
    console.log(`Posted ticket details to channel: ${channel.name}`);

  } catch (error) {
    console.error('Error creating ticket channel:', error);
  }
}

function getPriorityColor(priority: string): number {
  switch (priority.toLowerCase()) {
    case 'high':
    case 'critical':
      return 0xED4245; // Red
    case 'medium':
      return 0xFEE75C; // Yellow
    case 'low':
      return 0x57F287; // Green
    default:
      return 0x5865F2; // Blurple
  }
}

client.once('ready', async () => {
  console.log(`Logged in as ${client.user?.tag}!`);
  console.log('Discord Exportdienst is ready to create ticket channels');

  // Start Kafka consumer
  const kafkaBrokers = (process.env.KAFKA_BROKERS || 'localhost:9092').split(',');
  const kafkaTopic = process.env.KAFKA_TOPIC || 'tickets-labeled';
  const consumerGroup = process.env.CONSUMER_GROUP || 'discord-exportdienst';

  try {
    await startKafkaConsumer(kafkaBrokers, kafkaTopic, consumerGroup, createTicketChannel);
    console.log('Kafka consumer started successfully');
  } catch (error) {
    console.error('Failed to start Kafka consumer:', error);
    process.exit(1);
  }
});

client.on('error', (error) => {
  console.error('Discord client error:', error);
});

// Graceful shutdown
async function shutdown() {
  console.log('Shutting down...');
  await stopKafkaConsumer();
  await client.destroy();
  process.exit(0);
}

process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);

// Login to Discord
const token = process.env.DISCORD_TOKEN;
if (!token) {
  console.error('DISCORD_TOKEN environment variable is required');
  process.exit(1);
}

client.login(token).catch((error) => {
  console.error('Failed to login to Discord:', error);
  process.exit(1);
});
