<script lang="ts">
	import { onMount } from 'svelte';
	import {
		listBoluses,
		activateBolus,
		deactivateBolus,
		deleteBolus,
		createBolus,
		type BolusMetadata
	} from '$lib/api';

	let boluses = $state<BolusMetadata[]>([]);
	let showAll = $state(false);
	let filterTag = $state('');
	let filterRender = $state('');
	let loading = $state(true);
	let error = $state('');

	// Create form
	let showCreate = $state(false);
	let newId = $state('');
	let newTitle = $state('');
	let newSummary = $state('');
	let newRender = $state<'inline' | 'reference'>('reference');
	let newPriority = $state(50);
	let newTags = $state('');
	let newContent = $state('');

	async function load() {
		loading = true;
		error = '';
		try {
			boluses = await listBoluses(!showAll);
		} catch (e) {
			error = 'Failed to connect to Anamnesis API. Is the server running?';
		}
		loading = false;
	}

	onMount(load);

	async function toggle(b: BolusMetadata) {
		if (b.active) {
			await deactivateBolus(b.id);
		} else {
			await activateBolus(b.id);
		}
		await load();
	}

	async function remove(id: string) {
		await deleteBolus(id);
		await load();
	}

	async function handleCreate() {
		try {
			await createBolus({
				id: newId,
				title: newTitle || undefined,
				summary: newSummary,
				content: newContent,
				render: newRender,
				priority: newPriority,
				tags: newTags.split(',').map((t) => t.trim()).filter(Boolean)
			});
			showCreate = false;
			newId = newTitle = newSummary = newContent = newTags = '';
			newRender = 'reference';
			newPriority = 50;
			await load();
		} catch (e: any) {
			error = e.message;
		}
	}

	let allTags = $derived(
		[...new Set(boluses.flatMap((b) => b.tags || []))].sort()
	);

	let filtered = $derived(
		boluses.filter((b) => {
			if (filterTag && !(b.tags || []).includes(filterTag)) return false;
			if (filterRender && b.render !== filterRender) return false;
			return true;
		})
	);
</script>

<div class="page-header">
	<h2>Knowledge Boluses</h2>
	<div class="actions">
		<label class="toggle-label">
			<input type="checkbox" bind:checked={showAll} onchange={load} />
			Show inactive
		</label>
		<button class="btn-primary" onclick={() => (showCreate = !showCreate)}>
			{showCreate ? 'Cancel' : '+ New Bolus'}
		</button>
	</div>
</div>

