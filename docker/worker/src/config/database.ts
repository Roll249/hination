import pg, { QueryResult, QueryResultRow } from 'pg';

const { Pool } = pg;

export const pool = new Pool({
  host: process.env.POSTGRES_HOST || 'localhost',
  port: parseInt(process.env.POSTGRES_PORT || '5432'),
  user: process.env.POSTGRES_USER || 'hination',
  password: process.env.POSTGRES_PASSWORD,
  database: process.env.POSTGRES_DB || 'hination',
  max: 10,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 5000,
});

export async function query<T extends QueryResultRow = QueryResultRow>(
  text: string, 
  params?: unknown[]
): Promise<QueryResult<T>> {
  return pool.query<T>(text, params);
}

export async function updateJobStatus(
  jobId: string,
  status: 'processing' | 'completed' | 'failed',
  result?: Record<string, unknown>,
  aiResponse?: Record<string, unknown>,
  errorMessage?: string
): Promise<void> {
  const updates: string[] = ['status = $2'];
  const values: unknown[] = [jobId, status];
  let paramIndex = 3;

  if (status === 'processing') {
    updates.push('started_at = NOW()');
  }
  
  if (result) {
    updates.push(`result_data = $${paramIndex++}`);
    values.push(JSON.stringify(result));
  }
  
  if (aiResponse) {
    updates.push(`ai_response = $${paramIndex++}`);
    values.push(JSON.stringify(aiResponse));
  }
  
  if (errorMessage) {
    updates.push(`error_message = $${paramIndex++}`);
    values.push(errorMessage);
  }
  
  if (status === 'completed' || status === 'failed') {
    updates.push('completed_at = NOW()');
  }

  await pool.query(
    `UPDATE scoring_jobs SET ${updates.join(', ')} WHERE id = $1`,
    values
  );
}
