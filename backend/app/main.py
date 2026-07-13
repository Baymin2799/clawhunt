import asyncio
import base64
import hashlib
import hmac
import os
import re
import secrets
from contextlib import asynccontextmanager
from datetime import date, datetime, timezone
from typing import Any, Literal

import asyncpg
import httpx
import redis.asyncio as redis
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await ensure_schema()
    yield


app = FastAPI(title="ClawHunt API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MEMORY_USERS: dict[str, dict[str, Any]] = {}
MEMORY_TASKS: dict[str, dict[str, Any]] = {}

PROBLEM_TEMPLATES = [
    {
        "slug": "documentation",
        "title": "文档",
        "description": "目标受众、缺失文档和预期输出格式。",
        "category": "other",
        "difficulty": "easy",
        "budget_min": 15,
        "budget_max": 50,
        "title_template": "为项目补齐清晰、可维护的文档",
        "description_template": "说明目标受众、当前缺失内容、需要覆盖的主题以及预期交付格式。",
    },
    {
        "slug": "api-integration",
        "title": "API 集成",
        "description": "第三方 API 集成、身份验证、错误处理和可观测结果。",
        "category": "api",
        "difficulty": "medium",
        "budget_min": 50,
        "budget_max": 150,
        "title_template": "集成第三方 API 到现有产品流程",
        "description_template": "描述目标 API、认证方式、数据映射、错误处理、重试和可观测性要求。",
    },
    {
        "slug": "bug-fix",
        "title": "Bug 修复",
        "description": "结构化复现步骤、预期对比实际以及调试上下文。",
        "category": "backend",
        "difficulty": "easy",
        "budget_min": 30,
        "budget_max": 80,
        "title_template": "修复可稳定复现的产品缺陷",
        "description_template": "写明复现步骤、实际结果、预期结果、运行环境和相关日志。",
    },
    {
        "slug": "code-review",
        "title": "代码审查",
        "description": "仓库链接、审查重点和预期审查可交付物。",
        "category": "backend",
        "difficulty": "easy",
        "budget_min": 20,
        "budget_max": 60,
        "title_template": "审查代码并输出可执行的改进建议",
        "description_template": "提供仓库或代码链接、审查范围、风险重点以及期望的报告格式。",
    },
    {
        "slug": "data-pipeline",
        "title": "数据管道",
        "description": "输入输出结构、调度、监控和回溯需求。",
        "category": "data",
        "difficulty": "medium",
        "budget_min": 60,
        "budget_max": 180,
        "title_template": "构建可监控的数据处理管道",
        "description_template": "说明数据源、目标格式、处理规模、调度方式、监控和失败回溯要求。",
    },
    {
        "slug": "feature-request",
        "title": "功能请求",
        "description": "用户故事、范围、验收标准和发布说明。",
        "category": "frontend",
        "difficulty": "medium",
        "budget_min": 80,
        "budget_max": 180,
        "title_template": "实现一项可验收的产品功能",
        "description_template": "描述用户故事、功能范围、交互要求、技术约束和验收标准。",
    },
]

DELIVERY_STANDARDS = [
    {
        "slug": "standard-l0",
        "name": "普通交付（L0）",
        "level": "l0",
        "description": "提供最终交付物和简要使用说明。",
        "evidence_requirements": ["最终交付物", "使用说明"],
    },
    {
        "slug": "protocol-l1",
        "name": "协议交付（L1）",
        "level": "l1",
        "description": "提供交付清单、运行步骤和变更说明。",
        "evidence_requirements": ["交付清单", "运行步骤", "变更说明"],
    },
    {
        "slug": "verified-l2",
        "name": "已验证协议交付（L2）",
        "level": "l2",
        "description": "在 L1 基础上提供测试、日志或截图等可复核证据。",
        "evidence_requirements": ["交付清单", "测试结果", "运行日志或截图"],
    },
    {
        "slug": "platform-l3",
        "name": "平台协议交付（L3）",
        "level": "l3",
        "description": "由平台审核完整证据包并记录验收结论。",
        "evidence_requirements": ["完整证据包", "测试结果", "平台审核记录"],
    },
]


class RegisterRequest(BaseModel):
    username: str | None = None
    phone: str | None = None
    password: str = Field(min_length=6)


class LoginRequest(BaseModel):
    identifier: str
    password: str = Field(min_length=1)


class PublicUser(BaseModel):
    id: str
    username: str | None = None
    phone: str | None = None


class AuthResponse(BaseModel):
    user: PublicUser
    token: str


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    history: list[ChatMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    reply: str
    agent: str
    raw: dict[str, Any] | None = None


TaskSource = Literal["manual", "github"]
DeliveryMethod = Literal["platform", "github"]
RoutingStrategy = Literal["leaderboard", "direct", "marketplace"]
TaskDifficulty = Literal["easy", "medium", "hard", "expert"]
TaskCategory = Literal["ai", "backend", "frontend", "data", "devops", "security", "api", "other"]
ReviewMode = Literal["self", "ai"]
DeliveryProtocol = Literal["l0", "l1", "l2", "l3"]
TaskStatus = Literal["draft", "open", "assigned", "in_progress", "submitted", "completed", "cancelled", "rejected"]


class TaskCreateRequest(BaseModel):
    source: TaskSource = "manual"
    github_issue_url: str | None = Field(default=None, max_length=500)
    delivery_method: DeliveryMethod = "platform"
    routing_strategy: RoutingStrategy = "leaderboard"
    target_agent: str | None = Field(default=None, max_length=120)
    delivery_standard_id: str | None = Field(default=None, max_length=80)
    template_id: str | None = Field(default=None, max_length=80)
    title: str = Field(min_length=4, max_length=200)
    description: str = Field(min_length=20, max_length=20_000)
    acceptance_criteria: str | None = Field(default=None, max_length=10_000)
    difficulty: TaskDifficulty = "medium"
    category: TaskCategory = "other"
    deadline: date | None = None
    reference_url: str | None = Field(default=None, max_length=1000)
    review_mode: ReviewMode = "self"
    delivery_protocol: DeliveryProtocol = "l0"
    budget: float | None = Field(default=None, ge=0, le=1000)
    knowledge_compensation: Literal[0, 25, 50] = 0


class TaskUpdateRequest(BaseModel):
    source: TaskSource | None = None
    github_issue_url: str | None = Field(default=None, max_length=500)
    delivery_method: DeliveryMethod | None = None
    routing_strategy: RoutingStrategy | None = None
    target_agent: str | None = Field(default=None, max_length=120)
    delivery_standard_id: str | None = Field(default=None, max_length=80)
    template_id: str | None = Field(default=None, max_length=80)
    title: str | None = Field(default=None, min_length=4, max_length=200)
    description: str | None = Field(default=None, min_length=20, max_length=20_000)
    acceptance_criteria: str | None = Field(default=None, max_length=10_000)
    difficulty: TaskDifficulty | None = None
    category: TaskCategory | None = None
    deadline: date | None = None
    reference_url: str | None = Field(default=None, max_length=1000)
    review_mode: ReviewMode | None = None
    delivery_protocol: DeliveryProtocol | None = None
    budget: float | None = Field(default=None, ge=0, le=1000)
    knowledge_compensation: Literal[0, 25, 50] | None = None


class TaskResponse(BaseModel):
    id: str
    owner_id: str
    owner_name: str
    source: TaskSource
    github_issue_url: str | None = None
    delivery_method: DeliveryMethod
    routing_strategy: RoutingStrategy
    target_agent: str | None = None
    delivery_standard_id: str | None = None
    template_id: str | None = None
    title: str
    description: str
    acceptance_criteria: str | None = None
    difficulty: TaskDifficulty
    category: TaskCategory
    deadline: date | None = None
    reference_url: str | None = None
    review_mode: ReviewMode
    delivery_protocol: DeliveryProtocol
    budget: float | None = None
    knowledge_compensation: int
    status: TaskStatus
    bid_count: int = 0
    created_at: datetime
    updated_at: datetime


class TaskListResponse(BaseModel):
    items: list[TaskResponse]
    total: int


class GitHubIssueImportRequest(BaseModel):
    url: str = Field(min_length=1, max_length=500)


class GitHubIssueImportResponse(BaseModel):
    title: str
    description: str
    reference_url: str


def auth_store() -> str:
    return os.getenv("CLAWHUNT_AUTH_STORE", "postgres").lower()


def normalize_identifier(value: str | None) -> str:
    return (value or "").strip().lower()


def primary_identifier(username: str | None, phone: str | None) -> str:
    identifier = normalize_identifier(username) or normalize_identifier(phone)
    if not identifier:
        raise HTTPException(status_code=422, detail="username or phone is required")
    return identifier


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 240_000)
    return "pbkdf2_sha256$240000$" + base64.b64encode(salt).decode("ascii") + "$" + base64.b64encode(digest).decode("ascii")


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        _, iterations, salt_text, digest_text = stored_hash.split("$", 3)
        salt = base64.b64decode(salt_text.encode("ascii"))
        expected = base64.b64decode(digest_text.encode("ascii"))
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iterations))
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def create_token(user_id: str, identifier: str) -> str:
    secret = os.getenv("AUTH_TOKEN_SECRET", "clawhunt-local-dev-secret")
    issued_at = str(int(datetime.now(timezone.utc).timestamp()))
    payload = f"{user_id}:{identifier}:{issued_at}"
    signature = hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    token = base64.urlsafe_b64encode(f"{payload}:{signature}".encode("utf-8")).decode("ascii")
    return token.rstrip("=")


