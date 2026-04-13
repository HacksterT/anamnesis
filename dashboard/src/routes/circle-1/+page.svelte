<script lang="ts">
	import { onMount } from 'svelte';
	import { getInjection, getInjectionMetrics, type InjectionMetrics } from '$lib/api';

	let injection = $state('');
	let metrics = $state<InjectionMetrics | null>(null);
	let loading = $state(true);
	let error = $state('');

	async function load() {
		loading = true;
		error = '';
		try {
			[injection, metrics] = await Promise.all([getInjection(), getInjectionMetrics()]);
		} catch (e) {
			error = 'Failed to connect to Anamnesis API.';
		}
		loading = false;
	}

	onMount(load);

	let budgetColor = $derived(
		metrics?.status === 'exceeded'
			? 'var(--danger)'
			: metrics?.status === 'warning'
				? 'var(--warning)'
				: 'var(--success)'
	);

	let budgetPct = $derived(
		metrics ? Math.min((metrics.total_tokens / metrics.hard_ceiling) * 100, 100) : 0
	);

	let softMaxPct = $derived(
		metrics ? (metrics.soft_max / metrics.hard_ceiling) * 100 : 0
	);
</script>

<div class="page-header">
	<h2>Injection Preview</h2>
	<button class="btn-primary" onclick={load}>Refresh</button>
</div>

{#if error}
	<div class="error-banner">{error}</div>
{/if}

{#if loading}
	<p class="muted">Loading...</p>
{:else if metrics}
	<div class="metrics-bar">
		<div class="metrics-labels">
			<span>
				<strong>{metrics.total_tokens}</strong> tokens
				<span class="muted">/ {metrics.soft_max} soft max / {metrics.hard_ceiling} ceiling</span>
			</span>
			<span class="status" style="color: {budgetColor}">
				{metrics.status.toUpperCase()}
			</span>
		</div>

		<div class="budget-track">
			<div class="budget-fill" style="width: {budgetPct}%; background: {budgetColor}"></div>
			<div class="budget-marker" style="left: {softMaxPct}%" title="Soft max ({metrics.soft_max})"></div>
		</div>

		<div class="metrics-summary">
			<span>{metrics.active_boluses} active / {metrics.total_boluses} total boluses</span>
			<span>Utilization: {metrics.utilization_pct}%</span>
		</div>
	</div>

	<div class="injection-preview">
		<pre><code>{injection}</code></pre>
	</div>
{/if}

<style>
	/* .page-header, .error-banner, .muted, .btn-primary — defined in app.css */

	.metrics-bar {
		background: var(--bg-surface);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		padding: 20px;
		margin-bottom: 24px;
	}

	.metrics-labels {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 12px;
		font-size: 0.9rem;
	}

	.status {
		font-weight: 600;
		font-size: 0.8rem;
		letter-spacing: 0.05em;
	}

	.budget-track {
		position: relative;
		height: 8px;
		background: var(--bg);
		border-radius: 4px;
		overflow: visible;
		margin-bottom: 12px;
	}

	.budget-fill {
		height: 100%;
		border-radius: 4px;
		transition: width 0.3s ease;
	}

	.budget-marker {
		position: absolute;
		top: -4px;
		width: 2px;
		height: 16px;
		background: var(--text-muted);
		transform: translateX(-1px);
	}

	.metrics-summary {
		display: flex;
		justify-content: space-between;
		font-size: 0.8rem;
		color: var(--text-muted);
	}

	.injection-preview {
		background: var(--bg-surface);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		padding: 24px;
		overflow-x: auto;
	}

	pre {
		margin: 0;
		white-space: pre-wrap;
		word-wrap: break-word;
	}

	code {
		font-size: 0.85rem;
		line-height: 1.7;
		color: var(--text);
	}

</style>
