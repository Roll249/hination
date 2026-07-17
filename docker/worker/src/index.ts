import dotenv from 'dotenv';
import { logger } from './config/logger.js';
import { initializeRabbitMQ, consumeJobs, closeRabbitMQ } from './config/rabbitmq.js';
import { pool } from './config/database.js';
import { processScoringJob } from './services/scoringProcessor.js';

dotenv.config();

// Graceful shutdown
async function shutdown() {
  logger.info('Worker shutting down...');
  
  try {
    await closeRabbitMQ();
    await pool.end();
    logger.info('Worker shutdown complete');
    process.exit(0);
  } catch (error) {
    logger.error('Error during shutdown:', error);
    process.exit(1);
  }
}

process.on('SIGTERM', shutdown);
process.on('SIGINT', shutdown);

async function start() {
  try {
    logger.info('Starting Hination Worker...');
    
    // Initialize RabbitMQ connection
    await initializeRabbitMQ();
    
    // Start consuming jobs
    await consumeJobs(processScoringJob);
    
    logger.info('Worker is running and waiting for jobs');
    
  } catch (error) {
    logger.error('Failed to start worker:', error);
    process.exit(1);
  }
}

start();
