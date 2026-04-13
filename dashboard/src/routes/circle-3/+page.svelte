<script lang="ts">
</script>

<div class="page-header">
	<h2>Circle 3: Curation Queue</h2>
	<span class="status-badge">Phase 3-4</span>
</div>

<div class="coming-soon">
	<div class="circle-intro">
		<p>
			The staging area between raw extraction and confirmed knowledge. Facts extracted
			from episodes (Circle 4) or proposed by agents land here for human review.
		</p>
	</div>

	<div class="feature-list">
		<div class="feature">
			<strong>Reconciliation Queue</strong>
			<p>Review extracted facts. Confirm promotes to Circle 2 as a permanent bolus.
			   Reject discards. Defer keeps for later review.</p>
		</div>
		<div class="feature">
			<strong>Permissiveness Slider</strong>
			<p>Controls how much autonomy the system has. Level 1: every fact requires manual
			   confirmation. Level 5: high-confidence facts auto-promote. You set the threshold.</p>
		</div>
		<div class="feature">
			<strong>Contradiction Detection</strong>
			<p>New facts are checked against existing boluses. Contradictions are flagged
			   for manual resolution rather than silently overwriting.</p>
		</div>
		<div class="feature">
			<strong>Provenance Tracking</strong>
			<p>Every fact in the queue carries its source: which episode, which agent,
			   which conversation. Audit trail from extraction to confirmation.</p>
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
