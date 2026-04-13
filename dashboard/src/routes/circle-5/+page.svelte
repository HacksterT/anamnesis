<script lang="ts">
</script>

<div class="page-header">
	<h2>Circle 5: Behavioral Mining</h2>
	<span class="status-badge">Phase 6</span>
</div>

<div class="coming-soon">
	<div class="circle-intro">
		<p>
			The outermost circle. Micro-pipelines observe patterns from raw data &mdash;
			OS usage, study habits, communication preferences, tool usage frequency.
			Observations accumulate until they reach a confidence threshold, then compile
			into Circle 3 candidates for curation.
		</p>
	</div>

	<div class="feature-list">
		<div class="feature">
			<strong>Micro-Pipelines</strong>
			<p>Configurable observation pipelines. Each pipeline watches a specific data source
			   (OS activity, browsing patterns, study sessions) and extracts behavioral signals.</p>
		</div>
		<div class="feature">
			<strong>Confidence Ceiling</strong>
			<p>Once a pattern reaches a confidence threshold (e.g., 0.9 or 20 confirming observations),
			   collection stops for that pattern. The system self-limits rather than growing without bound.</p>
		</div>
		<div class="feature">
			<strong>JSON Index Architecture</strong>
			<p>A JSON index file tracks nodes (patterns, sources) and relationships (co-occurs, feeds).
			   Graph-shaped data stored flat. Traversal is a list comprehension, not a database query.</p>
		</div>
		<div class="feature">
			<strong>Drift Detection</strong>
			<p>If a contradicting observation appears after a pattern is confirmed, the confidence ceiling
			   reopens and the pattern is re-evaluated. Behavioral profiles adapt to change.</p>
		</div>
	</div>
</div>

<style>
	.status-badge {
		font-size: 0.75rem;
		padding: 4px 12px;
		border-radius: 12px;
		background: var(--bg-hover);
		color: var(--text-muted);
	}

	.coming-soon {
		max-width: 700px;
	}

	.circle-intro {
		margin-bottom: 32px;
	}

	.circle-intro p {
		color: var(--text-muted);
		font-size: 1rem;
		line-height: 1.7;
	}

	.feature-list {
		display: flex;
		flex-direction: column;
		gap: 16px;
	}

	.feature {
		background: var(--bg-surface);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		padding: 20px;
	}

	.feature strong {
		display: block;
		margin-bottom: 6px;
	}

	.feature p {
		font-size: 0.9rem;
		color: var(--text-muted);
		line-height: 1.6;
	}
</style>
