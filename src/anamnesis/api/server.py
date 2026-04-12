"""Anamnesis REST API — thin FastAPI wrapper over KnowledgeFramework."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from anamnesis.config import KnowledgeConfig
from anamnesis.framework import KnowledgeFramework


# ─── Request/response models ────────────────────────────────────


class BolusCreate(BaseModel):
    id: str
    title: str | None = None
    summary: str = ""
    content: str = ""
    render: str = "reference"
    priority: int = 50
    tags: list[str] = []


class BolusUpdate(BaseModel):
    content: str
    summary: str | None = None


class HealthResponse(BaseModel):
    status: str
    version: str


class TurnCapture(BaseModel):
    role: str
    content: str


class SessionEnd(BaseModel):
    summary: str | None = None
    agent: str | None = None


class AgentCreate(BaseModel):
    name: str
    token_budget: int = 4000
    recency_budget: int = 400


class AgentUpdate(BaseModel):
    token_budget: int | None = None
    recency_budget: int | None = None


# ─── App factory ─────────────────────────────────────────────────


def create_app(config: KnowledgeConfig, config_path: str | None = None) -> FastAPI:
    """Create a FastAPI app wired to a KnowledgeFramework instance."""

    kf = KnowledgeFramework(config)
    _config_path = config_path  # Stored for agent API access

    app = FastAPI(
        title="Anamnesis Knowledge API",
        description="Knowledge management for LLM agent systems.",
        version="0.1.0",
    )

    # ─── CORS (for dashboard dev server) ────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5175", "http://localhost:4173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ─── Auth middleware ──────────────────────────────────────

    if config.api_key:
        @app.middleware("http")
        async def check_api_key(request: Request, call_next):
            # Skip auth for health and docs
            if request.url.path in ("/v1/health", "/docs", "/openapi.json", "/redoc"):
                return await call_next(request)

            auth = request.headers.get("Authorization", "")
            if auth != f"Bearer {config.api_key}":
                return Response(
                    content='{"detail":"Invalid or missing API key"}',
                    status_code=401,
                    media_type="application/json",
                )
            return await call_next(request)

    # ─── Health ───────────────────────────────────────────────

    @app.get("/v1/health", response_model=HealthResponse)
    async def health():
        return {"status": "ok", "version": "0.1.0"}

    # ─── Injection endpoints ──────────────────────────────────

    @app.get("/v1/knowledge/injection", response_class=PlainTextResponse)
    async def get_injection():
        try:
            text = kf.get_injection()
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        return Response(content=text, media_type="text/markdown")

    @app.get("/v1/knowledge/injection/metrics")
    async def get_injection_metrics():
        try:
            return kf.get_injection_metrics()
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))

    # ─── Bolus CRUD ───────────────────────────────────────────

    @app.get("/v1/knowledge/boluses")
    async def list_boluses(active_only: bool = True):
        return kf.list_boluses(active_only=active_only)

    @app.get("/v1/knowledge/boluses/{bolus_id}")
    async def get_bolus(bolus_id: str):
        try:
            metadata, content = kf.store.read_full(bolus_id)
        except KeyError:
            raise HTTPException(status_code=404, detail=f"Bolus '{bolus_id}' not found")
        return {"id": bolus_id, "metadata": metadata, "content": content}

    @app.post("/v1/knowledge/boluses", status_code=201)
    async def create_bolus(body: BolusCreate):
        try:
            kf.create_bolus(
                body.id,
                body.content,
                title=body.title,
                summary=body.summary,
                render=body.render,
                priority=body.priority,
                tags=body.tags,
            )
        except ValueError as e:
            if "already exists" in str(e):
                raise HTTPException(status_code=409, detail=str(e))
            raise HTTPException(status_code=422, detail=str(e))
        return {"id": body.id, "status": "created"}

    @app.put("/v1/knowledge/boluses/{bolus_id}")
    async def update_bolus(bolus_id: str, body: BolusUpdate):
        try:
            kf.update_bolus(bolus_id, body.content)
        except KeyError:
            raise HTTPException(status_code=404, detail=f"Bolus '{bolus_id}' not found")
        return {"id": bolus_id, "status": "updated"}

    @app.delete("/v1/knowledge/boluses/{bolus_id}")
    async def delete_bolus(bolus_id: str):
        deleted = kf.delete_bolus(bolus_id)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Bolus '{bolus_id}' not found")
        return {"id": bolus_id, "status": "deleted"}

    @app.patch("/v1/knowledge/boluses/{bolus_id}/activate")
    async def activate_bolus(bolus_id: str):
        try:
            kf.set_bolus_active(bolus_id, True)
        except KeyError:
            raise HTTPException(status_code=404, detail=f"Bolus '{bolus_id}' not found")
        return {"id": bolus_id, "active": True}

    @app.patch("/v1/knowledge/boluses/{bolus_id}/deactivate")
    async def deactivate_bolus(bolus_id: str):
        try:
            kf.set_bolus_active(bolus_id, False)
        except KeyError:
            raise HTTPException(status_code=404, detail=f"Bolus '{bolus_id}' not found")
        return {"id": bolus_id, "active": False}

    # ─── Retrieve knowledge (tool endpoint) ───────────────────

    @app.get("/v1/knowledge/retrieve/{bolus_id}", response_class=PlainTextResponse)
    async def retrieve_knowledge(bolus_id: str):
        """The retrieve_knowledge tool endpoint. Returns bolus content as plain text."""
        try:
            content = kf.retrieve(bolus_id)
        except KeyError:
            raise HTTPException(status_code=404, detail=f"Bolus '{bolus_id}' not found")
        return Response(content=content, media_type="text/markdown")

    # ─── Episode capture (Circle 4) ─────────────────────────────

    @app.post("/v1/episodes/turn")
    async def capture_turn(body: TurnCapture):
        kf.capture_turn(body.role, body.content)
        return {"status": "captured"}

    @app.post("/v1/episodes/end")
    async def end_session(body: SessionEnd | None = None):
        summary = body.summary if body else None
        agent = body.agent if body else None
        session_id = kf.end_session(summary=summary, agent=agent)
        if session_id is None:
            return {"status": "no_session", "session_id": None}
        return {"status": "ended", "session_id": session_id}

    @app.get("/v1/episodes")
    async def list_episodes(agent: str | None = None):
        return kf.list_episodes(agent=agent)

    @app.get("/v1/episodes/{session_id}")
    async def get_episode(session_id: str):
        try:
            episode = kf.get_episode(session_id)
        except KeyError:
            raise HTTPException(status_code=404, detail=f"Episode '{session_id}' not found")
        return {
            "session_id": episode.session_id,
            "agent": episode.agent,
            "started": episode.started,
            "ended": episode.ended,
            "summary": episode.summary,
            "turn_count": episode.turn_count,
            "compiled": episode.compiled,
            "turns": [
                {"role": t.role, "content": t.content, "timestamp": t.timestamp, "sequence": t.sequence}
                for t in episode.turns
            ],
        }

    # ─── Agent registry ─────────────────────────────────────────

    # ─── Agent registry helpers ─────────────────────────────────

    from pathlib import Path as _Path
    from anamnesis.init import load_project_config, save_project_config

    _resolved_config_path = _Path(_config_path) if _config_path else None
    if _resolved_config_path is None:
        for _name in ["anamnesis.yaml", "anamnesis.yml"]:
            _p = _Path(_name)
            if _p.exists():
                _resolved_config_path = _p
                break

    def _load_agents() -> tuple[_Path, dict, dict]:
        """Load config and return (config_path, project, agents). Raises HTTPException."""
        if _resolved_config_path is None:
            raise HTTPException(status_code=422, detail="No config file found")
        project = load_project_config(_resolved_config_path)
        return _resolved_config_path, project, project.get("agents", {})

    @app.get("/v1/agents")
    async def list_agents():
        if _resolved_config_path is None:
            return {}
        project = load_project_config(_resolved_config_path)
        return project.get("agents", {})

    @app.get("/v1/agents/{name}")
    async def get_agent(name: str):
        _, _, agents = _load_agents()
        if name not in agents:
            raise HTTPException(status_code=404, detail=f"Agent '{name}' not found")
        return {"name": name, **agents[name]}

    @app.post("/v1/agents", status_code=201)
    async def create_agent(body: AgentCreate):
        cp, project, agents = _load_agents()
        if body.name in agents:
            raise HTTPException(status_code=409, detail=f"Agent '{body.name}' already exists")
        agents[body.name] = {
            "token_budget": body.token_budget,
            "recency_budget": body.recency_budget,
        }
        project.setdefault("agents", agents)
        save_project_config(cp, project)
        return {"name": body.name, "status": "created"}

    @app.patch("/v1/agents/{name}")
    async def update_agent(name: str, body: AgentUpdate):
        cp, project, agents = _load_agents()
        if name not in agents:
            raise HTTPException(status_code=404, detail=f"Agent '{name}' not found")
        if body.token_budget is not None:
            agents[name]["token_budget"] = body.token_budget
        if body.recency_budget is not None:
            agents[name]["recency_budget"] = body.recency_budget
        save_project_config(cp, project)
        return {"name": name, **agents[name]}

    @app.delete("/v1/agents/{name}")
    async def delete_agent(name: str):
        cp, project, agents = _load_agents()
        if name not in agents:
            raise HTTPException(status_code=404, detail=f"Agent '{name}' not found")
        del agents[name]
        save_project_config(cp, project)
        return {"name": name, "status": "deleted"}

    return app