{#if error}
	<div class="error-banner">{error}</div>
{/if}

{#if showCreate}
	<div class="create-form">
		<div class="form-row">
			<input bind:value={newId} placeholder="bolus-id (slug)" />
			<input bind:value={newTitle} placeholder="Title (optional)" />
		</div>
		<input bind:value={newSummary} placeholder="Summary (one line)" />
		<textarea bind:value={newContent} placeholder="Bolus content (markdown)" rows="6"></textarea>
		<div class="form-row">
			<select bind:value={newRender}>
				<option value="reference">Reference</option>
				<option value="inline">Inline</option>
			</select>
			<label>
				Priority
				<input type="number" bind:value={newPriority} min="1" max="100" style="width:80px" />
			</label>
			<input bind:value={newTags} placeholder="Tags (comma-separated)" />
			<button class="btn-primary" onclick={handleCreate}>Create</button>
		</div>
	</div>
{/if}

<div class="filters">
	{#if allTags.length > 0}
		<select bind:value={filterTag}>
			<option value="">All tags</option>
			{#each allTags as tag}
				<option value={tag}>{tag}</option>
			{/each}
		</select>
	{/if}
	<select bind:value={filterRender}>
		<option value="">All render modes</option>
		<option value="inline">Inline</option>
		<option value="reference">Reference</option>
	</select>
	<span class="count">{filtered.length} bolus{filtered.length !== 1 ? 'es' : ''}</span>
</div>

{#if loading}
	<p class="muted">Loading...</p>
{:else if filtered.length === 0}
	<p class="muted">No boluses found.</p>
{:else}
	<div class="bolus-list">
		{#each filtered as b (b.id)}
			<div class="bolus-card" class:inactive={!b.active}>
				<div class="card-header">
					<div class="card-title">
						<strong>{b.title || b.id}</strong>
						<span class="render-badge" class:inline={b.render === 'inline'}>
							{b.render}
						</span>
						<span class="priority">P{b.priority}</span>
					</div>
					<label class="switch">
						<input type="checkbox" checked={b.active} onchange={() => toggle(b)} />
						<span class="slider"></span>
					</label>
				</div>
				<p class="summary">{b.summary}</p>
				<div class="card-footer">
					<div class="tags">
						{#each b.tags || [] as tag}
							<span class="tag">{tag}</span>
						{/each}
					</div>
					<div class="card-actions">
						<span class="date">{b.updated}</span>
						<button class="btn-danger-sm" onclick={() => remove(b.id)}>Delete</button>
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

	.actions {
		display: flex;
		gap: 16px;
		align-items: center;
	}

	.toggle-label {
		font-size: 0.85rem;
		color: var(--text-muted);
		display: flex;
		align-items: center;
		gap: 6px;
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
		display: flex;
		flex-direction: column;
		gap: 12px;
	}

	.form-row {
		display: flex;
		gap: 12px;
		align-items: center;
	}

	input, textarea, select {
		background: var(--bg);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		color: var(--text);
		padding: 8px 12px;
		font-size: 0.9rem;
		flex: 1;
	}

	textarea {
		resize: vertical;
		font-family: var(--font-mono);
		font-size: 0.85rem;
	}

	.filters {
		display: flex;
		gap: 12px;
		align-items: center;
		margin-bottom: 20px;
	}

	.filters select {
		flex: 0 0 auto;
		width: auto;
	}

	.count {
		font-size: 0.85rem;
		color: var(--text-muted);
		margin-left: auto;
	}

	.muted {
		color: var(--text-muted);
	}

	.bolus-list {
		display: flex;
		flex-direction: column;
		gap: 12px;
	}

	.bolus-card {
		background: var(--bg-surface);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		padding: 16px 20px;
		transition: border-color 0.15s;
	}

	.bolus-card:hover {
		border-color: var(--accent);
	}

	.bolus-card.inactive {
		opacity: 0.5;
	}

	.card-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 8px;
	}

	.card-title {
		display: flex;
		align-items: center;
		gap: 10px;
	}

	.render-badge {
		font-size: 0.7rem;
		padding: 2px 8px;
		border-radius: 10px;
		background: rgba(108, 140, 255, 0.15);
		color: var(--accent);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.render-badge.inline {
		background: rgba(74, 222, 128, 0.15);
		color: var(--success);
	}

	.priority {
		font-size: 0.75rem;
		color: var(--text-muted);
		font-family: var(--font-mono);
	}

	.summary {
		font-size: 0.9rem;
		color: var(--text-muted);
		margin-bottom: 12px;
	}

	.card-footer {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.tags {
		display: flex;
		gap: 6px;
	}

	.tag {
		font-size: 0.7rem;
		padding: 2px 8px;
		border-radius: 10px;
		background: var(--bg-hover);
		color: var(--text-muted);
	}

	.card-actions {
		display: flex;
		gap: 12px;
		align-items: center;
	}

	.date {
		font-size: 0.75rem;
		color: var(--text-muted);
	}

	/* Toggle switch */
	.switch {
		position: relative;
		display: inline-block;
		width: 40px;
		height: 22px;
	}

	.switch input {
		opacity: 0;
		width: 0;
		height: 0;
	}

	.slider {
		position: absolute;
		cursor: pointer;
		inset: 0;
		background: var(--border);
		border-radius: 22px;
		transition: 0.2s;
	}

	.slider::before {
		content: '';
		position: absolute;
		height: 16px;
		width: 16px;
		left: 3px;
		bottom: 3px;
		background: var(--text);
		border-radius: 50%;
		transition: 0.2s;
	}

	.switch input:checked + .slider {
		background: var(--accent);
	}

	.switch input:checked + .slider::before {
		transform: translateX(18px);
	}

	/* Buttons */
	.btn-primary {
		background: var(--accent);
		color: white;
		border: none;
		padding: 8px 16px;
		border-radius: var(--radius);
		font-size: 0.85rem;
		font-weight: 500;
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