def public_user(row: dict[str, Any]) -> PublicUser:
    return PublicUser(id=str(row["id"]), username=row.get("username"), phone=row.get("phone"))


async def connect_db():
    return await asyncpg.connect(os.environ["DATABASE_URL"])


async def ensure_schema():
    if auth_store() == "memory":
        return

    conn = await connect_db()
    try:
        await conn.execute(
            """
            create table if not exists users (
                id bigserial primary key,
                identifier text not null unique,
                username text,
                phone text,
                password_hash text not null,
                created_at timestamptz not null default now()
            )
            """
        )
        await conn.execute(
            """
            create table if not exists problem_templates (
                slug text primary key,
                title text not null,
                description text not null,
                category text not null,
                difficulty text not null,
                budget_min double precision not null,
                budget_max double precision not null,
                title_template text not null,
                description_template text not null
            );

            create table if not exists delivery_standards (
                slug text primary key,
                name text not null,
                level text not null,
                description text not null,
                evidence_requirements text[] not null default '{}'
            );

            create table if not exists tasks (
                id bigserial primary key,
                owner_id bigint not null references users(id),
                source text not null default 'manual',
                github_issue_url text,
                delivery_method text not null default 'platform',
                routing_strategy text not null default 'leaderboard',
                target_agent text,
                delivery_standard_id text references delivery_standards(slug),
                template_id text references problem_templates(slug),
                title text not null,
                description text not null,
                acceptance_criteria text,
                difficulty text not null,
                category text not null,
                deadline date,
                reference_url text,
                review_mode text not null default 'self',
                delivery_protocol text not null default 'l0',
                budget double precision,
                knowledge_compensation integer not null default 0,
                status text not null default 'open',
                bid_count integer not null default 0,
                created_at timestamptz not null default now(),
                updated_at timestamptz not null default now()
            );

            create index if not exists tasks_status_created_idx on tasks(status, created_at desc);
            create index if not exists tasks_owner_created_idx on tasks(owner_id, created_at desc);
            """
        )
        await conn.executemany(
            """
            insert into problem_templates (
                slug, title, description, category, difficulty, budget_min,
                budget_max, title_template, description_template
            ) values ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            on conflict (slug) do update set
                title = excluded.title,
                description = excluded.description,
                category = excluded.category,
                difficulty = excluded.difficulty,
                budget_min = excluded.budget_min,
                budget_max = excluded.budget_max,
                title_template = excluded.title_template,
                description_template = excluded.description_template
            """,
            [
                (
                    item["slug"],
                    item["title"],
                    item["description"],
                    item["category"],
                    item["difficulty"],
                    item["budget_min"],
                    item["budget_max"],
                    item["title_template"],
                    item["description_template"],
                )
                for item in PROBLEM_TEMPLATES
            ],
        )
        await conn.executemany(
            """
            insert into delivery_standards (slug, name, level, description, evidence_requirements)
            values ($1, $2, $3, $4, $5)
            on conflict (slug) do update set
                name = excluded.name,
                level = excluded.level,
                description = excluded.description,
                evidence_requirements = excluded.evidence_requirements
            """,
            [
                (
                    item["slug"],
                    item["name"],
                    item["level"],
                    item["description"],
                    item["evidence_requirements"],
                )
                for item in DELIVERY_STANDARDS
            ],
        )
    finally:
        await conn.close()


