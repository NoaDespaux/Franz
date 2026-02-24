import { Kafka, Producer } from 'kafkajs';

const kafka = new Kafka({
  clientId: 'discord-kummerkasten',
  brokers: [process.env.KAFKA_BROKER || 'localhost:9092'],
});

const producer: Producer = kafka.producer();

let isConnected = false;

async function connectProducer() {
  if (!isConnected) {
    await producer.connect();
    isConnected = true;
    console.log('Kafka producer connected');
  }
}

export async function sendToKafka(ticketData: {
  message: string;
  username: string;
  timestamp: string;
}) {
  const topic = process.env.KAFKA_TOPIC || 'discordMSG';
  
  try {
    await connectProducer();
    
    await producer.send({
      topic,
      messages: [
        {
          value: JSON.stringify(ticketData),
        },
      ],
    });
    
    console.log(`Message sent to Kafka topic: ${topic}`);
  } catch (error) {
    console.error('Error sending to Kafka:', error);
    throw error;
  }
}

// Graceful shutdown
process.on('SIGINT', async () => {
  if (isConnected) {
    await producer.disconnect();
    console.log('Kafka producer disconnected');
  }
  process.exit(0);
});
