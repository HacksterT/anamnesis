<script lang="ts">
	import { onMount } from 'svelte';
	import {
		listAgents,
		createAgent,
		updateAgent,
		deleteAgent,
		getHealth,
		type AgentConfig
	} from '$lib/api';

	let agents = $state<Record<string, AgentConfig>>({});
	let connected = $state(false);
	let loading = $state(true);
	let error = $state('');
	let version = $state('');

	// Create form
	let showCreate = $state(false);
	let newName = $state('');
	let newTokenBudget = $state(4000);
	let newRecencyBudget = $state(400);

	// Debounce timers for slider saves
	let debounceTimers: Record<string, ReturnType<typeof setTimeout>> = {};

	async function load() {
		loading = true;
		error = '';
		try {
			const health = await getHealth();
			connected = true;
			version = health.version;
			agents = await listAgents();
		} catch {
			connected = false;
			error = 'Cannot reach Anamnesis API. Start the server with anamnesis serve.';
		}
		loading = false;
	}

	onMount(load);

	async function handleCreate() {
		try {
			await createAgent(newName, {
				token_budget: newTokenBudget,
				recency_budget: newRecencyBudget
			});
			showCreate = false;
			newName = '';
			newTokenBudget = 4000;
			newRecencyBudget = 400;
			await load();
		} catch (e: any) {
			error = e.message;
		}
	}

	async function handleDelete(name: string) {
		await deleteAgent(name);
		await load();
	}

	function handleRecencyChange(name: string, value: number) {
		// Update local state immediately for responsive UI
		if (agents[name]) {
			agents[name].recency_budget = value;
		}
		// Debounce the API call
		if (debounceTimers[name]) clearTimeout(debounceTimers[name]);
		debounceTimers[name] = setTimeout(async () => {
			await updateAgent(name, { recency_budget: value });
		}, 500);
	}

	let agentEntries = $derived(Object.entries(agents));
</script>

<div class="page-header">
	<h2>Agent Registry</h2>
	<div class="header-right">
		<div class="status-dot" class:online={connected}>
			{connected ? `API v${version}` : 'API Offline'}
		</div>
		<button class="btn-primary" onclick={() => (showCreate = !showCreate)}>
			{showCreate ? 'Cancel' : '+ New Agent'}
		</button>
	</div>
</div>

