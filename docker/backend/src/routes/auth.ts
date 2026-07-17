import { Router, Request, Response } from 'express';
import bcrypt from 'bcrypt';
import jwt from 'jsonwebtoken';
import { v4 as uuidv4 } from 'uuid';
import { query } from '../config/database.js';
import { logger } from '../config/logger.js';
import { authMiddleware, AuthenticatedRequest } from '../middleware/auth.js';

export const authRouter = Router();

// Login
authRouter.post('/login', async (req: Request, res: Response) => {
  try {
    const { username, password } = req.body;
    
    if (!username || !password) {
      res.status(400).json({ error: 'Username and password required' });
      return;
    }
    
    const result = await query(
      'SELECT id, username, password_hash, role, is_active FROM users WHERE username = $1',
      [username]
    );
    
    if (result.rows.length === 0) {
      logger.warn(`Login attempt for non-existent user: ${username}`);
      res.status(401).json({ error: 'Invalid credentials' });
      return;
    }
    
    const user = result.rows[0];
    
    if (!user.is_active) {
      res.status(401).json({ error: 'Account is disabled' });
      return;
    }
    
    const validPassword = await bcrypt.compare(password, user.password_hash);
    
    if (!validPassword) {
      logger.warn(`Failed login attempt for user: ${username}`);
      res.status(401).json({ error: 'Invalid credentials' });
      return;
    }
    
    // Generate JWT tokens
    const jti = uuidv4();
    const accessSecret = process.env.JWT_ACCESS_SECRET!;
    const refreshSecret = process.env.JWT_REFRESH_SECRET!;
    
    const accessToken = jwt.sign(
      {
        sub: user.id,
        jti,
        username: user.username,
        role: user.role
      },
      accessSecret,
      { expiresIn: '15m' }
    );
    
    const refreshToken = jwt.sign(
      {
        sub: user.id,
        jti: uuidv4(),
        type: 'refresh'
      },
      refreshSecret,
      { expiresIn: '7d' }
    );
    
    // Store refresh token hash in database
    const refreshTokenHash = await bcrypt.hash(refreshToken, 10);
    const refreshExpiryDate = new Date();
    refreshExpiryDate.setDate(refreshExpiryDate.getDate() + 7);
    
    await query(
      `INSERT INTO sessions (user_id, refresh_token_hash, user_agent, ip_address, expires_at)
       VALUES ($1, $2, $3, $4, $5)`,
      [
        user.id,
        refreshTokenHash,
        req.headers['user-agent'],
        req.ip,
        refreshExpiryDate
      ]
    );
    
    // Log successful login
    await query(
      `INSERT INTO audit_logs (user_id, action, resource_type, details, ip_address, user_agent)
       VALUES ($1, 'login', 'session', $2, $3, $4)`,
      [user.id, JSON.stringify({ jti }), req.ip, req.headers['user-agent']]
    );
    
    logger.info(`User logged in: ${username}`);
    
    res.json({
      accessToken,
      refreshToken,
      user: {
        id: user.id,
        username: user.username,
        role: user.role
      }
    });
  } catch (error) {
    logger.error('Login error:', error);
    res.status(500).json({ error: 'Login failed' });
  }
});

// Refresh token
authRouter.post('/refresh', async (req: Request, res: Response) => {
  try {
    const { refreshToken } = req.body;
    
    if (!refreshToken) {
      res.status(400).json({ error: 'Refresh token required' });
      return;
    }
    
    const refreshSecret = process.env.JWT_REFRESH_SECRET!;
    const decoded = jwt.verify(refreshToken, refreshSecret) as jwt.JwtPayload;
    
    if (decoded.type !== 'refresh') {
      res.status(401).json({ error: 'Invalid token type' });
      return;
    }
    
    // Find and verify session
    const sessions = await query(
      `SELECT s.*, u.username, u.role, u.is_active 
       FROM sessions s 
       JOIN users u ON s.user_id = u.id 
       WHERE s.user_id = $1 AND s.expires_at > NOW()`,
      [decoded.sub]
    );
    
    // Verify refresh token against stored hashes
    let validSession = null;
    for (const session of sessions.rows) {
      const valid = await bcrypt.compare(refreshToken, session.refresh_token_hash);
      if (valid) {
        validSession = session;
        break;
      }
    }
    
    if (!validSession) {
      res.status(401).json({ error: 'Invalid or expired refresh token' });
      return;
    }
    
    if (!validSession.is_active) {
      res.status(401).json({ error: 'Account is disabled' });
      return;
    }
    
    // Generate new access token
    const newJti = uuidv4();
    const accessSecret = process.env.JWT_ACCESS_SECRET!;
    
    const accessToken = jwt.sign(
      {
        sub: validSession.user_id,
        jti: newJti,
        username: validSession.username,
        role: validSession.role
      },
      accessSecret,
      { expiresIn: '15m' }
    );
    
    res.json({
      accessToken,
      user: {
        id: validSession.user_id,
        username: validSession.username,
        role: validSession.role
      }
    });
  } catch (error) {
    if (error instanceof jwt.TokenExpiredError) {
      res.status(401).json({ error: 'Refresh token expired' });
      return;
    }
    logger.error('Refresh error:', error);
    res.status(500).json({ error: 'Token refresh failed' });
  }
});

// Logout
authRouter.post('/logout', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const user = req.user!;
    
    // Delete all sessions for user
    await query('DELETE FROM sessions WHERE user_id = $1', [user.sub]);
    
    // Log logout
    await query(
      `INSERT INTO audit_logs (user_id, action, details, ip_address, user_agent)
       VALUES ($1, 'logout', '{}', $2, $3)`,
      [user.sub, req.ip, req.headers['user-agent']]
    );
    
    logger.info(`User logged out: ${user.username}`);
    
    res.json({ message: 'Logged out successfully' });
  } catch (error) {
    logger.error('Logout error:', error);
    res.status(500).json({ error: 'Logout failed' });
  }
});

// Get current user
authRouter.get('/me', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const result = await query(
      'SELECT id, username, role, created_at FROM users WHERE id = $1',
      [req.user!.sub]
    );
    
    if (result.rows.length === 0) {
      res.status(404).json({ error: 'User not found' });
      return;
    }
    
    res.json({ user: result.rows[0] });
  } catch (error) {
    logger.error('Get user error:', error);
    res.status(500).json({ error: 'Failed to get user' });
  }
});
