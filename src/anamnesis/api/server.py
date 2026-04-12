"""Anamnesis REST API — thin FastAPI wrapper over KnowledgeFramework."""

from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, Request, Response
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


# ─── App factory ─────────────────────────────────────────────────


def create_app(config: KnowledgeConfig) -> FastAPI:
    """Create a FastAPI app wired to a KnowledgeFramework instance."""

    kf = KnowledgeFramework(config)

    app = FastAPI(
        title="Anamnesis Knowledge API",
        description="Knowledge management for LLM agent systems.",
        version="0.1.0",
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
            content = kf.read_bolus(bolus_id)
            metadata = kf.get_bolus_metadata(bolus_id)
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

    return app
