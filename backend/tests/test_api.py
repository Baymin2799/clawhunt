import importlib

from fastapi.testclient import TestClient


def load_test_client(monkeypatch):
    monkeypatch.setenv("CLAWHUNT_AUTH_STORE", "memory")
    monkeypatch.setenv("OPENAGENTS_WORKSPACE_API_URL", "https://workspace-endpoint.openagents.org")
    monkeypatch.setenv("OPENAGENTS_WORKSPACE_ID", "test-workspace")
    monkeypatch.setenv("OPENAGENTS_WORKSPACE_TOKEN", "test-workspace-token")
    monkeypatch.setenv("OPENAGENTS_AGENT", "superclaw")
    monkeypatch.setenv("MODEL", "minimax/MiniMax-M2.5")
    monkeypatch.setenv("MINIMAX_BASE_URL", "https://api.minimaxi.com/anthropic")

    import app.main as main

    importlib.reload(main)
    return main, TestClient(main.app)


def test_register_and_login_with_username(monkeypatch):
    _, client = load_test_client(monkeypatch)

    register_response = client.post(
        "/api/auth/register",
        json={"username": "demo_user", "password": "pass1234"},
    )

    assert register_response.status_code == 200
    register_body = register_response.json()
    assert register_body["user"]["username"] == "demo_user"
    assert register_body["token"]

    login_response = client.post(
        "/api/auth/login",
        json={"identifier": "demo_user", "password": "pass1234"},
    )

    assert login_response.status_code == 200
    assert login_response.json()["user"]["username"] == "demo_user"
    assert login_response.json()["token"]


def test_register_accepts_phone_identifier(monkeypatch):
    _, client = load_test_client(monkeypatch)

    response = client.post(
        "/api/auth/register",
        json={"phone": "13800138000", "password": "123456"},
    )

    assert response.status_code == 200
    assert response.json()["user"]["phone"] == "13800138000"


def test_login_rejects_wrong_password(monkeypatch):
    _, client = load_test_client(monkeypatch)
    client.post("/api/auth/register", json={"username": "demo_user", "password": "pass1234"})

    response = client.post(
        "/api/auth/login",
        json={"identifier": "demo_user", "password": "wrongpass"},
    )

    assert response.status_code == 401


def register_user(client, username="task_owner"):
    response = client.post(
        "/api/auth/register",
        json={"username": username, "password": "pass1234"},
    )
    assert response.status_code == 200
    return response.json()


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def task_payload(**overrides):
    payload = {
        "source": "manual",
        "delivery_method": "platform",
        "routing_strategy": "leaderboard",
        "title": "为项目补齐发布任务后端",
        "description": "实现任务保存、市场列表、详情以及任务所有者管理接口。",
        "acceptance_criteria": "测试通过，发布后的任务可以在市场列表和我的任务中查询。",
        "difficulty": "medium",
        "category": "backend",
        "review_mode": "self",
        "delivery_protocol": "l0",
        "budget": 200,
        "knowledge_compensation": 0,
    }
    payload.update(overrides)
    return payload


def test_task_creation_requires_login(monkeypatch):
    _, client = load_test_client(monkeypatch)

    response = client.post("/api/tasks", json=task_payload())

    assert response.status_code == 401


def test_task_owner_can_publish_and_query_task(monkeypatch):
    _, client = load_test_client(monkeypatch)
    account = register_user(client)

    create_response = client.post(
        "/api/tasks",
        headers=auth_headers(account["token"]),
        json=task_payload(),
    )

    assert create_response.status_code == 201
    task = create_response.json()
    assert task["title"] == "为项目补齐发布任务后端"
    assert task["status"] == "open"
    assert task["owner_id"] == account["user"]["id"]
    assert task["owner_name"] == "task_owner"

    list_response = client.get("/api/tasks")
    assert list_response.status_code == 200
    assert list_response.json()["items"][0]["id"] == task["id"]

    detail_response = client.get(f"/api/tasks/{task['id']}")
    assert detail_response.status_code == 200
    assert detail_response.json()["description"] == task["description"]

    mine_response = client.get(
        "/api/tasks/mine",
        headers=auth_headers(account["token"]),
    )
    assert mine_response.status_code == 200
    assert mine_response.json()["items"][0]["id"] == task["id"]


