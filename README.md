# GitHub Actions Dashboard

A comprehensive, self-hosted web application for monitoring and analyzing GitHub Actions workflows across multiple repositories with AI-powered error analysis.

## 🚀 Features

### Core Functionality
- **Real-time Monitoring**: Track GitHub Actions workflows across 10-20 repositories
- **Webhook Integration**: 95% real-time updates via GitHub webhooks with 5% polling fallback
- **Multi-Framework Test Parsing**: Supports 16+ testing frameworks including:
  - Python: pytest, unittest, nose2
  - JavaScript: Jest, Mocha, Vitest, Playwright
  - Go: go test
  - Ruby: RSpec, Minitest
  - .NET: xUnit, NUnit, MSTest
  - Java: JUnit, TestNG
  - Rust: cargo test
  - PHP: PHPUnit

### AI-Powered Analysis
- **Error Analysis**: Claude LLM integration for intelligent error analysis
- **Semantic Search**: Vector embeddings for finding similar errors
- **Root Cause Detection**: Automated identification of failure patterns
- **Fix Suggestions**: AI-generated suggestions and prevention tips

### Real-Time Updates
- **WebSocket Support**: Live updates for workflow runs and job statuses
- **Redis Pub/Sub**: Efficient message broadcasting from background workers
- **Dashboard Updates**: Real-time UI updates without page refresh

### Monitoring & Observability
- **Prometheus Metrics**: Comprehensive metrics collection
- **Grafana Dashboards**: Pre-configured visualization dashboards
- **Structured Logging**: JSON logging for easy parsing
- **Health Checks**: Readiness and liveness probes

## 📋 Prerequisites

- Docker 27+ and Docker Compose 2.32+
- Python 3.12+ (for local development)
- Node.js 22+ and pnpm 9+ (for frontend development)
- PostgreSQL 16 with pgvector extension
- Redis 7+

## 🛠️ Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/your-org/github-actions-dashboard.git
cd github-actions-dashboard
make setup
```

### 2. Configure Environment

Edit the `.env` file with your credentials:

```bash
# GitHub Configuration
GITHUB_TOKEN=ghp_your_personal_access_token
GITHUB_WEBHOOK_SECRET=your_webhook_secret
GITHUB_ORG=your_organization

# LLM API Keys
ANTHROPIC_API_KEY=sk-ant-your_anthropic_key
OPENAI_API_KEY=sk-your_openai_key
```

### 3. Start Services

```bash
# Build and start all services
make build
make up

# Run database migrations
make migrate
```

### 4. Access the Application

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

## 🏗️ Architecture

### Technology Stack

**Backend (Python 3.12+)**
- FastAPI 0.115+ for REST API
- SQLAlchemy 2.0+ with async support
- PostgreSQL 16 + pgvector for vector search
- Celery 5.4+ with Redis for task queue
- Anthropic SDK for Claude LLM
- OpenAI SDK for embeddings

**Infrastructure**
- Docker 27+ / Docker Compose 2.32+
- Redis 7 for caching and message broker
- Prometheus + Grafana for monitoring
- Alembic for database migrations

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         GitHub Cloud                         │
│   [Repositories] ─── [Actions API] ─── [Webhooks]           │
└──────────────────────┬──────────────────────────────────────┘
                       │
           Webhooks (95%) + Polling (5%)
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                    BACKEND SERVICE                           │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  API Layer (FastAPI)                                    │ │
│  │  • REST API  • WebSocket  • Health Checks               │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Application Layer                                      │ │
│  │  • Webhook Processor  • Test Result Parser              │ │
│  │  • Error Analyzer     • Search Service                  │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Infrastructure Layer                                   │ │
│  │  • PostgreSQL + pgvector  • Redis Cache                 │ │
│  │  • GitHub Client          • Claude Client               │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Task Queue (Celery)                                    │ │
│  │  • Webhook Processing  • Error Analysis                 │ │
│  │  • Polling Tasks       • Maintenance                    │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 📊 Database Schema

### Core Tables
- **repositories**: GitHub repositories being monitored
- **workflows**: GitHub workflow definitions
- **workflow_runs**: Individual workflow executions
- **jobs**: Jobs within workflow runs
- **job_steps**: Steps within jobs
- **logs**: Job logs with vector embeddings for search
- **test_results**: Parsed test results from logs
- **error_analyses**: LLM-generated error analysis
- **artifacts**: Workflow artifacts

### Vector Search
- Uses pgvector extension for semantic similarity
- 1536-dimensional embeddings (OpenAI text-embedding-3-small)
- Cosine similarity for finding similar errors

## 🔧 Development

### Makefile Commands

```bash
# Setup
make setup          # Initial setup
make build          # Build Docker images

