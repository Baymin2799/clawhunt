export type TaskStatus =
  | "draft"
  | "open"
  | "assigned"
  | "in_progress"
  | "submitted"
  | "completed"
  | "cancelled"
  | "rejected";

export type MarketplaceTask = {
  id: string;
  owner_id: string;
  owner_name: string;
  source: "manual" | "github";
  github_issue_url?: string | null;
  delivery_method: "platform" | "github";
  routing_strategy: "leaderboard" | "direct" | "marketplace";
  target_agent?: string | null;
  delivery_standard_id?: string | null;
  template_id?: string | null;
  title: string;
  description: string;
  acceptance_criteria?: string | null;
  difficulty: "easy" | "medium" | "hard" | "expert";
  category: "ai" | "backend" | "frontend" | "data" | "devops" | "security" | "api" | "other";
  deadline?: string | null;
  reference_url?: string | null;
  review_mode: "self" | "ai";
  delivery_protocol: "l0" | "l1" | "l2" | "l3";
  budget?: number | null;
  knowledge_compensation: 0 | 25 | 50;
  status: TaskStatus;
  bid_count: number;
  created_at: string;
  updated_at: string;
};

export type ProblemTemplate = {
  slug: string;
  title: string;
  description: string;
  category: MarketplaceTask["category"];
  difficulty: MarketplaceTask["difficulty"];
  budget_min: number;
  budget_max: number;
  title_template: string;
  description_template: string;
};

export type DeliveryStandard = {
  slug: string;
  name: string;
  level: MarketplaceTask["delivery_protocol"];
  description: string;
  evidence_requirements: string[];
};

export type TaskFormValues = {
  source: MarketplaceTask["source"];
  github_issue_url: string;
  delivery_method: MarketplaceTask["delivery_method"];
  routing_strategy: MarketplaceTask["routing_strategy"];
  target_agent: string;
  delivery_standard_id: string;
  template_id: string;
  title: string;
  description: string;
  acceptance_criteria: string;
  difficulty: MarketplaceTask["difficulty"];
  category: MarketplaceTask["category"];
  deadline: string;
  reference_url: string;
  review_mode: MarketplaceTask["review_mode"];
  delivery_protocol: MarketplaceTask["delivery_protocol"];
  budget: string;
  knowledge_compensation: MarketplaceTask["knowledge_compensation"];
};

export const emptyTaskForm: TaskFormValues = {
  source: "manual",
  github_issue_url: "",
  delivery_method: "platform",
  routing_strategy: "leaderboard",
  target_agent: "",
  delivery_standard_id: "",
  template_id: "",
  title: "",
  description: "",
  acceptance_criteria: "",
  difficulty: "medium",
  category: "ai",
  deadline: "",
  reference_url: "",
  review_mode: "self",
  delivery_protocol: "l0",
  budget: "",
  knowledge_compensation: 0,
};

export function taskToForm(task: MarketplaceTask): TaskFormValues {
  return {
    source: task.source,
    github_issue_url: task.github_issue_url ?? "",
    delivery_method: task.delivery_method,
    routing_strategy: task.routing_strategy,
    target_agent: task.target_agent ?? "",
    delivery_standard_id: task.delivery_standard_id ?? "",
    template_id: task.template_id ?? "",
    title: task.title,
    description: task.description,
    acceptance_criteria: task.acceptance_criteria ?? "",
    difficulty: task.difficulty,
    category: task.category,
    deadline: task.deadline ?? "",
    reference_url: task.reference_url ?? "",
    review_mode: task.review_mode,
    delivery_protocol: task.delivery_protocol,
    budget: task.budget == null ? "" : String(task.budget),
    knowledge_compensation: task.knowledge_compensation,
  };
}

function authToken() {
  return localStorage.getItem("clawhunt_token");
}

export function currentUserId() {
  try {
    const raw = localStorage.getItem("clawhunt_user");
    return raw ? String(JSON.parse(raw).id ?? "") : "";
  } catch {
    return "";
  }
}

async function apiRequest<T>(url: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.body) headers.set("Content-Type", "application/json");
  const token = authToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(url, { ...options, headers });
  if (!response.ok) {
    let detail = `请求失败（${response.status}）`;
    try {
      const body = await response.json();
      if (typeof body.detail === "string") detail = body.detail;
      if (Array.isArray(body.detail) && body.detail[0]?.msg) detail = body.detail[0].msg;
    } catch {
      detail = response.statusText || detail;
    }
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}

export function fetchTasks(mine = false, query = "") {
  const endpoint = mine ? "/api/tasks/mine" : `/api/tasks${query ? `?${query}` : ""}`;
  return apiRequest<{ items: MarketplaceTask[]; total: number }>(endpoint);
}

export function fetchTask(taskId: string) {
  return apiRequest<MarketplaceTask>(`/api/tasks/${taskId}`);
}

export function fetchProblemTemplates() {
  return apiRequest<ProblemTemplate[]>("/api/problem-templates");
}

export function fetchDeliveryStandards() {
  return apiRequest<DeliveryStandard[]>("/api/delivery-standards");
}

function taskPayload(values: TaskFormValues) {
  return {
    ...values,
    github_issue_url: values.github_issue_url || null,
    target_agent: values.target_agent || null,
    delivery_standard_id: values.delivery_standard_id || null,
    template_id: values.template_id || null,
    acceptance_criteria: values.acceptance_criteria || null,
    deadline: values.deadline || null,
    reference_url: values.reference_url || null,
    budget: values.budget === "" ? null : Number(values.budget),
  };
}

export function saveTask(values: TaskFormValues, taskId?: string) {
  return apiRequest<MarketplaceTask>(taskId ? `/api/tasks/${taskId}` : "/api/tasks", {
    body: JSON.stringify(taskPayload(values)),
    method: taskId ? "PATCH" : "POST",
  });
}

export function cancelTask(taskId: string) {
  return apiRequest<MarketplaceTask>(`/api/tasks/${taskId}`, { method: "DELETE" });
}

export function importGitHubIssue(url: string) {
  return apiRequest<{ title: string; description: string; reference_url: string }>("/api/github/issues/import", {
    body: JSON.stringify({ url }),
    method: "POST",
  });
}
