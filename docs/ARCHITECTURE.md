# Hination - AI Grading System Architecture

## 1. System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              INTERNET                                       │
│                    ecombay.online (Cloudflare Tunnel)                        │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   │ :8080 (HTTP) / :8443 (HTTPS)
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              NGINX (Public)                                  │
│                    Reverse Proxy / Load Balancer                             │
│                                                                              │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│   │  /api/*      │  │  /admin/*    │  │  /rabbitmq/* │  │  /*          │   │
│   │  → Backend   │  │  → Backend   │  │  → RabbitMQ  │  │  → Frontend  │   │
│   └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
            ┌──────────────────────┼──────────────────────┐
            │                      │                      │
            ▼                      ▼                      ▼
    ┌───────────────┐      ┌───────────────┐      ┌───────────────┐
    │   FRONTEND    │      │    BACKEND    │      │   RABBITMQ    │
    │   (Next.js)   │      │   (Express)   │      │   Management  │
    │   :3100       │      │   :4000       │      │   :15673       │
    └───────────────┘      └───────┬───────┘      └───────────────┘
                                   │
         ┌─────────────────────────┼─────────────────────────┐
         │                         │                         │
         ▼                         ▼                         ▼
 ┌───────────────┐         ┌───────────────┐         ┌───────────────┐
 │  PostgreSQL   │         │    Redis      │         │   RABBITMQ    │
 │    :5444      │         │    :6380      │         │   :5673       │
 └───────────────┘         └───────────────┘         └───────┬───────┘
                                                              │
                                                              ▼
                                                    ┌───────────────┐
                                                    │    WORKER     │
                                                    │  (Node.js)    │
                                                    │   Consumer    │
                                                    └───────┬───────┘
                                                            │
                                                            ▼
                                                    ┌───────────────┐
                                                    │  AI SERVER    │
                                                    │  (External)   │
                                                    │  :PORT        │
                                                    └───────────────┘
```

## 2. Technology Stack

| Component     | Technology           | Port  | Image / Version          |
|---------------|----------------------|-------|--------------------------|
| Reverse Proxy | Nginx                | 8080  | nginx:alpine             |
| Frontend      | Next.js + TypeScript | 3100  | node:20-alpine            |
| Backend API   | Express + TypeScript | 4000  | node:20-alpine            |
| Database      | PostgreSQL           | 5444  | postgres:16-alpine        |
| Cache / Store | Redis                | 6380  | redis:7-alpine            |
| Message Queue | RabbitMQ             | 5673  | rabbitmq:3.13-management  |
| Worker        | Node.js              | -     | node:20-alpine (no port)  |

## 3. Port Allocation

### 3.1 Internal Ports (Docker Internal Network)

| Service       | Internal Port | Purpose                          |
|---------------|---------------|----------------------------------|
| frontend      | 3100          | Next.js dev server               |
| backend       | 4000          | Express API                      |
| postgres      | 5432          | PostgreSQL default               |
| redis         | 6379          | Redis default                    |
| rabbitmq      | 5672          | RabbitMQ AMQP                    |
| rabbitmq-mgmt | 15672         | RabbitMQ Management UI           |

### 3.2 Exposed Ports (Host → Container)

| Host Port | Container Port | Service              | Access              |
|-----------|----------------|----------------------|---------------------|
| 5444      | 5432           | PostgreSQL           | Backend only        |
| 6380      | 6379           | Redis                | Backend only        |
| 5673      | 5672           | RabbitMQ AMQP        | Worker + Backend    |
| 15673     | 15672          | RabbitMQ Management  | Nginx (restricted)  |
| 4000      | 4000           | Backend API          | Nginx only          |
| 3100      | 3100           | Frontend             | Nginx only          |
| 8080      | 80             | Nginx HTTP           | PUBLIC (Cloudflare) |
| 8443      | 443            | Nginx HTTPS          | PUBLIC (Cloudflare) |

### 3.3 Reserved Ports (DO NOT USE)

```
22    - SSH
53    - DNS
80    - Existing Nginx (host)
443   - Existing Nginx (host)
3000  - Docker
3001  - Docker
5433  - Docker
5455  - Docker
8081  - Docker
8082  - Docker
20241 - Cloudflared Tunnel
```

### 3.4 Cloudflare Tunnel

Cloudflare Tunnel đã chạy sẵn trên server (UDP random ports). Sẽ tạo tunnel mới trỏ `ecombay.online` → `localhost:8080`.

## 4. Authentication System

### 4.1 User Authentication (Admin Login)

- **Single Admin Account**: Tạo duy nhất 1 tài khoản admin khi bootstrap
- **Login Flow**:
  ```
  POST /api/auth/login
  Body: { username, password }
  Response: { accessToken, refreshToken, user: { id, username, role } }
  ```
- **JWT Tokens**:
  - Access Token: 15 phút, lưu trong memory
  - Refresh Token: 7 ngày, lưu trong httpOnly cookie
- **Sessions**: Lưu refresh token hash trong PostgreSQL

### 4.2 Static API Token (Scoring System)

- **Purpose**: Cho phép hệ thống máy chấm điểm gọi API mà không cần login
- **Storage**: Lưu trong `.env` (không lưu trong DB)
- **Usage**:
  ```
  POST /api/scoring/submit
  Headers: { Authorization: Bearer <STATIC_API_TOKEN> }
  Body: { studentId, answers, ... }
  ```
- **Security**: Token dài, random, không có expiry (rotate bằng tay khi cần)

### 4.3 Environment Variables

```env
# Static API Token cho hệ thống chấm điểm
STATIC_API_TOKEN=your_very_long_random_token_here_min_64_chars

# JWT Secrets
JWT_ACCESS_SECRET=your_jwt_access_secret
JWT_REFRESH_SECRET=your_jwt_refresh_secret

# Database
POSTGRES_USER=admin
POSTGRES_PASSWORD=your_postgres_password
POSTGRES_DB=hination

# Redis
REDIS_PASSWORD=your_redis_password

# RabbitMQ
RABBITMQ_DEFAULT_USER=guest
RABBITMQ_DEFAULT_PASS=guest
```

## 5. API Endpoints Design

### 5.1 Public Endpoints (No Auth)

```
POST   /api/auth/login           - Admin login
POST   /api/auth/refresh         - Refresh access token
```

### 5.2 Protected Endpoints (JWT Required)

```
# Admin only
GET    /api/admin/users          - List users
POST   /api/admin/users          - Create user (future)
PUT    /api/admin/users/:id       - Update user
DELETE /api/admin/users/:id       - Delete user

# Scoring endpoints (JWT - for admin dashboard)
GET    /api/scoring/jobs          - List scoring jobs
GET    /api/scoring/jobs/:id       - Get job status
```

### 5.3 Scoring Endpoints (Static Token)

```
POST   /api/scoring/submit         - Submit answer for grading
GET    /api/scoring/jobs/:id/result - Get grading result
```

### 5.4 Webhook (Future)

```
POST   /api/webhook/ai-callback    - AI server callback
```

## 6. Request Flow

### 6.1 Admin Login Flow

```
1. User → Frontend (3100) → POST /api/auth/login
2. Frontend → Nginx (8080) → Backend (4000)
3. Backend → PostgreSQL (verify credentials)
4. Backend → Redis (check refresh token)
5. Backend ← PostgreSQL (user data)
6. Backend → JWT (generate tokens)
7. Backend → Redis (store refresh token hash)
8. Frontend ← Backend (accessToken + user info)
9. Frontend → Set httpOnly cookie (refreshToken)
```

### 6.2 Scoring Flow (Machine)

```
1. Grading Machine → POST /api/scoring/submit
   Headers: { Authorization: Bearer <STATIC_API_TOKEN> }
2. Nginx (8080) → Backend (4000)
3. Backend → Verify STATIC_API_TOKEN (env check)
4. Backend → Validate request body
5. Backend → PostgreSQL (create job record)
6. Backend → RabbitMQ (publish job message)
7. Backend ← RabbitMQ (job queued)
8. Frontend ← Backend (202 Accepted, { jobId })
9. Worker ← RabbitMQ (consume message)
10. Worker → AI Server (call grading API)
11. Worker ← AI Server (grading result)
12. Worker → PostgreSQL (update job result)
13. Grading Machine → GET /api/scoring/jobs/:id/result
14. Backend ← PostgreSQL (job result)
15. Grading Machine ← Backend (result)
```

### 6.3 Worker Queue Processing

```
RabbitMQ Queue: scoring_jobs

Message Format:
{
  "jobId": "uuid",
  "studentId": "string",
  "answers": [...],
  "metadata": {...},
  "timestamp": "ISO8601"
}

Processing Steps:
1. Consume message from queue
2. Update job status to "processing" in DB
3. Call AI Server with answers
4. Get AI response
5. Update job status to "completed" with results
6. If error: update status to "failed" with error message
7. Acknowledge message
```

## 7. Nginx Configuration

### 7.1 Main Config (`nginx/nginx.conf`)

```nginx
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    # Gzip
    gzip on;
    gzip_types text/plain application/json application/javascript text/css;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=auth_limit:10m rate=5r/m;

    # Upstreams
    upstream backend {
        server backend:4000;
        keepalive 32;
    }

    upstream frontend {
        server frontend:3100;
        keepalive 32;
    }

    upstream rabbitmq_mgmt {
        server rabbitmq:15672;
        keepalive 16;
    }

    include /etc/nginx/conf.d/*.conf;
}
```

### 7.2 Sites Config (`nginx/conf.d/sites.conf`)

```nginx
server {
    listen 80;
    server_name _;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Rate limiting
    limit_req zone=api_limit burst=20 nodelay;

    # Backend API
    location /api/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection "";

        # Timeout
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # RabbitMQ Management (restricted)
    location /rabbitmq/ {
        proxy_pass http://rabbitmq_mgmt/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;

        # Basic auth for RabbitMQ management
        auth_basic "RabbitMQ Management";
        auth_basic_user_file /etc/nginx/.htpasswd;
    }

    # Frontend (SPA)
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection "";
    }
}
```

## 8. Database Schema

### 8.1 Users Table (Admin only)

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'admin',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Seed admin user (run on first startup)
INSERT INTO users (username, password_hash, role)
VALUES ('admin', <bcrypt_hash>, 'admin');
```

### 8.2 Sessions Table (Refresh Tokens)

```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    refresh_token_hash VARCHAR(255) NOT NULL,
    user_agent TEXT,
    ip_address INET,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 8.3 Scoring Jobs Table

```sql
CREATE TABLE scoring_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'queued',
    -- Status: queued, processing, completed, failed
    input_data JSONB NOT NULL,
    result_data JSONB,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_scoring_jobs_status ON scoring_jobs(status);
CREATE INDEX idx_scoring_jobs_student_id ON scoring_jobs(student_id);
CREATE INDEX idx_scoring_jobs_created_at ON scoring_jobs(created_at);
```

## 9. Folder Structure

```
hination/
├── docs/
│   ├── ARCHITECTURE.md      # This file
│   └── DEPLOYMENT.md        # Deployment guide
├── docker/
│   ├── nginx/
│   │   ├── Dockerfile
│   │   ├── nginx.conf
│   │   └── conf.d/
│   │       └── sites.conf
│   ├── frontend/
│   │   ├── Dockerfile
│   │   └── (Next.js source)
│   ├── backend/
│   │   ├── Dockerfile
│   │   ├── tsconfig.json
│   │   ├── package.json
│   │   └── src/
│   │       ├── index.ts
│   │       ├── config/
│   │       │   ├── database.ts
│   │       │   ├── redis.ts
│   │       │   └── rabbitmq.ts
│   │       ├── routes/
│   │       │   ├── auth.ts
│   │       │   ├── admin.ts
│   │       │   └── scoring.ts
│   │       ├── middleware/
│   │       │   ├── auth.ts
│   │       │   └── staticToken.ts
│   │       ├── services/
│   │       │   ├── userService.ts
│   │       │   └── scoringService.ts
│   │       └── types/
│   │           └── index.ts
│   └── worker/
│       ├── Dockerfile
│       ├── tsconfig.json
│       ├── package.json
│       └── src/
│           ├── index.ts
│           └── scoringConsumer.ts
├── scripts/
│   └── seed-admin.ts        # Seed admin user
├── .env.example
├── docker-compose.yml
├── docker-compose.prod.yml
├── .gitignore
└── README.md
```

## 10. Security Considerations

### 10.1 Static API Token Security

- Token phải dài tối thiểu 64 ký tự
- Lưu trong `.env`, KHÔNG commit vào git
- Không log token ra console
- Rate limit cho endpoint dùng static token
- Có thể rotate token bằng cách restart service với env mới

### 10.2 Admin Account Security

- Password dài tối thiểu 12 ký tự
- Bcrypt hash với salt rounds = 12
- Refresh token rotation on use
- Single session policy (optional)

### 10.3 Network Security

- Tất cả services chỉ expose qua Nginx
- Không expose DB/Redis/RabbitMQ port ra ngoài
- Cloudflare Tunnel mã hóa traffic
- Có thể bật HTTPS trong nginx

## 11. Deployment Phases

### Phase 1: Local Development
- [x] Thiết kế kiến trúc (docs/ARCHITECTURE.md)
- [ ] Setup Docker Compose
- [ ] Setup PostgreSQL + seed admin
- [ ] Setup Redis
- [ ] Setup RabbitMQ
- [ ] Implement Backend API
- [ ] Implement Frontend (Login)
- [ ] Implement Worker
- [ ] Test local

### Phase 2: Production Local
- [ ] Nginx config production
- [ ] Environment variables setup
- [ ] SSL certificates
- [ ] Backup strategy
- [ ] Monitoring/Logging

### Phase 3: Cloudflare Tunnel
- [ ] Create tunnel for ecombay.online
- [ ] Point to nginx:8080
- [ ] DNS configuration
- [ ] SSL full

### Phase 4: AI Server Integration
- [ ] Define AI API contract
- [ ] Implement AI client in worker
- [ ] Error handling & retry
- [ ] Rate limiting

## 12. Environment Variables Reference

```env
# =======================
# APPLICATION
# =======================
NODE_ENV=development

# =======================
# DATABASE
# =======================
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=hination
POSTGRES_PASSWORD=<secure_password>
POSTGRES_DB=hination

# =======================
# REDIS
# =======================
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=<secure_password>

# =======================
# RABBITMQ
# =======================
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASS=guest
RABBITMQ_VHOST=/

# =======================
# JWT
# =======================
JWT_ACCESS_SECRET=<64_char_random>
JWT_ACCESS_EXPIRY=15m
JWT_REFRESH_SECRET=<64_char_random>
JWT_REFRESH_EXPIRY=7d

# =======================
# STATIC API TOKEN (Scoring)
# =======================
# IMPORTANT: Generate with: openssl rand -hex 64
STATIC_API_TOKEN=<64_char_random_token>

# =======================
# AI SERVER
# =======================
AI_API_URL=https://your-ai-server.com/api/grade
AI_API_KEY=<ai_api_key>

# =======================
# FRONTEND
# =======================
NEXT_PUBLIC_API_URL=http://localhost:8080/api
```

## 13. Useful Commands

```bash
# Generate secure tokens
openssl rand -hex 64

# Generate bcrypt hash (Node.js)
node -e "const bcrypt = require('bcrypt'); bcrypt.hash('your_password', 12).then(h => console.log(h))"

# Check logs
docker compose logs -f backend
docker compose logs -f worker
docker compose logs -f nginx

# Database migration
docker compose exec backend npm run db:migrate

# Seed admin
docker compose exec backend npm run seed:admin

# RabbitMQ
docker compose exec rabbitmq rabbitmqctl list_queues
docker compose exec rabbitmq rabbitmqctl list_channels
```
