import { Router, Response } from 'express';
import { query } from '../config/database.js';
import { logger } from '../config/logger.js';
import { authMiddleware, requireRole, AuthenticatedRequest } from '../middleware/auth.js';

export const adminRouter = Router();

// All admin routes require authentication and admin role
adminRouter.use(authMiddleware);
adminRouter.use(requireRole('admin'));

// List all users
adminRouter.get('/users', async (req: AuthenticatedRequest, res: Response) => {
  try {
    const page = parseInt(req.query.page as string) || 1;
    const limit = Math.min(parseInt(req.query.limit as string) || 20, 100);
    const offset = (page - 1) * limit;
    
    const result = await query(
      `SELECT id, username, role, is_active, created_at, updated_at 
       FROM users 
       ORDER BY created_at DESC 
       LIMIT $1 OFFSET $2`,
      [limit, offset]
    );
    
    const countResult = await query('SELECT COUNT(*) FROM users');
    const total = parseInt(countResult.rows[0].count);
    
    res.json({
      users: result.rows,
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit)
      }
    });
  } catch (error) {
    logger.error('List users error:', error);
    res.status(500).json({ error: 'Failed to list users' });
  }
});

// Get user by ID
adminRouter.get('/users/:id', async (req: AuthenticatedRequest, res: Response) => {
  try {
    const result = await query(
      'SELECT id, username, role, is_active, created_at, updated_at FROM users WHERE id = $1',
      [req.params.id]
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

// Update user
adminRouter.put('/users/:id', async (req: AuthenticatedRequest, res: Response) => {
  try {
    const { username, role, is_active } = req.body;
    const userId = req.params.id;
    
    const updates: string[] = [];
    const values: unknown[] = [];
    let paramIndex = 1;
    
    if (username !== undefined) {
      updates.push(`username = $${paramIndex++}`);
      values.push(username);
    }
    if (role !== undefined) {
      updates.push(`role = $${paramIndex++}`);
      values.push(role);
    }
    if (is_active !== undefined) {
      updates.push(`is_active = $${paramIndex++}`);
      values.push(is_active);
    }
    
    if (updates.length === 0) {
      res.status(400).json({ error: 'No fields to update' });
      return;
    }
    
    values.push(userId);
    
    const result = await query(
      `UPDATE users SET ${updates.join(', ')} WHERE id = $${paramIndex} RETURNING id, username, role, is_active, created_at, updated_at`,
      values
    );
    
    if (result.rows.length === 0) {
      res.status(404).json({ error: 'User not found' });
      return;
    }
    
    // Log update
    await query(
      `INSERT INTO audit_logs (user_id, action, resource_type, resource_id, details, ip_address)
       VALUES ($1, 'update_user', 'user', $2, $3, $4)`,
      [req.user!.sub, userId, JSON.stringify(req.body), req.ip]
    );
    
    res.json({ user: result.rows[0] });
  } catch (error: unknown) {
    if ((error as { code?: string }).code === '23505') {
      res.status(409).json({ error: 'Username already exists' });
      return;
    }
    logger.error('Update user error:', error);
    res.status(500).json({ error: 'Failed to update user' });
  }
});

// Delete user
adminRouter.delete('/users/:id', async (req: AuthenticatedRequest, res: Response) => {
  try {
    const userId = req.params.id;
    
    // Prevent self-deletion
    if (userId === req.user!.sub) {
      res.status(400).json({ error: 'Cannot delete your own account' });
      return;
    }
    
    const result = await query(
      'DELETE FROM users WHERE id = $1 RETURNING id',
      [userId]
    );
    
    if (result.rows.length === 0) {
      res.status(404).json({ error: 'User not found' });
      return;
    }
    
    // Log deletion
    await query(
      `INSERT INTO audit_logs (user_id, action, resource_type, resource_id, ip_address)
       VALUES ($1, 'delete_user', 'user', $2, $3)`,
      [req.user!.sub, userId, req.ip]
    );
    
    res.json({ message: 'User deleted successfully' });
  } catch (error) {
    logger.error('Delete user error:', error);
    res.status(500).json({ error: 'Failed to delete user' });
  }
});

// Get audit logs
adminRouter.get('/audit-logs', async (req: AuthenticatedRequest, res: Response) => {
  try {
    const page = parseInt(req.query.page as string) || 1;
    const limit = Math.min(parseInt(req.query.limit as string) || 50, 100);
    const offset = (page - 1) * limit;
    const userId = req.query.userId as string | undefined;
    
    let whereClause = '';
    const values: unknown[] = [];
    let paramIndex = 1;
    
    if (userId) {
      whereClause = `WHERE user_id = $${paramIndex++}`;
      values.push(userId);
    }
    
    values.push(limit, offset);
    
    const result = await query(
      `SELECT a.*, u.username 
       FROM audit_logs a 
       LEFT JOIN users u ON a.user_id = u.id 
       ${whereClause}
       ORDER BY a.created_at DESC 
       LIMIT $${paramIndex++} OFFSET $${paramIndex}`,
      values
    );
    
    let countQuery = 'SELECT COUNT(*) FROM audit_logs';
    if (userId) {
      countQuery += ` WHERE user_id = $1`;
    }
    
    const countResult = await query(
      countQuery,
      userId ? [userId] : []
    );
    const total = parseInt(countResult.rows[0].count);
    
    res.json({
      logs: result.rows,
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit)
      }
    });
  } catch (error) {
    logger.error('Get audit logs error:', error);
    res.status(500).json({ error: 'Failed to get audit logs' });
  }
});

// System stats
adminRouter.get('/stats', async (req: AuthenticatedRequest, res: Response) => {
  try {
    const [userCount, sessionCount, jobCount, recentJobs] = await Promise.all([
      query('SELECT COUNT(*) FROM users'),
      query('SELECT COUNT(*) FROM sessions WHERE expires_at > NOW()'),
      query('SELECT COUNT(*) FROM scoring_jobs'),
      query(`
        SELECT status, COUNT(*) 
        FROM scoring_jobs 
        WHERE created_at > NOW() - INTERVAL '24 hours'
        GROUP BY status
      `)
    ]);
    
    const statusCounts: Record<string, number> = {};
    for (const row of recentJobs.rows) {
      statusCounts[row.status] = parseInt(row.count);
    }
    
    res.json({
      stats: {
        users: parseInt(userCount.rows[0].count),
        activeSessions: parseInt(sessionCount.rows[0].count),
        totalJobs: parseInt(jobCount.rows[0].count),
        jobsLast24h: statusCounts
      }
    });
  } catch (error) {
    logger.error('Get stats error:', error);
    res.status(500).json({ error: 'Failed to get stats' });
  }
});
