# Deployment Guide

Complete guide for deploying the Evo-AI platform to production environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Database Setup](#database-setup)
- [Backend Deployment](#backend-deployment)
- [Frontend Deployment](#frontend-deployment)
- [Infrastructure Services](#infrastructure-services)
- [Monitoring & Observability](#monitoring--observability)
- [Security](#security)
- [Scaling](#scaling)

## Prerequisites

### System Requirements

- **OS**: Linux (Ubuntu 20.04+ recommended) or Docker-compatible system
- **RAM**: Minimum 8GB, Recommended 16GB+
- **CPU**: Minimum 4 cores, Recommended 8+ cores
- **Storage**: Minimum 50GB SSD
- **Network**: Stable internet connection for external API calls

### Software Requirements

- Docker 24.0+
- Docker Compose 2.20+
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+

## Environment Setup

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/evo-ai.git
cd evo-ai
```

### 2. Configure Environment Variables

#### Backend (`backend/.env`)

```bash
# Database
DATABASE_URL=postgresql://evo_user:your_password@localhost:5432/evo_ai
POSTGRES_USER=evo_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=evo_ai

# Redis
REDIS_URL=redis://localhost:6379/0

# MinIO (S3-compatible storage)
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=evo-ai-storage
MINIO_SECURE=false

# API Keys (set your actual keys)
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key

# Ray
RAY_ADDRESS=auto

# Observability
JAEGER_AGENT_HOST=localhost
JAEGER_AGENT_PORT=6831
PROMETHEUS_PORT=9090

# Application
LOG_LEVEL=INFO
ENVIRONMENT=production
API_HOST=0.0.0.0
API_PORT=8000
```

#### Frontend (`frontend/.env.local`)

```bash
# Backend API URL
NEXT_PUBLIC_API_URL=https://api.yourdomain.com

# Environment
NODE_ENV=production
```

## Database Setup

### 1. Initialize PostgreSQL

```bash
# Using Docker
docker run -d \
  --name evo-ai-postgres \
  -e POSTGRES_USER=evo_user \
  -e POSTGRES_PASSWORD=your_password \
  -e POSTGRES_DB=evo_ai \
  -p 5432:5432 \
  -v postgres-data:/var/lib/postgresql/data \
  postgres:15-alpine
```

### 2. Run Migrations

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m evo_ai.database.init_db
```

### 3. Verify Database

```bash
psql -h localhost -U evo_user -d evo_ai -c "\dt"
```

## Backend Deployment

### Option 1: Docker Deployment (Recommended)

```bash
# Build backend image
docker build -t evo-ai-backend:latest ./backend

# Run backend container
docker run -d \
  --name evo-ai-backend \
  -p 8000:8000 \
  --env-file backend/.env \
  --network evo-ai-network \
  evo-ai-backend:latest
```

### Option 2: Systemd Service

```bash
# Create systemd service file
sudo nano /etc/systemd/system/evo-ai-backend.service
```

```ini
[Unit]
Description=Evo-AI Backend Service
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=evo-ai
WorkingDirectory=/opt/evo-ai/backend
Environment="PATH=/opt/evo-ai/backend/venv/bin"
EnvironmentFile=/opt/evo-ai/backend/.env
ExecStart=/opt/evo-ai/backend/venv/bin/uvicorn evo_ai.api.app:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable evo-ai-backend
sudo systemctl start evo-ai-backend
sudo systemctl status evo-ai-backend
```

### Option 3: Gunicorn with Uvicorn Workers

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn evo_ai.api.app:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

## Frontend Deployment

### Option 1: Docker Deployment

```bash
# Build frontend image
docker build -t evo-ai-frontend:latest ./frontend

# Run frontend container
docker run -d \
  --name evo-ai-frontend \
  -p 3000:3000 \
  --env-file frontend/.env.local \
  evo-ai-frontend:latest
```

### Option 2: Vercel Deployment

```bash
cd frontend
npm install -g vercel
vercel --prod
```

Follow the prompts to configure deployment settings.

### Option 3: Static Export

```bash
cd frontend
npm run build
npm run export

# Serve with nginx
sudo cp -r out/* /var/www/html/evo-ai/
```

## Infrastructure Services

### Docker Compose (All Services)

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres-data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    restart: unless-stopped

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ACCESS_KEY}
      MINIO_ROOT_PASSWORD: ${MINIO_SECRET_KEY}
    volumes:
      - minio-data:/data
    ports:
      - "9000:9000"
      - "9001:9001"
    restart: unless-stopped

  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"
      - "6831:6831/udp"
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./infrastructure/observability/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    ports:
      - "9090:9090"
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
    volumes:
      - grafana-data:/var/lib/grafana
      - ./infrastructure/observability/grafana:/etc/grafana/provisioning
    ports:
      - "3001:3000"
    restart: unless-stopped

  backend:
    build: ./backend
    depends_on:
      - postgres
      - redis
      - minio
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      REDIS_URL: redis://redis:6379/0
    ports:
      - "8000:8000"
    restart: unless-stopped

  frontend:
    build: ./frontend
    depends_on:
      - backend
    environment:
      NEXT_PUBLIC_API_URL: http://backend:8000
    ports:
      - "3000:3000"
    restart: unless-stopped

volumes:
  postgres-data:
  redis-data:
  minio-data:
  prometheus-data:
  grafana-data:
```

```bash
# Deploy all services
docker-compose -f docker-compose.prod.yml up -d
```

## Monitoring & Observability

### Grafana Dashboards

1. Access Grafana: `http://your-server:3001`
2. Login with admin credentials
3. Import dashboards:
   - Evo-AI System Metrics
   - Agent Performance
   - Campaign Analytics

### Prometheus Metrics

Available at: `http://your-server:9090`

Key metrics:
- `agent_execution_total` - Total agent executions
- `variant_generation_rate` - Variants generated per second
- `selection_success_rate` - Successful selections
- `api_request_duration_seconds` - API latency

### Jaeger Tracing

Access UI: `http://your-server:16686`

Search for traces by:
- Campaign ID
- Round number
- Agent type
- Trace ID

## Security

### 1. API Key Management

```bash
# Use environment variables, never hardcode
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...

# Or use secrets management
docker secret create openai_key openai_key.txt
```

### 2. Database Security

```sql
-- Create read-only user for reporting
CREATE USER evo_readonly WITH PASSWORD 'readonly_password';
GRANT SELECT ON ALL TABLES IN SCHEMA public TO evo_readonly;
```

### 3. HTTPS/TLS

```nginx
# nginx configuration
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 4. CORS Configuration

In `backend/src/evo_ai/api/app.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Scaling

### Horizontal Scaling (Multiple Instances)

```bash
# Scale backend with load balancer
docker-compose -f docker-compose.prod.yml up -d --scale backend=4

# Use nginx for load balancing
upstream backend {
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
    server backend4:8000;
}
```

### Ray Cluster for Distributed Tasks

```python
# Initialize Ray cluster
ray start --head --port=6379 --dashboard-host=0.0.0.0

# Connect workers
ray start --address='head-node-ip:6379'
```

### Database Connection Pooling

```python
# In database configuration
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True
)
```

## Health Checks

### Backend Health Endpoint

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "ray": "connected"
}
```

### Frontend Health Check

```bash
curl http://localhost:3000/api/health
```

## Backup & Recovery

### Database Backup

```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -h localhost -U evo_user evo_ai | gzip > /backups/evo_ai_$DATE.sql.gz

# Keep only last 30 days
find /backups -name "evo_ai_*.sql.gz" -mtime +30 -delete
```

### Database Restore

```bash
gunzip < /backups/evo_ai_20240101_120000.sql.gz | psql -h localhost -U evo_user evo_ai
```

## Troubleshooting

### Backend Won't Start

```bash
# Check logs
docker logs evo-ai-backend

# Verify database connection
python -c "from evo_ai.database import get_session; print('OK')"

# Check port conflicts
sudo lsof -i :8000
```

### Frontend Build Errors

```bash
# Clear cache and rebuild
rm -rf .next node_modules
npm install
npm run build
```

### Ray Connection Issues

```bash
# Check Ray status
ray status

# Restart Ray
ray stop
ray start --head
```

## Production Checklist

- [ ] All environment variables configured
- [ ] Database migrations applied
- [ ] SSL/TLS certificates installed
- [ ] CORS configured for production domain
- [ ] API keys secured in secrets management
- [ ] Monitoring dashboards configured
- [ ] Backup scripts scheduled
- [ ] Log rotation configured
- [ ] Resource limits set (CPU, memory)
- [ ] Health checks enabled
- [ ] Error tracking configured (Sentry, etc.)
- [ ] Performance testing completed
- [ ] Security audit completed
- [ ] Documentation updated

## Support

For deployment issues:
- GitHub Issues: [evo-ai/issues](https://github.com/yourusername/evo-ai/issues)
- Email: support@yourdomain.com
- Slack: #evo-ai-support
