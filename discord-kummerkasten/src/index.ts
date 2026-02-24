import { Client, GatewayIntentBits, REST, Routes, SlashCommandBuilder } from 'discord.js';
import { sendToKafka } from './kafka';
import * as dotenv from 'dotenv';

dotenv.config();

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
  ],
});

const commands = [
  new SlashCommandBuilder()
    .setName('ticket')
    .setDescription('Submit a ticket')
    .addStringOption(option =>
      option
        .setName('message')
        .setDescription('Your ticket message')
        .setRequired(true)
    )
    .toJSON(),
];

client.once('ready', async () => {
  console.log(`Logged in as ${client.user?.tag}!`);
  
  // Register slash commands
  const rest = new REST({ version: '10' }).setToken(process.env.DISCORD_TOKEN!);
  
  try {
    console.log('Started refreshing application (/) commands.');
    
    await rest.put(
      Routes.applicationCommands(process.env.DISCORD_CLIENT_ID!),
      { body: commands },
    );
    
    console.log('Successfully reloaded application (/) commands.');
  } catch (error) {
    console.error(error);
  }
});

client.on('interactionCreate', async interaction => {
  if (!interaction.isChatInputCommand()) return;

  if (interaction.commandName === 'ticket') {
    const message = interaction.options.getString('message', true);
    const username = interaction.user.username;
    const timestamp = new Date().toISOString();

    const ticketData = {
      message,
      username,
      timestamp,
    };

    try {
      await sendToKafka(ticketData);
      await interaction.reply({
        embeds: [{
          author: {
            name: interaction.user.username,
            icon_url: interaction.user.displayAvatarURL(),
          },
          title: '✅ Ticket Submitted',
          color: 3066993, // Green color
          fields: [
            {
              name: 'Content',
              value: message.length > 1018 
                ? '```\n' + message.substring(0, 1015) + '...\n```' 
                : '```\n' + message + '\n```',
              inline: false,
            },
          ],
          timestamp: timestamp,
        }],
      });
      console.log('Ticket submitted:', ticketData);
    } catch (error) {
      console.error('Error submitting ticket:', error);
      await interaction.reply({
        embeds: [{
          title: '⚠️ Submission Failed',
          color: 15158332, // Red color
          fields: [
            {
              name: 'Error',
              value: 'Failed to submit ticket. Please try again later.',
              inline: false,
            },
          ],
          timestamp: timestamp,
        }],
        ephemeral: true,
      });
    }
  }
});

client.login(process.env.DISCORD_TOKEN);
