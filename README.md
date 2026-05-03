# Nexora Agent

A lightweight AI workspace with a clean chat UI, OpenAI-backed chat, specialist agents, and SQLite persistence.

## Stack

- Frontend: React, TypeScript, Vite, TailwindCSS, Framer Motion
- Backend: FastAPI, SQLite
- Model runtime: OpenAI API

## Quick Start

1. Install frontend dependencies:

```bash
npm install
```

2. Install backend dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ./backend
```

3. Copy env config and set your OpenAI API key:

```bash
cp .env.example .env
```

Set `OPENAI_API_KEY` in `.env`. You can also change `DEFAULT_MODEL` if needed.

4. Start both apps:

```bash
npm run dev
```

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`

## Features

- Minimal desktop-first chat workspace
- Streaming OpenAI responses
- Specialist agents for finance, stock research, weather, and news
- Local tool execution with visible tool logs
- SQLite chat storage

## Structure

```text
frontend/   React UI
backend/    FastAPI API, agent orchestration, storage
```
