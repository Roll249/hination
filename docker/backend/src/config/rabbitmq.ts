import amqp, { Connection, Channel } from 'amqplib';
import { logger } from './logger.js';

let connection: Connection | null = null;
let channel: Channel | null = null;

const QUEUE_NAME = 'scoring_jobs';
const EXCHANGE_NAME = 'scoring_exchange';
const DEAD_LETTER_QUEUE = 'scoring_jobs_dlq';

export async function initializeRabbitMQ(): Promise<void> {
  const url = `amqp://${process.env.RABBITMQ_USER || 'guest'}:${process.env.RABBITMQ_PASS || 'guest'}@${process.env.RABBITMQ_HOST || 'localhost'}:${process.env.RABBITMQ_PORT || '5672'}/${process.env.RABBITMQ_VHOST || '/'}`;
  
  connection = await amqp.connect(url);
  channel = await connection.createChannel();
  
  // Set up dead letter exchange
  await channel.assertExchange('dlx', 'direct', { durable: true });
  
  // Set up dead letter queue
  await channel.assertQueue(DEAD_LETTER_QUEUE, {
    durable: true
  });
  await channel.bindQueue(DEAD_LETTER_QUEUE, 'dlx', QUEUE_NAME);
  
  // Set up main exchange
  await channel.assertExchange(EXCHANGE_NAME, 'direct', { durable: true });
  
  // Set up main queue with dead letter config
  await channel.assertQueue(QUEUE_NAME, {
    durable: true,
    arguments: {
      'x-dead-letter-exchange': 'dlx',
      'x-dead-letter-routing-key': QUEUE_NAME
    }
  });
  await channel.bindQueue(QUEUE_NAME, EXCHANGE_NAME, QUEUE_NAME);
  
  // Prefetch for worker scaling
  await channel.prefetch(1);
  
  connection.on('error', (err) => {
    logger.error('RabbitMQ connection error:', err);
  });
  
  connection.on('close', () => {
    logger.warn('RabbitMQ connection closed');
  });
  
  logger.info('RabbitMQ connected and queues initialized');
}

export function getChannel(): Channel {
  if (!channel) {
    throw new Error('RabbitMQ channel not initialized');
  }
  return channel;
}

export interface ScoringJobMessage {
  jobId: string;
  studentId: string;
  answers: unknown[];
  metadata: Record<string, unknown>;
  timestamp: string;
}

export async function publishScoringJob(job: ScoringJobMessage): Promise<boolean> {
  const ch = getChannel();
  const message = Buffer.from(JSON.stringify(job));
  
  return ch.publish(EXCHANGE_NAME, QUEUE_NAME, message, {
    persistent: true,
    contentType: 'application/json',
    timestamp: Date.now()
  });
}

export async function consumeScoringJobs(
  handler: (job: ScoringJobMessage) => Promise<void>
): Promise<void> {
  const ch = getChannel();
  
  await ch.consume(QUEUE_NAME, async (msg) => {
    if (!msg) return;
    
    try {
      const job: ScoringJobMessage = JSON.parse(msg.content.toString());
      await handler(job);
      ch.ack(msg);
    } catch (error) {
      logger.error('Error processing job:', error);
      // Reject and send to DLQ
      ch.nack(msg, false, false);
    }
  });
}

export async function closeRabbitMQ(): Promise<void> {
  if (channel) {
    await channel.close();
  }
  if (connection) {
    await connection.close();
  }
}
