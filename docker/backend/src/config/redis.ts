import Redis from 'ioredis';
import { logger } from './logger.js';

export const redis = new Redis({
  host: process.env.REDIS_HOST || 'localhost',
  port: parseInt(process.env.REDIS_PORT || '6379'),
  password: process.env.REDIS_PASSWORD,
  retryStrategy: (times) => {
    const delay = Math.min(times * 50, 2000);
    return delay;
  },
  maxRetriesPerRequest: 3,
});

redis.on('error', (err) => {
  logger.error('Redis error:', err);
});

redis.on('connect', () => {
  logger.info('Redis connected');
});

export async function initializeRedis(): Promise<void> {
  const pong = await redis.ping();
  if (pong !== 'PONG') {
    throw new Error('Redis ping failed');
  }
}

// Token blacklist for JWT invalidation
export async function blacklistToken(jti: string, expiresIn: number): Promise<void> {
  await redis.setex(`blacklist:${jti}`, expiresIn, '1');
}

export async function isTokenBlacklisted(jti: string): Promise<boolean> {
  const result = await redis.get(`blacklist:${jti}`);
  return result === '1';
}

// Rate limiting
export async function checkRateLimit(
  key: string, 
  limit: number, 
  windowSeconds: number
): Promise<{ allowed: boolean; remaining: number; resetAt: number }> {
  const now = Math.floor(Date.now() / 1000);
  const windowKey = `ratelimit:${key}:${Math.floor(now / windowSeconds)}`;
  
  const multi = redis.multi();
  multi.incr(windowKey);
  multi.ttl(windowKey);
  
  const results = await multi.exec();
  if (!results) throw new Error('Redis transaction failed');
  
  const count = results[0][1] as number;
  const ttl = results[1][1] as number;
  
  return {
    allowed: count <= limit,
    remaining: Math.max(0, limit - count),
    resetAt: now + (ttl > 0 ? ttl : windowSeconds)
  };
}