async def find_user(identifier: str) -> dict[str, Any] | None:
    if auth_store() == "memory":
        return MEMORY_USERS.get(identifier)

    conn = await connect_db()
    try:
        row = await conn.fetchrow(
            "select id, username, phone, password_hash from users where identifier = $1",
            identifier,
        )
        return dict(row) if row else None
    finally:
        await conn.close()


async def find_user_by_id(user_id: str) -> dict[str, Any] | None:
    if auth_store() == "memory":
        for row in MEMORY_USERS.values():
            if str(row["id"]) == str(user_id):
                return row
        return None

    try:
        numeric_id = int(user_id)
    except ValueError:
        return None

    conn = await connect_db()
    try:
        row = await conn.fetchrow(
            "select id, identifier, username, phone, password_hash from users where id = $1",
            numeric_id,
        )
        return dict(row) if row else None
    finally:
        await conn.close()


def verify_token(token: str) -> tuple[str, str]:
    try:
        padded = token + "=" * (-len(token) % 4)
        decoded = base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8")
        parts = decoded.split(":")
        if len(parts) < 4:
            raise ValueError("invalid token")
        user_id = parts[0]
        identifier = ":".join(parts[1:-2])
        issued_at = parts[-2]
        signature = parts[-1]
        payload = f"{user_id}:{identifier}:{issued_at}"
        secret = os.getenv("AUTH_TOKEN_SECRET", "clawhunt-local-dev-secret")
        expected = hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
        if not identifier or not hmac.compare_digest(signature, expected):
            raise ValueError("invalid token")
        return user_id, identifier
    except Exception as exc:
        raise HTTPException(status_code=401, detail="invalid or expired token") from exc


