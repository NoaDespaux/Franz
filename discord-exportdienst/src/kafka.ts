import { Kafka, Consumer, EachMessagePayload } from 'kafkajs';

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

export type TicketHandler = (ticket: LabeledTicket) => Promise<void>;

let consumer: Consumer | null = null;

export async function startKafkaConsumer(
  brokers: string[],
  topic: string,
  groupId: string,
  onTicket: TicketHandler
): Promise<void> {
  const kafka = new Kafka({
    clientId: 'discord-exportdienst',
    brokers,
  });

  consumer = kafka.consumer({ groupId });

  await consumer.connect();
  console.log('Kafka consumer connected');

  await consumer.subscribe({ topic, fromBeginning: false });
  console.log(`Subscribed to topic: ${topic}`);

  await consumer.run({
    eachMessage: async ({ topic, partition, message }: EachMessagePayload) => {
      if (!message.value) {
        console.warn('Received message with no value');
        return;
      }

      try {
        const ticketData: LabeledTicket = JSON.parse(message.value.toString());
        console.log('Received labeled ticket:', {
          contact: ticketData.formattedTicket.contact,
          category: ticketData.category,
          priority: ticketData.priority,
          type: ticketData.type,
        });

        await onTicket(ticketData);
      } catch (error) {
        console.error('Error processing message:', error);
      }
    },
  });
}

export async function stopKafkaConsumer(): Promise<void> {
  if (consumer) {
    await consumer.disconnect();
    console.log('Kafka consumer disconnected');
  }
}