def test_only_owner_can_edit_and_cancel_task(monkeypatch):
    _, client = load_test_client(monkeypatch)
    owner = register_user(client, "owner")
    other = register_user(client, "other")
    task = client.post(
        "/api/tasks",
        headers=auth_headers(owner["token"]),
        json=task_payload(),
    ).json()

    forbidden = client.patch(
        f"/api/tasks/{task['id']}",
        headers=auth_headers(other["token"]),
        json={"title": "不允许的修改"},
    )
    assert forbidden.status_code == 403

    updated = client.patch(
        f"/api/tasks/{task['id']}",
        headers=auth_headers(owner["token"]),
        json={"title": "更新后的任务标题", "budget": 320},
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "更新后的任务标题"
    assert updated.json()["budget"] == 320

    cancelled = client.delete(
        f"/api/tasks/{task['id']}",
        headers=auth_headers(owner["token"]),
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"


def test_task_metadata_is_seeded_and_budget_is_limited(monkeypatch):
    _, client = load_test_client(monkeypatch)
    account = register_user(client)

    templates = client.get("/api/problem-templates")
    standards = client.get("/api/delivery-standards")
    invalid_budget = client.post(
        "/api/tasks",
        headers=auth_headers(account["token"]),
        json=task_payload(budget=1000.01),
    )

    assert templates.status_code == 200
    assert any(item["slug"] == "api-integration" for item in templates.json())
    assert standards.status_code == 200
    assert any(item["level"] == "l2" for item in standards.json())
    assert invalid_budget.status_code == 422


def test_my_tasks_rejects_invalid_token(monkeypatch):
    _, client = load_test_client(monkeypatch)

    response = client.get(
        "/api/tasks/mine",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401


def test_github_issue_import_prefills_public_issue(monkeypatch):
    main, client = load_test_client(monkeypatch)
    account = register_user(client)

    class FakeResponse:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {
                "title": "Public issue title",
                "body": "Public issue body with enough detail for a task.",
                "html_url": "https://github.com/example/project/issues/12",
            }

    class FakeAsyncClient:
        def __init__(self, timeout):
            assert timeout == 15

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def get(self, url, headers):
            assert url == "https://api.github.com/repos/example/project/issues/12"
            assert headers["User-Agent"] == "ClawHunt"
            return FakeResponse()

    monkeypatch.setattr(main.httpx, "AsyncClient", FakeAsyncClient)

    response = client.post(
        "/api/github/issues/import",
        headers=auth_headers(account["token"]),
        json={"url": "https://github.com/example/project/issues/12"},
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Public issue title"
    assert response.json()["reference_url"].endswith("/issues/12")


def test_superclaw_chat_proxies_to_configured_openagents_agent(monkeypatch):
    main, client = load_test_client(monkeypatch)
    captured_payload = {}

    async def fake_call_openagents(payload):
        captured_payload.update(payload)
        return {
            "reply": "SuperClaw received: " + payload["message"],
            "agent": payload["agent"],
            "model": payload["model"],
        }

    monkeypatch.setattr(main, "call_openagents", fake_call_openagents)

    response = client.post(
        "/api/superclaw/chat",
        json={"message": "帮我拆解这个任务", "history": [{"role": "user", "content": "你好"}]},
    )

    assert response.status_code == 200
    assert response.json()["reply"] == "SuperClaw received: 帮我拆解这个任务"
    assert response.json()["agent"] == "superclaw"
    assert captured_payload["agent"] == "superclaw"
    assert captured_payload["model"] == "minimax/MiniMax-M2.5"
    assert captured_payload["history"][0]["content"] == "你好"


def test_superclaw_chat_uses_workspace_http_api(monkeypatch):
    main, client = load_test_client(monkeypatch)
    calls = []

    class FakeResponse:
        def __init__(self, data):
            self._data = data

        def raise_for_status(self):
            return None

        def json(self):
            return {"data": self._data}

    class FakeAsyncClient:
        def __init__(self, timeout):
            calls.append(("timeout", timeout))
            self.poll_count = 0

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def post(self, url, json, headers):
            calls.append(("post", url, json, headers))
            if json["type"] == "network.channel.create":
                return FakeResponse({"metadata": {"channel_name": "channel-test"}})
            return FakeResponse({"id": "message-1"})

        async def get(self, url, params=None, headers=None):
            calls.append(("get", url, params, headers))
            self.poll_count += 1
            if self.poll_count == 1:
                return FakeResponse(
                    {
                        "events": [
                            {
                                "source": "openagents:superclaw",
                                "payload": {"content": "thinking...", "message_type": "status"},
                            }
                        ]
                    }
                )
            return FakeResponse(
                {
                    "events": [
                        {
                            "source": "openagents:superclaw",
                            "payload": {"content": "workspace reply: 只回复 OK", "message_type": "chat"},
                        }
                    ]
                }
            )

    monkeypatch.setattr(main.httpx, "AsyncClient", FakeAsyncClient)

    response = client.post(
        "/api/superclaw/chat",
        json={"message": "只回复 OK"},
    )

    assert response.status_code == 200
    assert response.json()["reply"] == "workspace reply: 只回复 OK"
    assert response.json()["agent"] == "superclaw"
    create_call = calls[1]
    send_call = calls[2]
    assert create_call[0] == "post"
    assert create_call[1] == "https://workspace-endpoint.openagents.org/v1/events"
    assert create_call[2]["type"] == "network.channel.create"
    assert create_call[2]["network"] == "test-workspace"
    assert create_call[2]["payload"]["master"] == "superclaw"
    assert create_call[2]["payload"]["participants"] == ["superclaw"]
    assert create_call[3]["X-Workspace-Token"] == "test-workspace-token"
    assert send_call[2]["type"] == "workspace.message.posted"
    assert send_call[2]["target"] == "channel/channel-test"
    assert send_call[2]["payload"]["content"] == "只回复 OK"
    poll_call = calls[3]
    assert poll_call[0] == "get"
    assert poll_call[2]["network"] == "test-workspace"
    assert poll_call[2]["channel"] == "channel-test"
    assert poll_call[2]["after"] == "message-1"
    assert poll_call[3]["X-Workspace-Token"] == "test-workspace-token"
