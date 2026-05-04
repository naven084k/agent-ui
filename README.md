# Nexora Agent

A lightweight AI chat workspace with a clean UI, multi-agent routing, real-time tool execution, and per-client chat isolation — no login required.

## Stack

| Layer | Tech |
|-------|------|
| Frontend | React, TypeScript, Vite, TailwindCSS, Framer Motion |
| Backend | FastAPI, SQLite |
| Model runtime | OpenAI API (any OpenAI-compatible endpoint) |

## Quick Start

### One-shot setup

```bash
bash start.sh
```

### Manual setup

```bash
# 1. Install frontend dependencies
npm install

# 2. Install backend dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -e ./backend

# 3. Configure environment
cp .env.example .env
# Edit .env and fill in your keys (see Environment below)

# 4. Run both servers
npm run dev
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |

To stop: press `Ctrl+C` in the terminal running `npm run dev`.  
To kill only the backend: `lsof -ti :8000 | xargs kill -9`

### Docker

```bash
docker compose up --build
```

## Environment

Copy `.env.example` to `.env` and fill in your values:

```env
OPENAI_API_KEY=sk-...          # Required — OpenAI or compatible key
OPENAI_BASE_URL=https://api.openai.com/v1  # Change for local/other providers
DEFAULT_MODEL=gpt-4o-mini      # Default model for new chats
SERPAPI_KEY=...                # Required for Google Search tool
SQLITE_PATH=backend/data/app.db
```

## Features

### Chat
- Streaming responses with real-time token display
- Multi-turn conversation history (last 20 messages sent to model)
- Per-conversation model selection
- Rename, delete, and regenerate responses
- Sidebar with search across chat titles and messages

### Multi-Agent Routing
Each message is automatically routed to the best specialist agent:

| Agent | Handles |
|-------|---------|
| **WeatherAgent** | Current conditions, multi-day forecasts, air quality |
| **SearchAgent** | Web search, stock prices, Wikipedia, currency conversion, word definitions, country facts |

### Tools (real-time data, no hallucination)

| Tool | API | Key required |
|------|-----|:---:|
| `weather_current` | Open-Meteo | No |
| `weather_forecast` | Open-Meteo | No |
| `air_quality` | Open-Meteo | No |
| `google_search` | SerpAPI | Yes (`SERPAPI_KEY`) |
| `wikipedia_search` | Wikipedia REST API | No |
| `stock_price` | Yahoo Finance (with crumb auth + Stooq fallback) | No |
| `currency_convert` | Frankfurter | No |
| `dictionary_lookup` | Free Dictionary API | No |
| `country_info` | Rest Countries | No |

Tool calls are visible inline in the chat — inputs, outputs, and status.

### Client Isolation
Chats are public (no login) but machine-specific. A UUID is generated on first visit and stored in `localStorage`. Every request carries it as `X-Client-ID`. The backend scopes all queries to that ID — other devices see a completely separate chat history.

## Project Structure

```
agent-ui/
├── frontend/               React + Vite UI
│   └── src/
│       ├── components/     Chat UI components
│       └── lib/            API client, types, utilities
├── backend/
│   └── app/
│       ├── services/
│       │   ├── agent.py    Multi-agent router + tool loop
│       │   ├── tools.py    Tool implementations
│       │   ├── openai.py   OpenAI client (streaming + one-shot)
│       │   └── store.py    SQLite chat/message persistence
│       ├── config.py       Pydantic settings (reads .env)
│       ├── db.py           Schema init + migrations
│       ├── main.py         FastAPI routes
│       └── schemas.py      Pydantic models
├── .env.example
├── package.json            npm workspaces + concurrently scripts
└── start.sh                One-shot bootstrap script
```
