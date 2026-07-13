# SuperClaw Workspace API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Route the local ClawHunt SuperClaw chat through OpenAgents Workspace so it reaches the Linux `superclaw` agent that already replies in the hosted Workspace.

**Architecture:** React continues to call the local FastAPI endpoint `/api/superclaw/chat`. FastAPI calls the OpenAgents Workspace event API at `https://workspace-endpoint.openagents.org` with the Workspace token, creates a temporary channel for the Linux `superclaw` agent, posts the user message, polls for the final agent reply, and returns the reply to React. Workspace token stays in local backend environment variables only.

**Tech Stack:** FastAPI, pytest, httpx, Vite React.

---

### Task 1: Replace Guessed HTTP Proxy With Workspace Event API

**Files:**
- Modify: `backend/tests/test_api.py`
- Modify: `backend/app/main.py`
- Modify: `backend/requirements.txt`
- Modify: `.env`
- Modify: `.env.local`

- [x] Add a backend test that stubs `httpx.AsyncClient` and proves `/api/superclaw/chat` creates a Workspace channel, posts a message, and polls `/v1/events`.
- [x] Run the targeted backend test and confirm it fails against the old integration shape.
- [x] Implement a Workspace event API helper in `backend/app/main.py`.
- [x] Update environment variable names in `.env` and `.env.local` to `OPENAGENTS_WORKSPACE_API_URL`, `OPENAGENTS_WORKSPACE_ID`, and `OPENAGENTS_WORKSPACE_TOKEN`.
- [x] Keep `httpx` as the only OpenAgents HTTP integration dependency.
- [x] Run backend tests.

### Task 2: Verify Local Frontend Path

**Files:**
- Existing: `clawhunt/src/App.tsx`
- Existing: `clawhunt/vite.config.ts`

- [x] Confirm React still posts to `/api/superclaw/chat`.
- [x] Run the frontend build to verify no TypeScript regression.
- [x] Start or reuse the backend and frontend dev servers.
- [x] Smoke test `POST http://127.0.0.1:8000/api/superclaw/chat` with a short message.
- [x] Smoke test `POST http://127.0.0.1:5173/api/superclaw/chat` to verify Vite proxy path.
