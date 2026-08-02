# Animus Studio — Architecture v1

**Status: FROZEN**
Date locked: 2026-08-01

> No architectural changes unless they solve a real problem discovered during implementation or testing.
> New ideas go to `ARCHITECTURE_v2.md`.

---

## One Sentence

Animus Studio is an operating environment for building, testing, evaluating, and deploying autonomous AI workflows.
The first workflow is the AnimusLab Marketing Pipeline.

---

## The Stack

```
Frontend (React/Vite)
    ?
API Layer (FastAPI)
    ?
Studio Runtime          ? the kernel
    ?
Workers                 ? stateless execution units
    ?
Infrastructure (Postgres + pgvector, Redis)
```

---

## Studio Runtime

The kernel. Every capability in Studio routes through it.

```
runtime/
+-- registry.py         — Runtime (the kernel object itself)
+-- capabilities.py     — CapabilityRegistry
+-- providers.py        — ProviderRegistry (AI providers only)
+-- credentials.py      — CredentialManager
+-- eventbus.py         — EventBus (event-sourced)
+-- context.py          — RuntimeContext, MissionSpec, ExecutionContext
+-- scheduler.py        — MissionScheduler (stub in v1)
+-- manifest.py         — MissionManifest
+-- doctor.py           — animus doctor CLI
```

### Runtime Object

The root object. One instance per process.

```python
class Runtime:
    capabilities:  CapabilityRegistry
    providers:     ProviderRegistry
    credentials:   CredentialManager
    events:        EventBus
    memory:        MemoryEngine
    scheduler:     MissionScheduler
    config:        Settings
```

Workers never import providers directly. They call `runtime.capabilities.resolve(Capability.X)`.

---

## Capability Vocabulary

Capabilities describe what is needed, never how to obtain it.

```python
class Capability(str, Enum):
    # Language
    TEXT_GENERATION      = "text_generation"
    TEXT_REASONING       = "text_reasoning"
    VISION_UNDERSTANDING = "vision_understanding"
    TEXT_EMBEDDING       = "text_embedding"

    # Audio
    VOICE_SYNTHESIS      = "voice_synthesis"
    VOICE_TRANSCRIPTION  = "voice_transcription"

    # Web
    WEB_SEARCH           = "web_search"
    WEB_SCRAPING         = "web_scraping"
    BROWSER              = "browser"

    # Media
    IMAGE_GENERATION     = "image_generation"
    VIDEO_ASSEMBLY       = "video_assembly"

    # Compute
    CODE                 = "code"
    TERMINAL             = "terminal"

    # Studio
    PUBLISH              = "publish"
    MEMORY               = "memory"
    ANALYTICS            = "analytics"
```

### CapabilityRegistry vs ProviderRegistry

**CapabilityRegistry** resolves any capability to its implementation.
This includes AI providers, but also Docker, ffmpeg, Playwright, shell, git.

**ProviderRegistry** manages AI model providers only (Ollama, OpenAI, Groq, etc.)
Owned by CapabilityRegistry. Not called directly by workers.

```
Worker
    ?
runtime.capabilities.resolve(Capability.TEXT_REASONING)
    ?
CapabilityRegistry
    ?  (for AI capabilities, delegates to)
ProviderRegistry
    ?
OllamaProvider
```

---

## Context Layers

Three layers. Clear separation of responsibility.

### RuntimeContext
Stable. Never changes across the Studio session.
```python
@dataclass(frozen=True)
class RuntimeContext:
    runtime:  Runtime
    logger:   BoundLogger
    config:   Settings
```

### MissionSpec
Immutable. Set once per mission. The specification.
```python
@dataclass(frozen=True)
class MissionSpec:
    mission_id:  str
    goal:        str
    brand:       Brand
    audience:    str
    language:    str
    tone:        str
    deadline:    datetime | None
```

### ExecutionContext
Mutable. One per workflow execution.
```python
@dataclass
class ExecutionContext:
    execution_id:  str
    step:          str
    retry_count:   int
    artifacts:     dict
    events:        EventBus
    cancellation:  asyncio.Event

    def get(self, key: str) -> Any: ...
    def set(self, key: str, value: Any) -> None: ...
    def emit(self, event_type: str, payload: dict) -> None: ...
```

