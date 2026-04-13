<script lang="ts">
	import { onMount } from 'svelte';

	let episodes: any[] = $state([]);
	let loading = $state(true);
	let error = $state('');

	onMount(async () => {
		try {
			const res = await fetch('http://localhost:8741/v1/episodes');
			episodes = await res.json();
		} catch {
			error = 'Cannot reach API.';
		}
		loading = false;
	});
</script>

<div class="page-header">
	<h2>Circle 4: Episodic Capture</h2>
	<span class="status-badge implemented">Implemented</span>
</div>

<div class="circle-intro">
	<p>
		Raw conversation capture. Every session's turns are stored in SQLite with timestamps
		and agent attribution. The recency pipeline automatically summarizes the most recent
		session into Circle 1, giving the agent short-term memory.
	</p>
</div>

{#if error}
	<div class="error-banner">{error}</div>
{/if}

<h3>Recent Episodes</h3>

{#if loading}
	<p class="muted">Loading...</p>
{:else if episodes.length === 0}
	<p class="muted">No episodes captured yet. Use <code>kf.capture_turn()</code> and <code>kf.end_session()</code> to record conversations.</p>
{:else}
	<div class="episode-list">
		{#each episodes as ep}
			<div class="episode-card">
				<div class="ep-header">
					<strong>{ep.session_id}</strong>
					{#if ep.agent}
						<span class="agent-badge">{ep.agent}</span>
					{/if}
				</div>
				<div class="ep-meta">
					<span>{ep.turn_count} turns</span>
					<span>{ep.started?.slice(0, 16)}</span>
					{#if ep.has_summary}
						<span class="summary-badge">has summary</span>
					{/if}
					{#if ep.compiled}
						<span class="compiled-badge">compiled</span>
					{/if}
				</div>
			</div>
		{/each}
	</div>
{/if}

<style>
	.status-badge {
		font-size: 0.75rem;
		padding: 4px 12px;
		border-radius: 12px;
		background: var(--bg-hover);
		color: var(--text-muted);
	}

	.status-badge.implemented {
		background: rgba(74, 222, 128, 0.15);
		color: var(--success);
	}

	.circle-intro {
		margin-bottom: 32px;
	}

	.circle-intro p {
		color: var(--text-muted);
		font-size: 1rem;
		line-height: 1.7;
		max-width: 700px;
	}

	h3 {
		font-size: 1.1rem;
		margin-bottom: 16px;
	}

	code {
		background: var(--bg-surface);
		padding: 2px 6px;
		border-radius: 4px;
		font-size: 0.85rem;
	}

	.episode-list {
		display: flex;
		flex-direction: column;
		gap: 8px;
	}

	.episode-card {
		background: var(--bg-surface);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		padding: 14px 18px;
	}

	.ep-header {
		display: flex;
		align-items: center;
		gap: 10px;
		margin-bottom: 6px;
	}

	.ep-header strong {
		font-size: 0.85rem;
		font-family: var(--font-mono);
	}

	.agent-badge {
		font-size: 0.7rem;
		padding: 2px 8px;
		border-radius: 10px;
		background: rgba(108, 140, 255, 0.15);
		color: var(--accent);
	}

	.ep-meta {
		display: flex;
		gap: 16px;
		font-size: 0.8rem;
		color: var(--text-muted);
	}

	.summary-badge {
		color: var(--success);
	}

	.compiled-badge {
		color: var(--warning);
	}
</style>