async def current_user(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="login required")
    user_id, identifier = verify_token(authorization[7:].strip())
    user = await find_user_by_id(user_id)
    if not user or normalize_identifier(user.get("identifier")) != normalize_identifier(identifier):
        raise HTTPException(status_code=401, detail="invalid or expired token")
    return user


async def insert_user(identifier: str, username: str | None, phone: str | None, password: str) -> dict[str, Any]:
    existing = await find_user(identifier)
    if existing:
        raise HTTPException(status_code=409, detail="account already exists")

    password_hash = hash_password(password)
    if auth_store() == "memory":
        row = {
            "id": str(len(MEMORY_USERS) + 1),
            "identifier": identifier,
            "username": username.strip() if username else None,
            "phone": phone.strip() if phone else None,
            "password_hash": password_hash,
        }
        MEMORY_USERS[identifier] = row
        return row

    conn = await connect_db()
    try:
        row = await conn.fetchrow(
            """
            insert into users (identifier, username, phone, password_hash)
            values ($1, $2, $3, $4)
            returning id, username, phone, password_hash
            """,
            identifier,
            username.strip() if username else None,
            phone.strip() if phone else None,
            password_hash,
        )
        return dict(row)
    finally:
        await conn.close()


@app.get("/api/health")
async def health():
    return {"ok": True}


@app.get("/api/ready")
async def ready():
    db_status = "ok"
    redis_status = "ok"

    try:
        conn = await asyncpg.connect(os.environ["DATABASE_URL"])
        await conn.execute("select 1")
        await conn.close()
    except Exception as exc:
        db_status = f"error: {type(exc).__name__}"

    try:
        client = redis.from_url(os.environ["REDIS_URL"])
        await client.ping()
        await client.aclose()
    except Exception as exc:
        redis_status = f"error: {type(exc).__name__}"

    return {
        "ok": db_status == "ok" and redis_status == "ok",
        "postgres": db_status,
        "redis": redis_status,
        "openagents_workspace_api_url": os.getenv("OPENAGENTS_WORKSPACE_API_URL", "https://workspace-endpoint.openagents.org"),
        "openagents_workspace_id": os.getenv("OPENAGENTS_WORKSPACE_ID"),
        "openagents_agent": os.getenv("OPENAGENTS_AGENT", "superclaw"),
    }


