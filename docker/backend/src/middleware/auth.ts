import { Request, Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';
import { query } from '../config/database.js';
import { isTokenBlacklisted } from '../config/redis.js';
import { logger } from '../config/logger.js';

export interface JWTPayload {
  sub: string;
  jti: string;
  username: string;
  role: string;
  iat: number;
  exp: number;
}

export interface AuthenticatedRequest extends Request {
  user?: JWTPayload;
}

export async function authMiddleware(
  req: AuthenticatedRequest,
  res: Response,
  next: NextFunction
): Promise<void> {
  try {
    const authHeader = req.headers.authorization;
    
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      res.status(401).json({ error: 'Missing or invalid authorization header' });
      return;
    }
    
    const token = authHeader.substring(7);
    const secret = process.env.JWT_ACCESS_SECRET;
    
    if (!secret) {
      logger.error('JWT_ACCESS_SECRET not configured');
      res.status(500).json({ error: 'Server configuration error' });
      return;
    }
    
    const decoded = jwt.verify(token, secret) as JWTPayload;
    
    // Check if token is blacklisted
    const isBlacklisted = await isTokenBlacklisted(decoded.jti);
    if (isBlacklisted) {
      res.status(401).json({ error: 'Token has been revoked' });
      return;
    }
    
    // Optionally verify user still exists and is active
    const result = await query(
      'SELECT id, username, role, is_active FROM users WHERE id = $1',
      [decoded.sub]
    );
    
    if (result.rows.length === 0 || !result.rows[0].is_active) {
      res.status(401).json({ error: 'User not found or inactive' });
      return;
    }
    
    req.user = decoded;
    next();
  } catch (error) {
    if (error instanceof jwt.TokenExpiredError) {
      res.status(401).json({ error: 'Token expired' });
      return;
    }
    if (error instanceof jwt.JsonWebTokenError) {
      res.status(401).json({ error: 'Invalid token' });
      return;
    }
    logger.error('Auth middleware error:', error);
    res.status(500).json({ error: 'Authentication error' });
  }
}

export function requireRole(...roles: string[]) {
  return (req: AuthenticatedRequest, res: Response, next: NextFunction): void => {
    if (!req.user) {
      res.status(401).json({ error: 'Not authenticated' });
      return;
    }
    
    if (!roles.includes(req.user.role)) {
      res.status(403).json({ error: 'Insufficient permissions' });
      return;
    }
    
    next();
  };
}
