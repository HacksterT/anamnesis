<script lang="ts">
	import { onMount } from 'svelte';
	import {
		getCurationQueue,
		stageFact,
		confirmItem,
		rejectItem,
		deferItem,
		type CurationItem
	} from '$lib/api';

	let items = $state<CurationItem[]>([]);
	let loading = $state(true);
	let error = $state('');
	let showStageForm = $state(false);

	// Stage form state
	let stageFact_ = $state('');
	let stageBolus = $state('');
	let stageConfidence = $state(0.7);
	let staging = $state(false);
	let stageError = $state('');

	// Confirm modal state
	let confirmingId = $state<number | null>(null);
	let confirmBolus = $state('');
	let confirmError = $state('');
	let confirming = $state(false);

	async function load() {
		loading = true;
		error = '';
		try {
			items = await getCurationQueue(100);
		} catch (e) {
			error = 'Failed to load curation queue.';
		}
		loading = false;
	}

	onMount(load);

	async function handleStage() {
		if (!stageFact_.trim()) return;
		staging = true;
		stageError = '';
		try {
			await stageFact({
				fact: stageFact_.trim(),
				suggested_bolus: stageBolus.trim() || undefined,
				confidence: stageConfidence
			});
			stageFact_ = '';
			stageBolus = '';
			stageConfidence = 0.7;
			showStageForm = false;
			await load();
		} catch (e: any) {
			stageError = e.message || 'Failed to stage fact.';
		}
		staging = false;
	}

	function startConfirm(id: number, suggested: string | null) {
		confirmingId = id;
		confirmBolus = suggested || '';
		confirmError = '';
	}

	async function handleConfirm() {
		if (!confirmBolus.trim() || confirmingId === null) return;
		confirming = true;
		confirmError = '';
		try {
			await confirmItem(confirmingId, confirmBolus.trim());
			confirmingId = null;
			confirmBolus = '';
			await load();
		} catch (e: any) {
			confirmError = e.message || 'Failed to confirm item.';
		}
		confirming = false;
	}

	async function handleReject(id: number) {
		try {
			await rejectItem(id);
			await load();
		} catch (e: any) {
			error = e.message || 'Failed to reject item.';
		}
	}

	async function handleDefer(id: number) {
		try {
			await deferItem(id);
			await load();
		} catch (e: any) {
			error = e.message || 'Failed to defer item.';
		}
	}

	function confidenceColor(c: number): string {
		if (c >= 0.8) return 'var(--success)';
		if (c >= 0.6) return 'var(--warning)';
		return 'var(--danger)';
	}
</script>

<div class="page-header">
	<h2>Circle 3: Curation Queue</h2>
	<div class="header-actions">
		<span class="queue-count">{items.length} pending</span>
		<button class="btn-primary" onclick={() => (showStageForm = !showStageForm)}>
			{showStageForm ? 'Cancel' : '+ Stage Fact'}
		</button>
	</div>
</div>

