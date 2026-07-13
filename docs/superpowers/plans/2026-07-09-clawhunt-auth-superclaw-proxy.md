# ClawHunt Auth And SuperClaw Proxy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace Google auth UI with username/phone password auth and connect SuperClaw chat to a backend OpenAgents proxy.

**Architecture:** FastAPI owns auth, stores users in Postgres when running normally, and exposes a configurable `/api/superclaw/chat` proxy. React calls only the local backend API; OpenAgents host, agent name, chat path, MiniMax key, model, and base URL stay in backend environment variables.

**Tech Stack:** React 19, Vite, FastAPI, asyncpg, standard-library password hashing and HMAC tokens, pytest/httpx for backend tests.

---

### Task 1: Backend Auth And Proxy

**Files:**
- Modify: `backend/app/main.py`
- Modify: `backend/requirements.txt`
- Test: `backend/tests/test_api.py`

- [ ] Write failing tests for register, login, and chat proxy behavior.
- [ ] Implement password hashing, token creation, user table initialization, auth endpoints, and SuperClaw proxy endpoint.
- [ ] Verify backend tests pass with `python -m pytest`.

### Task 2: Frontend Auth And Chat Wiring

**Files:**
- Modify: `clawhunt/src/App.tsx`
- Modify: `clawhunt/src/styles.css`

- [ ] Replace Google auth form with username/phone password form.
- [ ] Add API client helpers for auth and SuperClaw chat.
- [ ] Make Studio and Agents Hub chat composers call `/api/superclaw/chat` and render returned messages.
- [ ] Verify TypeScript build with `npm run build`.

### Task 3: Environment And Run Config

**Files:**
- Modify: `.env`
- Modify: `.env.local`
- Modify: `clawhunt/vite.config.ts`

- [ ] Add OpenAgents/MiniMax backend environment variables.
- [ ] Add Vite dev proxy for `/api` to `127.0.0.1:8000`.
- [ ] Smoke test backend health and frontend build.