@app.post("/api/auth/register", response_model=AuthResponse)
async def register(payload: RegisterRequest):
    identifier = primary_identifier(payload.username, payload.phone)
    row = await insert_user(identifier, payload.username, payload.phone, payload.password)
    return AuthResponse(user=public_user(row), token=create_token(str(row["id"]), identifier))


@app.post("/api/auth/login", response_model=AuthResponse)
async def login(payload: LoginRequest):
    identifier = normalize_identifier(payload.identifier)
    row = await find_user(identifier)
    if not row or not verify_password(payload.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="invalid credentials")

    return AuthResponse(user=public_user(row), token=create_token(str(row["id"]), identifier))


def task_response(row: dict[str, Any]) -> dict[str, Any]:
    data = dict(row)
    data["id"] = str(data["id"])
    data["owner_id"] = str(data["owner_id"])
    data["owner_name"] = data.get("owner_name") or "ClawHunt 用户"
    data["budget"] = float(data["budget"]) if data.get("budget") is not None else None
    return data


async def fetch_task(task_id: str) -> dict[str, Any] | None:
    if auth_store() == "memory":
        row = MEMORY_TASKS.get(str(task_id))
        return task_response(row) if row else None

    try:
        numeric_id = int(task_id)
    except ValueError:
        return None

    conn = await connect_db()
    try:
        row = await conn.fetchrow(
            """
            select t.*, coalesce(u.username, u.phone, 'ClawHunt 用户') as owner_name
            from tasks t
            join users u on u.id = t.owner_id
            where t.id = $1
            """,
            numeric_id,
        )
        return task_response(dict(row)) if row else None
    finally:
        await conn.close()


async def create_task_record(payload: TaskCreateRequest, user: dict[str, Any]) -> dict[str, Any]:
    values = payload.model_dump()
    now = datetime.now(timezone.utc)
    if auth_store() == "memory":
        task_id = str(len(MEMORY_TASKS) + 1)
        row = {
            "id": task_id,
            "owner_id": str(user["id"]),
            "owner_name": user.get("username") or user.get("phone") or "ClawHunt 用户",
            **values,
            "status": "open",
            "bid_count": 0,
            "created_at": now,
            "updated_at": now,
        }
        MEMORY_TASKS[task_id] = row
        return task_response(row)

    conn = await connect_db()
    try:
        row = await conn.fetchrow(
            """
            insert into tasks (
                owner_id, source, github_issue_url, delivery_method, routing_strategy,
                target_agent, delivery_standard_id, template_id, title, description,
                acceptance_criteria, difficulty, category, deadline, reference_url,
                review_mode, delivery_protocol, budget, knowledge_compensation
            ) values (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                $11, $12, $13, $14, $15, $16, $17, $18, $19
            )
            returning *
            """,
            int(user["id"]),
            values["source"],
            values["github_issue_url"],
            values["delivery_method"],
            values["routing_strategy"],
            values["target_agent"],
            values["delivery_standard_id"],
            values["template_id"],
            values["title"].strip(),
            values["description"].strip(),
            values["acceptance_criteria"].strip() if values["acceptance_criteria"] else None,
            values["difficulty"],
            values["category"],
            values["deadline"],
            values["reference_url"],
            values["review_mode"],
            values["delivery_protocol"],
            values["budget"],
            values["knowledge_compensation"],
        )
        result = dict(row)
        result["owner_name"] = user.get("username") or user.get("phone") or "ClawHunt 用户"
        return task_response(result)
    finally:
        await conn.close()