{#if error}
	<div class="error-banner">{error}</div>
{/if}

{#if showStageForm}
	<div class="create-form">
		<div class="form-field">
			<label for="stage-fact">Fact <span class="muted">(declarative, concise)</span></label>
			<textarea
				id="stage-fact"
				bind:value={stageFact_}
				placeholder="e.g. Prefer FastAPI over Flask for async workloads."
				rows="3"
			></textarea>
		</div>
		<div class="form-row">
			<div class="form-field flex1">
				<label for="stage-bolus">Suggested bolus ID <span class="muted">(optional)</span></label>
				<input
					id="stage-bolus"
					type="text"
					bind:value={stageBolus}
					placeholder="cto-knowledge"
				/>
			</div>
			<div class="form-field confidence-field">
				<label for="stage-confidence">Confidence: {stageConfidence.toFixed(1)}</label>
				<input
					id="stage-confidence"
					type="range"
					min="0"
					max="1"
					step="0.05"
					bind:value={stageConfidence}
				/>
			</div>
		</div>
		{#if stageError}
			<div class="error-banner">{stageError}</div>
		{/if}
		<div class="form-row">
			<button class="btn-primary" onclick={handleStage} disabled={staging || !stageFact_.trim()}>
				{staging ? 'Staging…' : 'Stage Fact'}
			</button>
		</div>
	</div>
{/if}

{#if loading}
	<p class="muted">Loading queue…</p>
{:else if items.length === 0}
	<div class="empty-state">
		<p>No pending facts in the curation queue.</p>
		<p class="muted">
			Run <code>anamnesis compile</code> to extract facts from episodes, or use
			<strong>+ Stage Fact</strong> to add one manually.
		</p>
	</div>
{:else}
	<div class="item-list">
		{#each items as item (item.id)}
			<div class="curation-card">
				<div class="card-body">
					<p class="fact-text">{item.fact}</p>
					<div class="meta-row">
						<div class="confidence-pill" style="--conf-color: {confidenceColor(item.confidence)}">
							<span class="conf-bar" style="width: {Math.round(item.confidence * 100)}%"></span>
							<span class="conf-label">{Math.round(item.confidence * 100)}% confidence</span>
						</div>
						{#if item.suggested_bolus}
							<span class="tag">→ {item.suggested_bolus}</span>
						{/if}
						{#if item.source_agent}
							<span class="tag muted-tag">{item.source_agent}</span>
						{/if}
						{#if item.source_url}
							<a href={item.source_url} target="_blank" class="tag muted-tag source-link" rel="noreferrer">
								source ↗
							</a>
						{/if}
					</div>
				</div>

				{#if confirmingId === item.id}
					<div class="confirm-row">
						<input
							type="text"
							bind:value={confirmBolus}
							placeholder="target-bolus-id"
							class="bolus-input"
							onkeydown={(e) => e.key === 'Enter' && handleConfirm()}
						/>
						<button
							class="btn-sm btn-confirm"
							onclick={handleConfirm}
							disabled={confirming || !confirmBolus.trim()}
						>
							{confirming ? '…' : 'Confirm'}
						</button>
						<button class="btn-sm btn-cancel" onclick={() => (confirmingId = null)}>Cancel</button>
						{#if confirmError}
							<span class="inline-error">{confirmError}</span>
						{/if}
					</div>
				{:else}
					<div class="action-row">
						<button
							class="btn-sm btn-confirm"
							onclick={() => startConfirm(item.id, item.suggested_bolus)}
						>
							Confirm →
						</button>
						<button class="btn-sm btn-defer" onclick={() => handleDefer(item.id)}>Defer</button>
						<button class="btn-sm btn-reject" onclick={() => handleReject(item.id)}>Reject</button>
					</div>
				{/if}
			</div>
		{/each}
	</div>
{/if}

<style>
	/* .page-header, .error-banner, .muted, .create-form, .form-row,
	   .btn-primary — defined in app.css */

	.header-actions {
		display: flex;
		gap: 12px;
		align-items: center;
	}

	.queue-count {
		font-size: 0.85rem;
		color: var(--text-muted);
	}

	.form-field {
		display: flex;
		flex-direction: column;
		gap: 6px;
	}

	.form-field label {
		font-size: 0.85rem;
		color: var(--text-muted);
	}

	.form-field textarea,
	.form-field input[type='text'] {
		background: var(--bg);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		color: var(--text);
		padding: 8px 12px;
		font-size: 0.9rem;
		font-family: inherit;
		width: 100%;
		resize: vertical;
	}

	.flex1 {
		flex: 1;
	}

	.confidence-field {
		min-width: 180px;
	}

	.confidence-field input[type='range'] {
		width: 100%;
		accent-color: var(--accent);
	}

	.empty-state {
		background: var(--bg-surface);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		padding: 40px 24px;
		text-align: center;
	}

	.empty-state p {
		margin-bottom: 8px;
	}

	.empty-state code {
		font-family: var(--font-mono);
		background: var(--bg);
		padding: 2px 6px;
		border-radius: 4px;
		font-size: 0.85rem;
	}

	.item-list {
		display: flex;
		flex-direction: column;
		gap: 12px;
	}

	.curation-card {
		background: var(--bg-surface);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		padding: 16px 20px;
	}

	.card-body {
		margin-bottom: 12px;
	}

	.fact-text {
		font-size: 0.95rem;
		line-height: 1.5;
		margin-bottom: 10px;
	}

	.meta-row {
		display: flex;
		flex-wrap: wrap;
		gap: 8px;
		align-items: center;
	}

	.confidence-pill {
		position: relative;
		display: inline-flex;
		align-items: center;
		height: 20px;
		min-width: 120px;
		border-radius: 10px;
		background: var(--bg);
		overflow: hidden;
	}

	.conf-bar {
		position: absolute;
		left: 0;
		top: 0;
		bottom: 0;
		background: var(--conf-color);
		opacity: 0.25;
		border-radius: 10px;
	}

	.conf-label {
		position: relative;
		font-size: 0.72rem;
		color: var(--conf-color);
		padding: 0 8px;
		font-weight: 600;
	}

	.tag {
		font-size: 0.75rem;
		padding: 2px 8px;
		border-radius: 4px;
		background: var(--bg);
		color: var(--accent);
		border: 1px solid var(--border);
		font-family: var(--font-mono);
	}

	.muted-tag {
		color: var(--text-muted);
	}

	.source-link {
		text-decoration: none;
	}

	.source-link:hover {
		color: var(--accent);
	}

	.action-row,
	.confirm-row {
		display: flex;
		gap: 8px;
		align-items: center;
		flex-wrap: wrap;
	}

	.btn-sm {
		padding: 5px 12px;
		border-radius: var(--radius);
		font-size: 0.8rem;
		font-weight: 500;
		border: 1px solid transparent;
		cursor: pointer;
		font-family: inherit;
	}

	.btn-confirm {
		background: var(--success);
		color: #000;
		border-color: var(--success);
	}

	.btn-confirm:hover {
		opacity: 0.85;
	}

	.btn-confirm:disabled {
		opacity: 0.5;
		cursor: default;
	}

	.btn-defer {
		background: none;
		border-color: var(--warning);
		color: var(--warning);
	}

	.btn-defer:hover {
		background: rgba(251, 191, 36, 0.1);
	}

	.btn-reject {
		background: none;
		border-color: var(--danger);
		color: var(--danger);
	}

	.btn-reject:hover {
		background: rgba(248, 113, 113, 0.1);
	}

	.btn-cancel {
		background: none;
		border-color: var(--border);
		color: var(--text-muted);
	}

	.btn-cancel:hover {
		background: var(--bg-hover);
	}

	.bolus-input {
		background: var(--bg);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		color: var(--text);
		padding: 5px 10px;
		font-size: 0.85rem;
		font-family: var(--font-mono);
		width: 200px;
	}

	.inline-error {
		font-size: 0.8rem;
		color: var(--danger);
	}
</style>
