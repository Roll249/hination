import { ScoringJobMessage } from '../config/rabbitmq.js';
import { updateJobStatus, query } from '../config/database.js';
import { AIService } from './aiService.js';
import { logger } from '../config/logger.js';

const aiService = new AIService();

export async function processScoringJob(job: ScoringJobMessage): Promise<void> {
  const { jobId, studentId, answers, metadata } = job;

  logger.info(`Processing job ${jobId}`, { studentId });

  // Update status to processing
  await updateJobStatus(jobId, 'processing');

  try {
    // Get job from database to check max retries
    const result = await query(
      'SELECT max_retries, retry_count FROM scoring_jobs WHERE id = $1',
      [jobId]
    );

    if (result.rows.length === 0) {
      throw new Error(`Job ${jobId} not found in database`);
    }

    const jobData = result.rows[0];

    if (jobData.retry_count >= jobData.max_retries) {
      throw new Error(`Job ${jobId} exceeded max retries`);
    }

    // Call AI service
    const aiResponse = await aiService.grade({
      jobId,
      studentId,
      answers,
      metadata
    });

    // Extract score from AI response
    const score = aiResponse.score;
    const feedback = aiResponse.feedback;
    const breakdown = aiResponse.breakdown;

    // Prepare result
    const resultData = {
      score,
      feedback,
      breakdown,
      gradedAt: new Date().toISOString(),
      gradingDuration: Date.now() - new Date(job.timestamp).getTime()
    };

    // Update job as completed
    await updateJobStatus(
      jobId,
      'completed',
      resultData,
      aiResponse
    );

    logger.info(`Job ${jobId} completed successfully`, {
      studentId,
      score
    });

  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';

    logger.error(`Job ${jobId} failed:`, { error: errorMessage });

    // Check if it's a retriable error
    const retriableErrors = ['AI_SERVICE_RATE_LIMITED', 'ECONNREFUSED', 'ETIMEDOUT'];

    if (retriableErrors.some(e => errorMessage.includes(e))) {
      // Will be retried by RabbitMQ consumer
      throw error;
    }

    // Update job as failed (non-retriable)
    await updateJobStatus(jobId, 'failed', undefined, undefined, errorMessage);

    logger.error(`Job ${jobId} marked as failed (non-retriable)`, {
      studentId,
      error: errorMessage
    });
  }
}
