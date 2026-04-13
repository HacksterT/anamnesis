/**
 * Anamnesis API client.
 * All dashboard reads/writes go through these functions.
 */

const BASE = 'http://localhost:8741';

async function request(path: string, options: RequestInit = {}): Promise<Response> {
	const res = await fetch(`${BASE}${path}`, {
		...options,
		headers: {
			'Content-Type': 'application/json',
			...options.headers
		}
	});
	return res;
}

// ─── Types ──────────────────────────────────────────────────────

export interface BolusMetadata {
	id: string;
	title: string;
	active: boolean;
	render: 'inline' | 'reference';
	priority: number;
	summary: string;
	tags: string[];
	created: string;
	updated: string;
}

export interface BolusDetail {
	id: string;
	metadata: BolusMetadata;
	content: string;
}

export interface InjectionMetrics {
	total_tokens: number;
	soft_max: number;
	hard_ceiling: number;
	utilization_pct: number;
	status: 'ok' | 'warning' | 'exceeded';
	active_boluses: number;
	total_boluses: number;
}

export interface AgentConfig {
	token_budget: number;
	recency_budget: number;
	knowledge_dir?: string;
}

export interface CurationItem {
	id: number;
	fact: string;
	source_episode: string | null;
	source_agent: string | null;
	source_url: string | null;
	suggested_bolus: string | null;
	confidence: number;
	status: 'pending' | 'confirmed' | 'rejected' | 'deferred';
	created: string;
}

// ─── Injection ──────────────────────────────────────────────────

export async function getInjection(): Promise<string> {
	const res = await request('/v1/knowledge/injection');
	return res.text();
}

export async function getInjectionMetrics(): Promise<InjectionMetrics> {
	const res = await request('/v1/knowledge/injection/metrics');
	return res.json();
}

// ─── Boluses ────────────────────────────────────────────────────

export async function listBoluses(activeOnly = true): Promise<BolusMetadata[]> {
	const res = await request(`/v1/knowledge/boluses?active_only=${activeOnly}`);
	return res.json();
}

export async function getBolus(id: string): Promise<BolusDetail> {
	const res = await request(`/v1/knowledge/boluses/${id}`);
	if (!res.ok) throw new Error(`Bolus '${id}' not found`);
	return res.json();
}

export async function createBolus(data: {
	id: string;
	title?: string;
	summary?: string;
	content?: string;
	render?: 'inline' | 'reference';
	priority?: number;
	tags?: string[];
}): Promise<void> {
	const res = await request('/v1/knowledge/boluses', {
		method: 'POST',
		body: JSON.stringify(data)
	});
	if (!res.ok) {
		const err = await res.json();
		throw new Error(err.detail || 'Failed to create bolus');
	}
}

export async function updateBolus(id: string, content: string): Promise<void> {
	const res = await request(`/v1/knowledge/boluses/${id}`, {
		method: 'PUT',
		body: JSON.stringify({ content })
	});
	if (!res.ok) throw new Error(`Failed to update bolus '${id}'`);
}

export async function upsertBolus(
	id: string,
	data: { content: string; title?: string; summary?: string; render?: string; priority?: number; tags?: string[] }
): Promise<'created' | 'updated'> {
	const res = await request(`/v1/knowledge/boluses/${id}`, {
		method: 'PUT',
		body: JSON.stringify(data)
	});
	if (!res.ok) {
		const err = await res.json();
		throw new Error(err.detail || `Failed to upsert bolus '${id}'`);
	}
	const body = await res.json();
	return body.status;
}

export async function appendBolus(
	id: string,
	content: string,
	separator = '\n\n---\n\n'
): Promise<void> {
	const res = await request(`/v1/knowledge/boluses/${id}/append`, {
		method: 'POST',
		body: JSON.stringify({ content, separator })
	});
	if (!res.ok) {
		const err = await res.json();
		throw new Error(err.detail || `Failed to append to bolus '${id}'`);
	}
}

export async function deleteBolus(id: string): Promise<void> {
	const res = await request(`/v1/knowledge/boluses/${id}`, { method: 'DELETE' });
	if (!res.ok) throw new Error(`Failed to delete bolus '${id}'`);
}

export async function activateBolus(id: string): Promise<void> {
	await request(`/v1/knowledge/boluses/${id}/activate`, { method: 'PATCH' });
}

export async function deactivateBolus(id: string): Promise<void> {
	await request(`/v1/knowledge/boluses/${id}/deactivate`, { method: 'PATCH' });
}

// ─── Curation queue ─────────────────────────────────────────────

export async function getCurationQueue(limit = 50): Promise<CurationItem[]> {
	const res = await request(`/v1/curation?limit=${limit}`);
	if (!res.ok) throw new Error('Failed to load curation queue');
	return res.json();
}

export async function stageFact(data: {
	fact: string;
	suggested_bolus?: string;
	confidence?: number;
	agent?: string;
	source_url?: string;
}): Promise<number> {
	const res = await request('/v1/curation', {
		method: 'POST',
		body: JSON.stringify(data)
	});
	if (!res.ok) {
		const err = await res.json();
		throw new Error(err.detail || 'Failed to stage fact');
	}
	const body = await res.json();
	return body.id;
}

export async function confirmItem(id: number, bolusId: string): Promise<void> {
	const res = await request(`/v1/curation/${id}/confirm`, {
		method: 'POST',
		body: JSON.stringify({ bolus_id: bolusId })
	});
	if (!res.ok) throw new Error(`Failed to confirm item ${id}`);
}

export async function rejectItem(id: number): Promise<void> {
	const res = await request(`/v1/curation/${id}/reject`, { method: 'POST' });
	if (!res.ok) throw new Error(`Failed to reject item ${id}`);
}

export async function deferItem(id: number): Promise<void> {
	const res = await request(`/v1/curation/${id}/defer`, { method: 'POST' });
	if (!res.ok) throw new Error(`Failed to defer item ${id}`);
}

// ─── Health ─────────────────────────────────────────────────────

export async function getHealth(): Promise<{ status: string; version: string }> {
	const res = await request('/v1/health');
	return res.json();
}

// ─── Agents ─────────────────────────────────────────────────────

export async function listAgents(): Promise<Record<string, AgentConfig>> {
	const res = await request('/v1/agents');
	return res.json();
}

export async function getAgent(name: string): Promise<AgentConfig & { name: string }> {
	const res = await request(`/v1/agents/${name}`);
	if (!res.ok) throw new Error(`Agent '${name}' not found`);
	return res.json();
}

export async function createAgent(
	name: string,
	config: { token_budget?: number; recency_budget?: number }
): Promise<void> {
	const res = await request('/v1/agents', {
		method: 'POST',
		body: JSON.stringify({ name, ...config })
	});
	if (!res.ok) {
		const err = await res.json();
		throw new Error(err.detail || 'Failed to create agent');
	}
}

export async function updateAgent(
	name: string,
	updates: Partial<AgentConfig>
): Promise<void> {
	const res = await request(`/v1/agents/${name}`, {
		method: 'PATCH',
		body: JSON.stringify(updates)
	});
	if (!res.ok) throw new Error(`Failed to update agent '${name}'`);
}

export async function deleteAgent(name: string): Promise<void> {
	const res = await request(`/v1/agents/${name}`, { method: 'DELETE' });
	if (!res.ok) throw new Error(`Failed to delete agent '${name}'`);
}
