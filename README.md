# Hination - AI Grading System

Hệ thống chấm điểm tự động sử dụng AI, được thiết kế với kiến trúc microservices.

## Architecture

```
Internet → Nginx (8080) → Frontend (3100)
                         → Backend API (4000)
                         → RabbitMQ Management (15673, protected)

Backend → PostgreSQL (5444)
       → Redis (6380)
       → RabbitMQ (5673)

RabbitMQ → Worker (consumes jobs) → AI Server (external)
```

## Quick Start

### 1. Setup Environment

```bash
# Copy environment file
cp .env.example .env

# Generate secure tokens
openssl rand -hex 64  # For STATIC_API_TOKEN
openssl rand -hex 64  # For JWT_ACCESS_SECRET
openssl rand -hex 64  # For JWT_REFRESH_SECRET

# Generate bcrypt hash for admin password
node -e "const bcrypt = require('bcrypt'); bcrypt.hash('your_password', 12).then(h => console.log(h))"
```

### 2. Start Services

```bash
# Development
docker compose up -d

# Production
docker compose -f docker-compose.prod.yml up -d
```

### 3. Access

- **Frontend**: http://localhost:8080
- **API**: http://localhost:8080/api
- **RabbitMQ Management**: http://localhost:8080/rabbitmq/ (auth required)

### 4. Default Credentials

- **Username**: admin
- **Password**: (set in ADMIN_PASSWORD in .env)

## API Documentation

### Authentication

#### Login
```bash
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "your_password"
}
```

Response:
```json
{
  "accessToken": "eyJhbG...",
  "refreshToken": "eyJhbG...",
  "user": {
    "id": "uuid",
    "username": "admin",
    "role": "admin"
  }
}
```

### Scoring API (Static Token)

Submit a grading job:
```bash
curl -X POST http://localhost:8080/api/scoring/submit \
  -H "Authorization: Bearer $STATIC_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "studentId": "STU001",
    "answers": ["answer1", "answer2"],
    "metadata": {"examId": "EX001"}
  }'
```

Get job status:
```bash
curl http://localhost:8080/api/scoring/jobs/{jobId} \
  -H "Authorization: Bearer $STATIC_API_TOKEN"
```

## Project Structure

```
hination/
├── docs/
│   └── ARCHITECTURE.md       # Detailed architecture
├── docker/
│   ├── nginx/
│   │   ├── nginx.conf
│   │   └── conf.d/
│   ├── frontend/             # Next.js frontend
│   │   ├── src/
│   │   │   ├── app/
│   │   │   │   ├── login/
│   │   │   │   └── dashboard/
│   │   │   └── lib/
│   │   └── Dockerfile
│   ├── backend/              # Express API
│   │   ├── src/
│   │   │   ├── config/
│   │   │   ├── routes/
│   │   │   ├── middleware/
│   │   │   └── types/
│   │   └── Dockerfile
│   └── worker/               # RabbitMQ consumer
│       ├── src/
│       │   ├── config/
│       │   └── services/
│       └── Dockerfile
├── scripts/
│   └── init-db.sql
├── docker-compose.yml        # Development
├── docker-compose.prod.yml   # Production
├── .env.example
└── README.md
```

## Commands

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f backend
docker compose logs -f worker
docker compose logs -f nginx

# Restart a service
docker compose restart backend

# Seed admin user
docker compose exec backend npm run seed:admin

# Database migration (if using migrations)
docker compose exec backend npm run db:migrate

# Rebuild after code changes
docker compose up -d --build

# Stop all services
docker compose down

# Clean up volumes (⚠️ deletes data)
docker compose down -v
```

## Port Allocation

| Port | Service | Description |
|------|---------|-------------|
| 8080 | Nginx | HTTP reverse proxy |
| 8443 | Nginx | HTTPS reverse proxy |
| 3100 | Frontend | Next.js |
| 4000 | Backend | Express API |
| 5444 | PostgreSQL | Database |
| 6380 | Redis | Cache |
| 5673 | RabbitMQ | AMQP |
| 15673 | RabbitMQ | Management UI |

## Deployment to Production

### 1. Configure Environment

```bash
# Production .env
NODE_ENV=production
POSTGRES_PASSWORD=<secure_password>
REDIS_PASSWORD=<secure_password>
STATIC_API_TOKEN=<generated_token>
JWT_ACCESS_SECRET=<generated_secret>
JWT_REFRESH_SECRET=<generated_secret>
```

### 2. Cloudflare Tunnel

Create a tunnel pointing to your server:
```bash
cloudflared tunnel create hination
cloudflared tunnel route dns hination ecombay.online
cloudflared tunnel run --url http://localhost:8080 hination
```

### 3. SSL Certificates

For production, configure SSL in nginx:
```nginx
server {
    listen 443 ssl http2;
    server_name ecombay.online;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    # ...
}
```

## License

MIT