async def list_task_records(
    owner_id: str | None = None,
    status: str | None = None,
    difficulty: str | None = None,
    category: str | None = None,
    search: str | None = None,
) -> list[dict[str, Any]]:
    if auth_store() == "memory":
        rows = [task_response(row) for row in MEMORY_TASKS.values()]
        if owner_id is None:
            rows = [row for row in rows if row["status"] not in {"draft", "cancelled"}]
        else:
            rows = [row for row in rows if row["owner_id"] == str(owner_id)]
        if status:
            rows = [row for row in rows if row["status"] == status]
        if difficulty:
            rows = [row for row in rows if row["difficulty"] == difficulty]
        if category:
            rows = [row for row in rows if row["category"] == category]
        if search:
            needle = search.lower()
            rows = [row for row in rows if needle in row["title"].lower() or needle in row["description"].lower()]
        return sorted(rows, key=lambda row: row["created_at"], reverse=True)

    clauses: list[str] = []
    values: list[Any] = []

    def add_clause(sql: str, value: Any):
        values.append(value)
        clauses.append(sql.replace("?", f"${len(values)}"))

    if owner_id is None:
        clauses.append("t.status not in ('draft', 'cancelled')")
    else:
        add_clause("t.owner_id = ?", int(owner_id))
    if status:
        add_clause("t.status = ?", status)
    if difficulty:
        add_clause("t.difficulty = ?", difficulty)
    if category:
        add_clause("t.category = ?", category)
    if search:
        pattern = f"%{search}%"
        values.append(pattern)
        title_parameter = len(values)
        values.append(pattern)
        description_parameter = len(values)
        clauses.append(f"(t.title ilike ${title_parameter} or t.description ilike ${description_parameter})")

    where_sql = " where " + " and ".join(clauses) if clauses else ""
    conn = await connect_db()
    try:
        rows = await conn.fetch(
            """
            select t.*, coalesce(u.username, u.phone, 'ClawHunt 用户') as owner_name
            from tasks t
            join users u on u.id = t.owner_id
            """
            + where_sql
            + " order by t.created_at desc",
            *values,
        )
        return [task_response(dict(row)) for row in rows]
    finally:
        await conn.close()


async def update_task_record(task: dict[str, Any], changes: dict[str, Any]) -> dict[str, Any]:
    if not changes:
        return task
    if task["status"] not in {"draft", "open"}:
        raise HTTPException(status_code=409, detail="only draft or open tasks can be edited")

    if auth_store() == "memory":
        row = MEMORY_TASKS[task["id"]]
        row.update(changes)
        row["updated_at"] = datetime.now(timezone.utc)
        return task_response(row)

    assignments: list[str] = []
    values: list[Any] = []
    for field, value in changes.items():
        values.append(value)
        assignments.append(f"{field} = ${len(values)}")
    values.append(int(task["id"]))
    assignments.append("updated_at = now()")
    conn = await connect_db()
    try:
        row = await conn.fetchrow(
            f"update tasks set {', '.join(assignments)} where id = ${len(values)} returning *",
            *values,
        )
        result = dict(row)
        result["owner_name"] = task["owner_name"]
        return task_response(result)
    finally:
        await conn.close()


async def cancel_task_record(task: dict[str, Any]) -> dict[str, Any]:
    if task["status"] == "completed":
        raise HTTPException(status_code=409, detail="completed tasks cannot be cancelled")
    if task["status"] == "cancelled":
        return task

    if auth_store() == "memory":
        row = MEMORY_TASKS[task["id"]]
        row["status"] = "cancelled"
        row["updated_at"] = datetime.now(timezone.utc)
        return task_response(row)

    conn = await connect_db()
    try:
        row = await conn.fetchrow(
            "update tasks set status = 'cancelled', updated_at = now() where id = $1 returning *",
            int(task["id"]),
        )
        result = dict(row)
        result["owner_name"] = task["owner_name"]
        return task_response(result)
    finally:
        await conn.close()


def require_task_owner(task: dict[str, Any], user: dict[str, Any]):
    if task["owner_id"] != str(user["id"]):
        raise HTTPException(status_code=403, detail="only the task owner can modify this task")


@app.get("/api/problem-templates")
async def problem_templates():
    if auth_store() == "memory":
        return PROBLEM_TEMPLATES
    conn = await connect_db()
    try:
        rows = await conn.fetch("select * from problem_templates order by budget_min, title")
        return [dict(row) for row in rows]
    finally:
        await conn.close()