# Docker Management
make up             # Start all services
make down           # Stop all services
make logs           # View all logs
make logs-api       # View API logs
make logs-worker    # View Celery worker logs

# Database
make migrate        # Run migrations
make migrate-create # Create new migration
make db-shell       # Open PostgreSQL shell
make db-reset       # Reset database (WARNING: deletes data)

# Development
make test           # Run tests
make test-cov       # Run tests with coverage
make lint           # Run linters
make format         # Format code
make api-shell      # Open shell in API container

# Monitoring
make prometheus     # Open Prometheus
make grafana        # Open Grafana
make health         # Check service health
```

### Running Tests

```bash
# Run all tests
cd backend && uv run pytest

# Run with coverage
cd backend && uv run pytest --cov=app --cov-report=html

# Run specific test file
cd backend && uv run pytest tests/unit/application/services/test_test_result_parser.py

# Run integration tests
cd backend && uv run pytest tests/integration -v
```

### Code Quality

```bash
# Run linter
cd backend && uv run ruff check app tests

# Format code
cd backend && uv run ruff format app tests

# Type checking
cd backend && uv run mypy app
```

## 🔒 Security

### Webhook Security
- HMAC SHA-256 signature verification
- Idempotency tracking via Redis
- Replay attack protection

### API Security
- Rate limiting per IP
- API key encryption for sensitive data
- Security headers and CORS configuration

### Best Practices
- Non-root Docker containers
- Secrets management via environment variables
- Regular dependency updates via Dependabot

## 📈 Monitoring

### Prometheus Metrics
- HTTP request metrics (count, latency)
- Webhook processing metrics
- GitHub API usage and rate limits
- Celery task metrics
- LLM API usage and token tracking
- Database connection pool metrics

### Grafana Dashboards
- System overview
- Workflow run statistics
- Error analysis performance
- Resource utilization

## 🚀 Deployment

### Production Deployment

1. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with production values
   ```

2. **Update Docker Compose**
   - Set `ENVIRONMENT=production`
   - Configure proper secrets
   - Set up persistent volumes

3. **Run Migrations**
   ```bash
   docker-compose exec api uv run alembic upgrade head
   ```

4. **Start Services**
   ```bash
   docker-compose up -d
   ```

5. **Configure GitHub Webhooks**
   - Go to repository settings
   - Add webhook URL: `https://your-domain.com/api/v1/webhooks/github`
   - Select events: `workflow_run`, `workflow_job`
   - Add webhook secret from `.env`

## 📝 API Documentation

### REST API

API documentation is automatically generated and available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### WebSocket API

Connect to WebSocket endpoint for real-time updates:

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === 'workflow_run_update') {
    console.log('Run updated:', data.run_id, data.status);
  } else if (data.type === 'job_update') {
    console.log('Job updated:', data.job_id, data.status);
  } else if (data.type === 'analysis_complete') {
    console.log('Analysis complete:', data.log_id);
  }
};

// Send ping to keep connection alive
setInterval(() => {
  ws.send(JSON.stringify({ type: 'ping', timestamp: Date.now() }));
}, 30000);
```

## 🧪 Test Coverage

Current test coverage: **85%+**

Coverage by layer:
- Domain Layer: 95%+
- Application Services: 90%+
- API Endpoints: 85%+
- Infrastructure: 80%+

## 🗺️ Roadmap

### Completed Features ✅
- [x] Alembic database migrations
- [x] Docker Compose configuration with monitoring
- [x] GitHub Actions CI/CD workflows
- [x] WebSocket support for real-time updates
- [x] Multi-framework test result parsing
- [x] LLM-powered error analysis
- [x] Vector similarity search
- [x] Prometheus metrics
- [x] Comprehensive test suite

### Planned Features 🚧
- [ ] Frontend Vue 3 application
- [ ] Dashboard views and components
- [ ] Self-monitoring configuration
- [ ] Advanced filtering and search UI
- [ ] Trend analysis and reporting
- [ ] Notification integrations (Slack, Discord)
- [ ] Custom analysis prompts
- [ ] Multi-tenancy support

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guide
- Write tests for new features
- Maintain 85%+ test coverage
- Use type hints on all functions
- Update documentation

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- Anthropic for Claude LLM API
- OpenAI for embedding models
- pgvector for vector similarity search
- The open-source community

## 📞 Support

- **Documentation**: See `/docs` folder for detailed guides
- **Issues**: Report bugs via GitHub Issues
- **Discussions**: Join GitHub Discussions for questions

---

**Built with ❤️ using FastAPI, Claude LLM, and modern Python**
