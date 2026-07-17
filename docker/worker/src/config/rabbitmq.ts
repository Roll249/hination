import amqp, { Connection, Channel, ConsumeMessage } from 'amqplib';
import { logger } from './config/logger.js';

let connection: Connection | null = null;
let channel: Channel | null = null;

const QUEUE_NAME = 'scoring_jobs';
const EXCHANGE_NAME = 'scoring_exchange';
const DEAD_LETTER_QUEUE = 'scoring_jobs_dlq';
const MAX_RETRIES = 3;

export interface ScoringJobMessage {
  jobId: string;
  studentId: string;
  answers: unknown[];
  metadata: Record<string, unknown>;
  timestamp: string;
  retryCount?: number;
}

export async function initializeRabbitMQ(): Promise<void> {
  const url = `amqp://${process.env.RABBITMQ_USER || 'guest'}:${process.env.RABBITMQ_PASS || 'guest'}@${process.env.RABBITMQ_HOST || 'localhost'}:${process.env.RABBITMQ_PORT || '5672'}/${process.env.RABBITMQ_VHOST || '/'}`;
  
  connection = await amqp.connect(url);
  channel = await connection.createChannel();
  
  // Set up dead letter exchange
  await channel.assertExchange('dlx', 'direct', { durable: true });
  
  // Set up dead letter queue
  await channel.assertQueue(DEAD_LETTER_QUEUE, { durable: true });
  await channel.bindQueue(DEAD_LETTER_QUEUE, 'dlx', QUEUE_NAME);
  
  // Set up main exchange and queue
  await channel.assertExchange(EXCHANGE_NAME, 'direct', { durable: true });
  await channel.assertQueue(QUEUE_NAME, {
    durable: true,
    arguments: {
      'x-dead-letter-exchange': 'dlx',
      'x-dead-letter-routing-key': QUEUE_NAME
    }
  });
  await channel.bindQueue(QUEUE_NAME, EXCHANGE_NAME, QUEUE_NAME);
  
  // Prefetch 1 job at a time
  await channel.prefetch(1);
  
  connection.on('error', (err) => {
    logger.error('RabbitMQ connection error:', err);
  });
  
  connection.on('close', () => {
    logger.warn('RabbitMQ connection closed, reconnecting...');
    setTimeout(initializeRabbitMQ, 5000);
  });
  
  logger.info('Worker connected to RabbitMQ');
}

export async function consumeJobs(
  handler: (job: ScoringJobMessage) => Promise<void>
): Promise<void> {
  if (!channel) {
    throw new Error('RabbitMQ channel not initialized');
  }
  
  await channel.consume(QUEUE_NAME, async (msg: ConsumeMessage | null) => {
    if (!msg) return;
    
    const job: ScoringJobMessage = JSON.parse(msg.content.toString());
    const retryCount = job.retryCount || 0;
    
    try {
      await handler(job);
      channel!.ack(msg);
    } catch (error) {
      logger.error(`Job ${job.jobId} failed:`, error);
      
      if (retryCount < MAX_RETRIES) {
        // Requeue with incremented retry count
        logger.info(`Retrying job ${job.jobId} (attempt ${retryCount + 1}/${MAX_RETRIES})`);
        
        const retryJob: ScoringJobMessage = {
          ...job,
          retryCount: retryCount + 1
        };
        
        channel!.ack(msg);
        
        // Republish to queue
        channel!.publish(
          EXCHANGE_NAME,
          QUEUE_NAME,
          Buffer.from(JSON.stringify(retryJob)),
          { persistent: true }
        );
      } else {
        // Max retries exceeded, send to DLQ
        logger.error(`Job ${job.jobId} exceeded max retries, sending to DLQ`);
        channel!.nack(msg, false, false);
      }
    }
  });
  
  logger.info(`Worker consuming from queue: ${QUEUE_NAME}`);
}

export async function closeRabbitMQ(): Promise<void> {
  if (channel) {
    await channel.close();
  }
  if (connection) {
    await connection.close();
  }
}