@app.get("/api/delivery-standards")
async def delivery_standards():
    if auth_store() == "memory":
        return DELIVERY_STANDARDS
    conn = await connect_db()
    try:
        rows = await conn.fetch("select * from delivery_standards order by level")
        return [dict(row) for row in rows]
    finally:
        await conn.close()


@app.get("/api/tasks", response_model=TaskListResponse)
async def tasks(
    status: str | None = Query(default=None),
    difficulty: str | None = Query(default=None),
    category: str | None = Query(default=None),
    search: str | None = Query(default=None, max_length=200),
):
    items = await list_task_records(status=status, difficulty=difficulty, category=category, search=search)
    return TaskListResponse(items=items, total=len(items))


@app.get("/api/tasks/mine", response_model=TaskListResponse)
async def my_tasks(user: dict[str, Any] = Depends(current_user)):
    items = await list_task_records(owner_id=str(user["id"]))
    return TaskListResponse(items=items, total=len(items))


@app.post("/api/tasks", response_model=TaskResponse, status_code=201)
async def create_task(payload: TaskCreateRequest, user: dict[str, Any] = Depends(current_user)):
    return await create_task_record(payload, user)


@app.post("/api/github/issues/import", response_model=GitHubIssueImportResponse)
async def import_github_issue(payload: GitHubIssueImportRequest, _user: dict[str, Any] = Depends(current_user)):
    match = re.fullmatch(r"https://github\.com/([^/]+)/([^/]+)/issues/(\d+)/?", payload.url.strip())
    if not match:
        raise HTTPException(status_code=422, detail="请输入公开 GitHub Issue 链接")
    owner, repository, issue_number = match.groups()
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "ClawHunt"}
    github_token = os.getenv("GITHUB_TOKEN")
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                f"https://api.github.com/repos/{owner}/{repository}/issues/{issue_number}",
                headers=headers,
            )
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="GitHub Issue 不存在或不是公开内容")
        response.raise_for_status()
        data = response.json()
    except HTTPException:
        raise
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="GitHub Issue 读取失败") from exc
    return GitHubIssueImportResponse(
        title=str(data.get("title") or "")[:200],
        description=str(data.get("body") or "暂无描述"),
        reference_url=str(data.get("html_url") or payload.url),
    )


@app.get("/api/tasks/{task_id}", response_model=TaskResponse)
async def task_detail(task_id: str):
    task = await fetch_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task not found")
    return task


@app.patch("/api/tasks/{task_id}", response_model=TaskResponse)
async def update_task(task_id: str, payload: TaskUpdateRequest, user: dict[str, Any] = Depends(current_user)):
    task = await fetch_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task not found")
    require_task_owner(task, user)
    return await update_task_record(task, payload.model_dump(exclude_unset=True))


@app.delete("/api/tasks/{task_id}", response_model=TaskResponse)
async def cancel_task(task_id: str, user: dict[str, Any] = Depends(current_user)):
    task = await fetch_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task not found")
    require_task_owner(task, user)
    return await cancel_task_record(task)


def extract_reply(data: dict[str, Any]) -> str:
    if isinstance(data.get("reply"), str):
        return data["reply"]
    if isinstance(data.get("content"), str):
        return data["content"]
    message = data.get("message")
    if isinstance(message, str):
        return message
    if isinstance(message, dict) and isinstance(message.get("content"), str):
        return message["content"]
    choices = data.get("choices")
    if isinstance(choices, list) and choices:
        first = choices[0]
        if isinstance(first, dict):
            nested_message = first.get("message")
            if isinstance(nested_message, dict) and isinstance(nested_message.get("content"), str):
                return nested_message["content"]
            if isinstance(first.get("text"), str):
                return first["text"]
    return "SuperClaw did not return a text response."


def workspace_headers() -> dict[str, str]:
    token = os.getenv("OPENAGENTS_WORKSPACE_TOKEN")
    if not token:
        raise RuntimeError("OPENAGENTS_WORKSPACE_TOKEN is required")
    return {"Content-Type": "application/json", "X-Workspace-Token": token}


def workspace_api_url(path: str) -> str:
    base_url = os.getenv("OPENAGENTS_WORKSPACE_API_URL", "https://workspace-endpoint.openagents.org").rstrip("/")
    return f"{base_url}/{path.lstrip('/')}"


