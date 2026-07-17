import { Router, Response } from 'express';
import { v4 as uuidv4 } from 'uuid';
import { z } from 'zod';
import { query } from '../config/database.js';
import { publishScoringJob, ScoringJobMessage } from '../config/rabbitmq.js';
import { logger } from '../config/logger.js';
import { authMiddleware, AuthenticatedRequest } from '../middleware/auth.js';

export const scoringRouter = Router();

// Validation schemas
const submitScoringSchema = z.object({
  studentId: z.string().min(1).max(100),
  jobType: z.string().optional().default('grading'),
  answers: z.array(z.unknown()),
  metadata: z.record(z.unknown()).optional().default({})
});

const jobQuerySchema = z.object({
  page: z.coerce.number().min(1).optional().default(1),
  limit: z.coerce.number().min(1).max(100).optional().default(20),
  status: z.enum(['queued', 'processing', 'completed', 'failed']).optional()
});

// Submit job for scoring (Static Token auth)
scoringRouter.post('/submit', async (req, res) => {
  try {
    const validation = submitScoringSchema.safeParse(req.body);
    
    if (!validation.success) {
      res.status(400).json({ 
        error: 'Invalid request body',
        details: validation.error.errors 
      });
      return;
    }
    
    const { studentId, jobType, answers, metadata } = validation.data;
    const jobId = uuidv4();
    
    // Create job record in database
    const result = await query(
      `INSERT INTO scoring_jobs (id, student_id, job_type, status, input_data)
       VALUES ($1, $2, $3, 'queued', $4)
       RETURNING id, student_id, status, created_at`,
      [jobId, studentId, jobType, JSON.stringify({ answers, metadata })]
    );
    
    // Publish to RabbitMQ
    const message: ScoringJobMessage = {
      jobId,
      studentId,
      answers,
      metadata: { jobType, ...metadata },
      timestamp: new Date().toISOString()
    };
    
    const published = await publishScoringJob(message);
    
    if (!published) {
      // Update job status to failed if couldn't publish
      await query(
        'UPDATE scoring_jobs SET status = $1, error_message = $2 WHERE id = $3',
        ['failed', 'Failed to queue job', jobId]
      );
      
      res.status(500).json({ error: 'Failed to queue scoring job' });
      return;
    }
    
    logger.info(`Scoring job created: ${jobId} for student: ${studentId}`);
    
    res.status(202).json({
      message: 'Job accepted for processing',
      jobId,
      status: 'queued',
      createdAt: result.rows[0].created_at
    });
  } catch (error) {
    logger.error('Submit scoring error:', error);
    res.status(500).json({ error: 'Failed to submit scoring job' });
  }
});

// Get job status/result (Static Token auth)
scoringRouter.get('/jobs/:id', async (req, res) => {
  try {
    const jobId = req.params.id;
    
    const result = await query(
      `SELECT id, student_id, job_type, status, input_data, result_data, 
              ai_response, error_message, retry_count, created_at, 
              started_at, completed_at
       FROM scoring_jobs 
       WHERE id = $1`,
      [jobId]
    );
    
    if (result.rows.length === 0) {
      res.status(404).json({ error: 'Job not found' });
      return;
    }
    
    const job = result.rows[0];
    
    res.json({
      job: {
        id: job.id,
        studentId: job.student_id,
        jobType: job.job_type,
        status: job.status,
        inputData: job.input_data,
        result: job.result_data,
        aiResponse: job.ai_response,
        error: job.error_message,
        retryCount: job.retry_count,
        createdAt: job.created_at,
        startedAt: job.started_at,
        completedAt: job.completed_at
      }
    });
  } catch (error) {
    logger.error('Get job error:', error);
    res.status(500).json({ error: 'Failed to get job' });
  }
});

// List jobs (JWT auth required)
scoringRouter.get('/jobs', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const validation = jobQuerySchema.safeParse(req.query);
    
    if (!validation.success) {
      res.status(400).json({ 
        error: 'Invalid query parameters',
        details: validation.error.errors 
      });
      return;
    }
    
    const { page, limit, status } = validation.data;
    const offset = (page - 1) * limit;
    
    let whereClause = '';
    const values: unknown[] = [];
    let paramIndex = 1;
    
    if (status) {
      whereClause = `WHERE status = $${paramIndex++}`;
      values.push(status);
    }
    
    values.push(limit, offset);
    
    const result = await query(
      `SELECT id, student_id, job_type, status, result_data, error_message, 
              created_at, completed_at
       FROM scoring_jobs 
       ${whereClause}
       ORDER BY created_at DESC 
       LIMIT $${paramIndex++} OFFSET $${paramIndex}`,
      values
    );
    
    let countQuery = 'SELECT COUNT(*) FROM scoring_jobs';
    if (status) {
      countQuery += ` WHERE status = $1`;
    }
    
    const countResult = await query(
      countQuery,
      status ? [status] : []
    );
    const total = parseInt(countResult.rows[0].count);
    
    res.json({
      jobs: result.rows.map(job => ({
        id: job.id,
        studentId: job.student_id,
        jobType: job.job_type,
        status: job.status,
        result: job.result_data,
        error: job.error_message,
        createdAt: job.created_at,
        completedAt: job.completed_at
      })),
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit)
      }
    });
  } catch (error) {
    logger.error('List jobs error:', error);
    res.status(500).json({ error: 'Failed to list jobs' });
  }
});

// Retry failed job (JWT auth required)
scoringRouter.post('/jobs/:id/retry', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const jobId = req.params.id;
    
    const result = await query(
      `UPDATE scoring_jobs 
       SET status = 'queued', error_message = NULL, retry_count = retry_count + 1
       WHERE id = $1 AND status = 'failed'
       RETURNING id, student_id, status`,
      [jobId]
    );
    
    if (result.rows.length === 0) {
      res.status(404).json({ error: 'Job not found or not in failed status' });
      return;
    }
    
    const job = result.rows[0];
    
    // Re-publish to queue
    const jobData = await query(
      'SELECT input_data FROM scoring_jobs WHERE id = $1',
      [jobId]
    );
    
    const inputData = jobData.rows[0].input_data;
    
    const message: ScoringJobMessage = {
      jobId,
      studentId: job.student_id,
      answers: inputData.answers || [],
      metadata: inputData.metadata || {},
      timestamp: new Date().toISOString()
    };
    
    await publishScoringJob(message);
    
    logger.info(`Job retry queued: ${jobId}`);
    
    res.json({
      message: 'Job queued for retry',
      jobId,
      status: 'queued'
    });
  } catch (error) {
    logger.error('Retry job error:', error);
    res.status(500).json({ error: 'Failed to retry job' });
  }
});