{#if error}
	<div class="error-banner">{error}</div>
{/if}

{#if showCreate}
	<div class="create-form">
		<div class="form-row">
			<input bind:value={newName} placeholder="Agent name (e.g. atlas)" />
			<label>
				Token Budget
				<input type="number" bind:value={newTokenBudget} min="500" max="6000" style="width:100px" />
			</label>
			<label>
				Recency Budget
				<input type="number" bind:value={newRecencyBudget} min="0" max="1000" style="width:100px" />
			</label>
			<button class="btn-primary" onclick={handleCreate}>Register</button>
		</div>
	</div>
{/if}

{#if loading}
	<p class="muted">Connecting...</p>
{:else if agentEntries.length === 0}
	<div class="empty-state">
		<p>No agents registered.</p>
		<p class="muted">Register an agent with the button above or via CLI: <code>anamnesis init --agent &lt;name&gt;</code></p>
	</div>
{:else}
	<div class="agent-list">
		{#each agentEntries as [name, cfg] (name)}
			{@const recencyPct = cfg.token_budget > 0 ? (cfg.recency_budget / cfg.token_budget) * 100 : 0}
			{@const curatedPct = 100 - recencyPct}
			<div class="agent-card">
				<div class="card-header">
					<h3>{name}</h3>
					<button class="btn-danger-sm" onclick={() => handleDelete(name)}>Remove</button>
				</div>

				<div class="budget-section">
					<div class="budget-label">
						<span>Token Budget: <strong>{cfg.token_budget}</strong></span>
					</div>

					<div class="allocation-bar">
						<div class="alloc-curated" style="width: {curatedPct}%">
							<span>{Math.round(cfg.token_budget - cfg.recency_budget)} curated</span>
						</div>
						{#if cfg.recency_budget > 0}
							<div class="alloc-recency" style="width: {recencyPct}%">
								<span>{cfg.recency_budget} recency</span>
							</div>
						{/if}
					</div>
				</div>

				<div class="slider-section">
					<div class="slider-label">
						Recency Budget: <strong>{cfg.recency_budget}</strong> tokens
					</div>
					<input
						type="range"
						min="0"
						max="1000"
						step="50"
						value={cfg.recency_budget}
						oninput={(e) => handleRecencyChange(name, parseInt(e.currentTarget.value))}
					/>
					<div class="slider-range">
						<span>0 (disabled)</span>
						<span>1000</span>
					</div>
				</div>
			</div>
		{/each}
	</div>
{/if}

<style>
	.page-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 24px;
	}

	h2 {
		font-size: 1.4rem;
		font-weight: 600;
	}

	h3 {
		font-size: 1.1rem;
		font-weight: 600;
	}

	.header-right {
		display: flex;
		gap: 16px;
		align-items: center;
	}

	.status-dot {
		font-size: 0.8rem;
		color: var(--danger);
		display: flex;
		align-items: center;
		gap: 8px;
	}

	.status-dot::before {
		content: '';
		width: 8px;
		height: 8px;
		border-radius: 50%;
		background: var(--danger);
	}

	.status-dot.online {
		color: var(--success);
	}

	.status-dot.online::before {
		background: var(--success);
	}

	.error-banner {
		background: rgba(248, 113, 113, 0.1);
		border: 1px solid var(--danger);
		color: var(--danger);
		padding: 12px 16px;
		border-radius: var(--radius);
		margin-bottom: 16px;
		font-size: 0.9rem;
	}

	.create-form {
		background: var(--bg-surface);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		padding: 20px;
		margin-bottom: 24px;
	}

	.form-row {
		display: flex;
		gap: 12px;
		align-items: center;
	}

	input {
		background: var(--bg);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		color: var(--text);
		padding: 8px 12px;
		font-size: 0.9rem;
		flex: 1;
	}

	label {
		font-size: 0.85rem;
		color: var(--text-muted);
		display: flex;
		align-items: center;
		gap: 8px;
		flex-shrink: 0;
	}

	.muted {
		color: var(--text-muted);
		font-size: 0.9rem;
	}

	.empty-state {
		text-align: center;
		padding: 60px 20px;
	}

	code {
		background: var(--bg-surface);
		padding: 2px 6px;
		border-radius: 4px;
		font-size: 0.85rem;
	}

	.agent-list {
		display: flex;
		flex-direction: column;
		gap: 16px;
	}

	.agent-card {
		background: var(--bg-surface);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		padding: 20px;
	}

	.card-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 20px;
	}

	.budget-section {
		margin-bottom: 20px;
	}

	.budget-label {
		font-size: 0.9rem;
		margin-bottom: 8px;
	}

	.allocation-bar {
		display: flex;
		height: 28px;
		border-radius: 6px;
		overflow: hidden;
		background: var(--bg);
	}

	.alloc-curated {
		background: var(--success);
		display: flex;
		align-items: center;
		justify-content: center;
		min-width: 0;
		transition: width 0.2s ease;
	}

	.alloc-curated span {
		font-size: 0.7rem;
		color: #000;
		font-weight: 600;
		white-space: nowrap;
		overflow: hidden;
	}

	.alloc-recency {
		background: var(--accent);
		display: flex;
		align-items: center;
		justify-content: center;
		min-width: 0;
		transition: width 0.2s ease;
	}

	.alloc-recency span {
		font-size: 0.7rem;
		color: #fff;
		font-weight: 600;
		white-space: nowrap;
		overflow: hidden;
	}

	.slider-section {
		padding-top: 4px;
	}

	.slider-label {
		display: block;
		margin-bottom: 8px;
		font-size: 0.9rem;
		color: var(--text);
	}

	input[type='range'] {
		width: 100%;
		accent-color: var(--accent);
		flex: 1;
		padding: 0;
		border: none;
		background: transparent;
	}

	.slider-range {
		display: flex;
		justify-content: space-between;
		font-size: 0.7rem;
		color: var(--text-muted);
		margin-top: 4px;
	}

	.btn-primary {
		background: var(--accent);
		color: white;
		border: none;
		padding: 8px 16px;
		border-radius: var(--radius);
		font-size: 0.85rem;
		font-weight: 500;
		flex-shrink: 0;
	}

	.btn-primary:hover {
		background: var(--accent-hover);
	}

	.btn-danger-sm {
		background: none;
		border: 1px solid var(--danger);
		color: var(--danger);
		padding: 4px 10px;
		border-radius: var(--radius);
		font-size: 0.75rem;
	}

	.btn-danger-sm:hover {
		background: rgba(248, 113, 113, 0.1);
	}
</style>