def workspace_id() -> str:
    value = os.getenv("OPENAGENTS_WORKSPACE_ID")
    if not value:
        raise RuntimeError("OPENAGENTS_WORKSPACE_ID is required")
    return value


def response_data(response: httpx.Response) -> Any:
    response.raise_for_status()
    body = response.json()
    return body.get("data", body) if isinstance(body, dict) else body


def is_final_agent_message(event: dict[str, Any], agent: str) -> bool:
    if event.get("source") != f"openagents:{agent}":
        return False
    payload = event.get("payload")
    if not isinstance(payload, dict) or not isinstance(payload.get("content"), str):
        return False
    return payload.get("message_type", "chat") not in {"status", "thinking", "loading"}


async def call_openagents(payload: dict[str, Any]) -> dict[str, Any]:
    agent = payload["agent"]
    network = workspace_id()
    headers = workspace_headers()
    timeout = float(os.getenv("OPENAGENTS_TIMEOUT_SECONDS", "60"))
    poll_interval = float(os.getenv("OPENAGENTS_POLL_INTERVAL_SECONDS", "2"))

    async with httpx.AsyncClient(timeout=timeout) as client:
        create_response = await client.post(
            workspace_api_url("/v1/events"),
            json={
                "type": "network.channel.create",
                "source": "human:user",
                "target": "core",
                "payload": {
                    "title": os.getenv("OPENAGENTS_THREAD_TITLE", "ClawHunt SuperClaw"),
                    "master": agent,
                    "participants": [agent],
                },
                "network": network,
            },
            headers=headers,
        )
        channel_event = response_data(create_response)
        metadata = channel_event.get("metadata") if isinstance(channel_event, dict) else None
        channel = metadata.get("channel_name") if isinstance(metadata, dict) else None
        if not channel:
            raise RuntimeError("OpenAgents did not return a channel name")

        send_response = await client.post(
            workspace_api_url("/v1/events"),
            json={
                "type": "workspace.message.posted",
                "source": "human:clawhunt-web",
                "target": f"channel/{channel}",
                "payload": {
                    "content": payload["message"],
                    "sender_type": "human",
                    "sender_name": "ClawHunt",
                    "sender_id": "clawhunt-web",
                },
                "visibility": "channel",
                "network": network,
            },
            headers=headers,
        )
        sent_event = response_data(send_response)
        after_event = sent_event.get("id") if isinstance(sent_event, dict) else None

        deadline = asyncio.get_running_loop().time() + timeout
        while asyncio.get_running_loop().time() < deadline:
            params = {
                "network": network,
                "channel": channel,
                "type": "workspace.message",
                "limit": "200",
            }
            if after_event:
                params["after"] = after_event
            poll_response = await client.get(workspace_api_url("/v1/events"), params=params, headers=headers)
            poll_data = response_data(poll_response)
            events = poll_data.get("events", []) if isinstance(poll_data, dict) else []
            for event in events:
                if isinstance(event, dict) and is_final_agent_message(event, agent):
                    return {
                        "reply": event["payload"]["content"],
                        "agent": agent,
                        "event": event,
                        "channel": channel,
                    }
            if poll_interval > 0:
                await asyncio.sleep(poll_interval)

    raise TimeoutError(f"Timed out waiting for {agent} response")


@app.post("/api/superclaw/chat", response_model=ChatResponse)
async def superclaw_chat(payload: ChatRequest):
    agent = os.getenv("OPENAGENTS_AGENT", "superclaw")
    request_payload = {
        "agent": agent,
        "message": payload.message,
        "history": [message.model_dump() for message in payload.history],
        "model": os.getenv("MODEL", "minimax/MiniMax-M2.5"),
        "model_base_url": os.getenv("MINIMAX_BASE_URL", "https://api.minimaxi.com/anthropic"),
    }

    minimax_api_key = os.getenv("MINIMAX_API_KEY")
    if minimax_api_key:
        request_payload["minimax_api_key"] = minimax_api_key

    try:
        raw = await call_openagents(request_payload)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"openagents request failed: {type(exc).__name__}") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"openagents workspace request failed: {type(exc).__name__}") from exc

    return ChatResponse(reply=extract_reply(raw), agent=agent, raw=raw)
