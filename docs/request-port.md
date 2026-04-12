# Port Assignment Request — Anamnesis

**Project:** Anamnesis
**Requested by:** Anamnesis development
**Date:** 2026-04-12
**Status:** Pending Atlas coordination

---

## Ports Needed

### 1. Anamnesis REST API Server

- **Assigned port:** 8741
- **Protocol:** HTTP
- **Purpose:** Primary REST API for knowledge management. All bolus CRUD, injection assembly, retrieve_knowledge tool, and metrics endpoints. Consumed by agents (Atlas, Selah), the CLI, and the web dashboard.
- **Binding:** `127.0.0.1` (local only by default, configurable)
- **When running:** Whenever `anamnesis serve` is active or the API is deployed
- **Configured in:** `anamnesis.yaml` → `api_port`, `KnowledgeConfig.api_port`, CLI `--port` flag

### 2. Dashboard Dev Server (Development Only)

- **Assigned port:** 5175 (changed from 5173 — conflict with epic-writer-assistant)
- **Protocol:** HTTP
- **Purpose:** SvelteKit development server with hot module replacement. Only runs during dashboard development (`npm run dev` in `/dashboard`).
- **Binding:** `localhost`
- **When running:** Development only — not needed in production
- **Note:** This is the Vite default. The production dashboard can be built as static files and served from the API server or any web server, eliminating this port.

### 3. Dashboard Preview Server (Development Only)

- **Assigned port:** 4173
- **Protocol:** HTTP
- **Purpose:** SvelteKit production preview (`npm run preview`). Used to test the production build locally before deployment.
- **Binding:** `localhost`
- **When running:** Development testing only
- **Note:** Also a Vite default. Not needed in production.

---

## Production Deployment

In production, only **one port** is needed — the API server. The dashboard can be:
- Built to static files (`npm run build`) and served by FastAPI at `/dashboard`
- Deployed behind a reverse proxy alongside the API
- Hosted separately (Vercel, Cloudflare Pages, etc.) pointing to the API

---

## Conflict Check

Known ports in use by other projects (verify with Atlas):

| Port | Project | Service |
|------|---------|---------|
| 3000 | the-agency | Next.js frontend |
| 5432 | the-agency | PostgreSQL |
| 8000 | ? | Common Python dev server |
| 8080 | ? | Common dev server |
| 8741 | Anamnesis (provisional) | REST API |

---

## Notes

- The API port (8741) was chosen to avoid common dev server conflicts. Open to reassignment.
- The dashboard dev ports (5173, 4173) are Vite defaults and can be changed in `dashboard/vite.config.ts` if they conflict.
- All provisional — pending final assignment from Atlas.

---

## Atlas CTO Port Assignment Response

**Reviewed by:** Atlas CTO (on behalf of HacksterT)
**Date:** 2026-04-12
**Status:** APPROVED with one required change

### Conflict Analysis

Full port audit against the Mac Mini M4 Pro infrastructure registry:

| Requested Port | Conflict? | Details |
|---------------|-----------|---------|
| **8741** (API) | No conflict | Port is clear across all machines. Approved as-is. |
| **5173** (Dashboard dev) | **CONFLICT** | Already assigned to `epic-writer-assistant` Vite Frontend on Windows dev machine. While these are different machines, we maintain unique port assignments across the fleet to avoid confusion and enable future cross-machine development. |
| **4173** (Preview) | No conflict | Port is clear. Approved as-is. |

### Assignments

| Port | Service | Status | Notes |
|------|---------|--------|-------|
| **8741** | Anamnesis REST API | **ASSIGNED** | Production + dev. Binding 127.0.0.1 confirmed. Will be added to infrastructure registry. |
| **5175** | Dashboard Dev Server | **ASSIGNED (changed from 5173)** | 5173 is taken by epic-writer-assistant, 5174 is taken by Selah frontend. Use 5175. Update `dashboard/vite.config.ts` accordingly. |
| **4173** | Dashboard Preview | **ASSIGNED** | Dev-only. Vite default is fine here, no conflicts. |

### Required Action

Update `dashboard/vite.config.ts` to set the dev server port to **5175** instead of the Vite default 5173:

```typescript
export default defineConfig({
  server: {
    port: 5175
  },
  preview: {
    port: 4173
  }
})
```

### Infrastructure Registry Update

Atlas will add these to the canonical infrastructure registry at `LAN-Central-Command/sysadmin-infrastructure/registry.json` under the `mac-mini` machine entry. Anamnesis is now a registered project in the fleet.

### Full Mac Mini Port Map (for your reference)

Ports currently assigned on this machine: 80, 3000, 3100, 3200, 3201, 3333, 3847, 5432, 5433, 7474, 7687, 8000, 8001, 8002, 8888, 9000. Your assignments (8741, 5175, 4173) are all clear.
