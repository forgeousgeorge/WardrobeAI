# WardrobeAI

AI-powered wardrobe manager and daily outfit suggester.

## Stack
- **Frontend**: React + TypeScript + Tailwind CSS (PWA, mobile-first for iPhone)
- **Backend**: FastAPI (Python 3.12)
- **Database**: PostgreSQL 16
- **Image Storage**: MinIO (S3-compatible)
- **AI**: Claude Vision API (classification + outfit suggestions)
- **Weather**: OpenWeatherMap forecast API
- **Orchestration**: Docker Compose

## Quick Start

### 1. Configure environment
```bash
cp .env.example .env
# Fill in your API keys in .env:
#   CLAUDE_API_KEY=sk-ant-...
#   OPENWEATHER_API_KEY=...
#   JWT_SECRET=$(openssl rand -hex 32)
```

### 2. Run migrations and start all services
```bash
docker compose up --build
```

The app is available at http://localhost. MinIO console at http://localhost:9001.

### 3. Run database migrations (first time)
```bash
docker compose exec backend alembic upgrade head
```

## Development (hot reload)
The `docker-compose.override.yml` is automatically applied in dev:
```bash
docker compose up --build
# Backend hot-reloads on file changes via uvicorn --reload
# Frontend served by Vite dev server at http://localhost:5173
```

## API Reference
All endpoints are prefixed `/api/v1`.

### Auth
| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Create account |
| POST | `/auth/login` | Login |
| POST | `/auth/refresh` | Refresh access token |
| POST | `/auth/logout` | Revoke refresh token |
| GET | `/auth/me` | Get current user |
| PATCH | `/auth/me` | Update profile (city, country_code for weather) |

### Clothing
| Method | Path | Description |
|--------|------|-------------|
| POST | `/clothing/upload` | Upload + auto-classify item |
| GET | `/clothing/` | List wardrobe (filterable) |
| PATCH | `/clothing/{id}` | Edit item metadata |
| DELETE | `/clothing/{id}` | Archive item |
| POST | `/clothing/{id}/archive` | Toggle archive state |

### Outfits
| Method | Path | Description |
|--------|------|-------------|
| GET | `/outfits/suggest?occasion=casual` | Get/generate daily suggestion |
| GET | `/outfits/` | Suggestion history |
| POST | `/outfits/{id}/rate` | Rate an outfit 1–5 |

### Health
| `GET /health` | `GET /health/ready` |

## Project Structure
```
WardrobeAI/
├── docker-compose.yml
├── docker-compose.override.yml   # dev overrides
├── .env.example
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── dependencies.py
│   │   ├── models/          # SQLAlchemy ORM
│   │   ├── schemas/         # Pydantic I/O
│   │   ├── routers/         # auth, clothing, outfits
│   │   └── services/        # claude, minio, weather, auth
│   └── alembic/             # DB migrations
└── frontend/
    └── src/
        ├── api/             # Typed API client
        ├── stores/          # Zustand state
        ├── components/      # UI components
        └── pages/           # Route pages
```