Workers receive all three. Workers only write to `ExecutionContext.artifacts`.

---

## Workers

Workers are stateless execution units. They are not intelligent agents.

### Rules
1. **Never store state on `self`**
2. **Read only from `exec.artifacts`**
3. **Write only to `exec.artifacts`**
4. **Declare what you need** — `requires`
5. **Declare what you produce** — `produces`

### Declaration
```python
class ScriptWorker(BaseWorker):
    name     = "script"
    requires = {Capability.TEXT_REASONING}
    produces = {"script", "title", "description", "tags"}

    async def _run(
        self,
        rt:   RuntimeContext,
        spec: MissionSpec,
        exec: ExecutionContext,
    ) -> dict:
        research = exec.get("research")   # read from artifacts
        ...
        return {"script": ..., "title": ..., "description": ..., "tags": ...}
```

### Testing consequence
```python
result = await ScriptWorker().run(rt, spec, exec)
assert "script" in result
# No mocks, no database, no network needed
```

---

## Mission Graph (DAG)

Missions are declared as graphs, even when v1 executes them linearly.

```python
DAILY_CONTENT_GRAPH = MissionGraph(
    nodes=[
        "research", "script", "voice",
        "thumbnail", "editor", "publisher", "analytics",
    ],
    edges=[
        ("research",   "script"),
        ("script",     "voice"),
        ("script",     "thumbnail"),  # parallel in v2
        ("voice",      "editor"),
        ("thumbnail",  "editor"),
        ("editor",     "publisher"),
        ("publisher",  "analytics"),
    ],
    human_gates=["script"],
)
```

v1: topological order (linear).
v2: independent branches run in parallel.

Declaring as a graph now means parallelism is additive, not a rewrite.

---

## EventBus

All mission events are persisted. Nothing fire-and-forget.

```
mission_events table:
    id           UUID PK
    mission_id   UUID (indexed)
    execution_id UUID
    event_type   str    "step.started" | "step.completed" | "step.failed"
    step         str
    worker       str
    payload      JSONB
    emitted_at   DateTime
```

Enables: real-time WebSocket timeline, full replay, analytics queries, debugging.

---

## CredentialManager

One place for all credentials. Workers never call os.getenv() for secrets.

```python
class CredentialManager:
    def get(self, service: str) -> Credential | None
    async def store(self, service: str, cred: Credential) -> None
    async def refresh(self, service: str) -> Credential
    def is_configured(self, service: str) -> bool
```

Credential types: APIKeyCredential, OAuthCredential
v1 backends: .env (API keys) + Postgres encrypted (OAuth tokens)

---

## Mission Manifest

Every mission produces a manifest. Immutable after completion.

```json
{
  "id": "m_01j8x...",
  "goal": "AI governance video",
  "started_at": "2026-08-01T10:00:00Z",
  "completed_at": "2026-08-01T10:05:12Z",
  "duration_s": 312,
  "workers": ["research", "script", "voice", "editor", "publisher"],
  "outputs": {
    "script": "outputs/m_01j8x/script.md",
    "audio": "outputs/m_01j8x/voice.mp3",
    "video": "outputs/m_01j8x/video.mp4",
    "thumbnail": "outputs/m_01j8x/thumbnail.jpg"
  },
  "providers": {
    "TEXT_REASONING": "ollama/deepseek-r1:8b",
    "VOICE_SYNTHESIS": "kokoro/af_heart",
    "IMAGE_GENERATION": "pillow/template"
  },
  "cost_usd": 0.00,
  "status": "completed"
}
```

---

## animus doctor CLI

```bash
python -m runtime.doctor        # full health check
python -m runtime.doctor models # model status only
python -m runtime.doctor caps   # capability matrix only
```

Output style: Homebrew-style. Green checkmarks, yellow warnings, red errors, install suggestions.

---

## What is NOT in v1

- Multi-user / teams
- Billing / marketplace
- Mobile app
- Parallel branch execution (graph declared, execution linear)
- Vault / secrets manager
- ComfyUI
- Agent orchestrating other agents
- Kubernetes

---

## The Rule

> Any capability added before October 1 must route through the Runtime.
> If it calls a provider directly, it does not merge.

Everything else belongs in ARCHITECTURE_v2.md.
