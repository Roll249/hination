import { Request, Response, NextFunction } from 'express';
import crypto from 'crypto';
import { logger } from '../config/logger.js';

export interface StaticTokenRequest extends Request {
  apiKeyName?: string;
}

export function staticTokenMiddleware(
  req: StaticTokenRequest,
  res: Response,
  next: NextFunction
): void {
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    res.status(401).json({ error: 'Missing or invalid authorization header' });
    return;
  }
  
  const token = authHeader.substring(7);
  const configuredToken = process.env.STATIC_API_TOKEN;
  
  if (!configuredToken) {
    logger.error('STATIC_API_TOKEN not configured');
    res.status(500).json({ error: 'Server configuration error' });
    return;
  }
  
  // Constant-time comparison to prevent timing attacks
  const tokenBuffer = crypto.createHash('sha256').update(token).digest();
  const configuredBuffer = crypto.createHash('sha256').update(configuredToken).digest();
  
  if (!crypto.timingSafeEqual(tokenBuffer, configuredBuffer)) {
    logger.warn(`Invalid static token attempt from IP: ${req.ip}`);
    res.status(401).json({ error: 'Invalid API token' });
    return;
  }
  
  // Optionally log the request
  logger.info(`Static token API access: ${req.method} ${req.path}`, {
    ip: req.ip,
    userAgent: req.headers['user-agent']
  });
  
  req.apiKeyName = 'static_scoring_token';
  next();
}
