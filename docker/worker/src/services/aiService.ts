import axios, { AxiosError } from 'axios';
import { logger } from '../config/logger.js';

export interface AIGradingRequest {
  jobId: string;
  studentId: string;
  answers: unknown[];
  metadata?: Record<string, unknown>;
}

export interface AIGradingResponse {
  score: number;
  feedback: string;
  breakdown: Record<string, number>;
  metadata?: Record<string, unknown>;
}

export class AIService {
  private apiUrl: string;
  private apiKey: string;

  constructor() {
    this.apiUrl = process.env.AI_API_URL || 'http://localhost:8000/api/grade';
    this.apiKey = process.env.AI_API_KEY || '';
  }

  async grade(request: AIGradingRequest): Promise<AIGradingResponse> {
    logger.info(`Calling AI service for job ${request.jobId}`, {
      studentId: request.studentId,
      answersCount: request.answers.length
    });

    try {
      const response = await axios.post<AIGradingResponse>(
        this.apiUrl,
        {
          student_id: request.studentId,
          answers: request.answers,
          metadata: request.metadata
        },
        {
          headers: {
            'Content-Type': 'application/json',
            ...(this.apiKey && { 'Authorization': `Bearer ${this.apiKey}` })
          },
          timeout: 120000 // 2 minutes timeout
        }
      );

      logger.info(`AI service response for job ${request.jobId}`, {
        score: response.data.score
      });

      return response.data;
    } catch (error) {
      if (error instanceof AxiosError) {
        logger.error(`AI service error for job ${request.jobId}:`, {
          status: error.response?.status,
          message: error.message,
          data: error.response?.data
        });
        
        if (error.response?.status === 429) {
          throw new Error('AI_SERVICE_RATE_LIMITED');
        }
        if (error.response?.status === 401) {
          throw new Error('AI_SERVICE_AUTH_FAILED');
        }
      }
      
      throw new Error(`AI service call failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async healthCheck(): Promise<boolean> {
    try {
      const healthUrl = this.apiUrl.replace('/grade', '/health');
      const response = await axios.get(healthUrl, { timeout: 5000 });
      return response.status === 200;
    } catch {
      return false;
    }
  }
}
