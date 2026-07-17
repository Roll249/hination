export interface User {
  id: string;
  username: string;
  password_hash: string;
  role: 'admin' | 'user';
  is_active: boolean;
  created_at: Date;
  updated_at: Date;
}

export interface Session {
  id: string;
  user_id: string;
  refresh_token_hash: string;
  user_agent: string | null;
  ip_address: string | null;
  expires_at: Date;
  created_at: Date;
}

export interface ScoringJob {
  id: string;
  student_id: string;
  job_type: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  input_data: {
    answers: unknown[];
    metadata: Record<string, unknown>;
  };
  result_data: Record<string, unknown> | null;
  ai_response: Record<string, unknown> | null;
  error_message: string | null;
  retry_count: number;
  max_retries: number;
  created_at: Date;
  started_at: Date | null;
  completed_at: Date | null;
}

export interface APIKey {
  id: string;
  name: string;
  key_hash: string;
  scopes: string[];
  is_active: boolean;
  expires_at: Date | null;
  last_used_at: Date | null;
  created_by: string;
  created_at: Date;
}

export interface AuditLog {
  id: string;
  user_id: string;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  details: Record<string, unknown>;
  ip_address: string | null;
  user_agent: string | null;
  created_at: Date;
}

export interface AIResponse {
  score: number;
  feedback: string;
  breakdown: Record<string, number>;
  metadata: Record<string, unknown>;
}
