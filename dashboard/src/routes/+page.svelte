<script lang="ts">
	import { onMount } from 'svelte';
	import { getHealth } from '$lib/api';

	let connected = $state(false);
	let version = $state('');

	onMount(async () => {
		try {
			const health = await getHealth();
			connected = true;
			version = health.version;
		} catch {
			connected = false;
		}
	});

	const circles = [
		{
			number: 5,
			name: 'Behavioral Mining',
			color: '#4a5568',
			radius: 200,
			description:
				'Outermost circle. Micro-pipelines observe patterns from raw data \u2014 OS usage, study habits, communication preferences. Observations accumulate until confidence thresholds are met, then compile into curation candidates.',
			status: 'Planned (Phase 6)'
		},
		{
			number: 4,
			name: 'Episodic Capture',
			color: '#6c8cff',
			radius: 160,
			description:
				'Raw conversation turns stored in SQLite. The recency pipeline automatically summarizes the latest session into Circle 1, giving the agent short-term memory. Configurable retention.',
			status: 'Implemented'
		},
		{
			number: 3,
			name: 'Curation Queue',
			color: '#fbbf24',
			radius: 120,
			description:
				'The staging area. Facts extracted from episodes land here for review. Confirm promotes to Circle 2. Reject discards. Defer keeps for later. The permissiveness slider controls how much autonomy the system has.',
			status: 'Planned (Phase 3\u20134)'
		},
		{
			number: 2,
			name: 'Knowledge Boluses',
			color: '#4ade80',
			radius: 80,
			description:
				'The confirmed knowledge library. Each bolus is a curated markdown file with YAML frontmatter. Inline boluses appear directly in the injection. Reference boluses are summarized with retrieval pointers.',
			status: 'Implemented'
		},
		{
			number: 1,
			name: 'Core Injection',
			color: '#f87171',
			radius: 40,
			description:
				'The center. A single markdown file (anamnesis.md) assembled from active boluses and injected into the LLM system prompt. Token-budgeted. What the agent reads on every turn.',
			status: 'Implemented'
		}
	];
</script>

<div class="framework-page">
	<div class="hero">
		<h2>Anamnesis Framework</h2>
		<p class="subtitle">
			Knowledge flows inward through curation. Raw data enters at the outer circles and is
			refined, confirmed, and compressed as it moves toward the core.
		</p>
		{#if connected}
			<span class="api-badge online">API v{version}</span>
		{:else}
			<span class="api-badge offline">API Offline</span>
		{/if}
	</div>

	<div class="principles">
		<h3>Design Principles</h3>
		<div class="principle-grid">
			<div class="principle">
				<strong>Curation over accumulation</strong>
				<p>Every fact is reviewed before it reaches the agent. Knowledge is curated, not dumped. No context stuffing.</p>
			</div>
			<div class="principle">
				<strong>Token budget discipline</strong>
				<p>The injection has hard limits. Boluses carry summaries; the agent retrieves full details on demand. You control what fits.</p>
			</div>
			<div class="principle">
				<strong>One primitive: the bolus</strong>
				<p>Identity, facts, skills, constraints, expert personas — everything is a knowledge bolus with a render mode and tags. Simple to reason about.</p>
			</div>
			<div class="principle">
				<strong>LLM-agnostic</strong>
				<p>Any model reads anamnesis.md. The retrieve_knowledge tool works with Claude, GPT, Gemma, or any agent framework. No vendor lock-in.</p>
			</div>
		</div>
	</div>

	<div class="diagram-section">
		<h3 class="section-title">The Five-Circle Model</h3>
		<p class="section-subtitle">Knowledge flows inward through curation — from raw observations to the agent's working memory.</p>
		<svg viewBox="0 0 500 500" class="circle-diagram">
			{#each circles as circle}
				<circle
					cx="250"
					cy="250"
					r={circle.radius}
					fill="none"
					stroke={circle.color}
					stroke-width="2"
					opacity="0.3"
				/>
				<circle
					cx="250"
					cy="250"
					r={circle.radius}
					fill={circle.color}
					opacity="0.06"
				/>
			{/each}

			<!-- Labels on the circles -->
			<text x="250" y="250" text-anchor="middle" dy="0.35em" fill="#f87171" font-size="11" font-weight="600">
				C1: Core
			</text>
			<text x="250" y="200" text-anchor="middle" fill="#4ade80" font-size="10" font-weight="500">
				C2: Boluses
			</text>
			<text x="250" y="155" text-anchor="middle" fill="#fbbf24" font-size="10" font-weight="500">
				C3: Curation
			</text>
			<text x="250" y="112" text-anchor="middle" fill="#6c8cff" font-size="10" font-weight="500">
				C4: Episodic
			</text>
			<text x="250" y="68" text-anchor="middle" fill="#4a5568" font-size="10" font-weight="500">
				C5: Behavioral
			</text>

			<!-- Flow arrows (inward) -->
			<defs>
				<marker id="arrow" viewBox="0 0 10 10" refX="5" refY="5"
					markerWidth="4" markerHeight="4" orient="auto-start-reverse">
					<path d="M 0 0 L 10 5 L 0 10 z" fill="var(--text-muted)" opacity="0.5" />
				</marker>
			</defs>

			<!-- Right side flow arrows -->
			<line x1="440" y1="300" x2="410" y2="290" stroke="var(--text-muted)" stroke-width="1" opacity="0.3" marker-end="url(#arrow)" />
			<line x1="400" y1="300" x2="370" y2="290" stroke="var(--text-muted)" stroke-width="1" opacity="0.3" marker-end="url(#arrow)" />
			<line x1="360" y1="300" x2="335" y2="290" stroke="var(--text-muted)" stroke-width="1" opacity="0.3" marker-end="url(#arrow)" />
			<line x1="320" y1="295" x2="300" y2="285" stroke="var(--text-muted)" stroke-width="1" opacity="0.3" marker-end="url(#arrow)" />

			<!-- "Knowledge flows inward" label -->
			<text x="420" y="340" text-anchor="middle" fill="var(--text-muted)" font-size="8" opacity="0.5">
				knowledge flows inward
			</text>
			<text x="420" y="350" text-anchor="middle" fill="var(--text-muted)" font-size="8" opacity="0.5">
				through curation
			</text>
		</svg>
	</div>

	<div class="circle-cards">
		{#each circles.toReversed() as circle}
			<div class="circle-card">
				<div class="card-header">
					<div class="circle-badge" style="background: {circle.color}20; color: {circle.color}; border-color: {circle.color}40;">
						Circle {circle.number}
					</div>
					<h3>{circle.name}</h3>
					<span class="status-badge" class:implemented={circle.status === 'Implemented'}>
						{circle.status}
					</span>
				</div>
				<p>{circle.description}</p>
			</div>
		{/each}
	</div>

</div>

<style>
	.framework-page {
		max-width: 900px;
	}

	.hero {
		margin-bottom: 40px;
	}

	h2 {
		font-size: 1.6rem;
		font-weight: 700;
		margin-bottom: 8px;
	}

	.subtitle {
		color: var(--text-muted);
		font-size: 1rem;
		line-height: 1.6;
		max-width: 600px;
		margin-bottom: 12px;
	}

	.api-badge {
		display: inline-block;
		font-size: 0.75rem;
		padding: 3px 10px;
		border-radius: 12px;
	}

	.api-badge.online {
		background: rgba(74, 222, 128, 0.15);
		color: var(--success);
	}

	.api-badge.offline {
		background: rgba(248, 113, 113, 0.15);
		color: var(--danger);
	}

	.section-title {
		font-size: 1.2rem;
		font-weight: 600;
		margin-bottom: 6px;
	}

	.section-subtitle {
		color: var(--text-muted);
		font-size: 0.9rem;
		margin-bottom: 24px;
	}

	.diagram-section {
		margin-bottom: 48px;
	}

	.diagram-section svg {
		display: block;
		margin: 0 auto;
	}

	.circle-diagram {
		width: 100%;
		max-width: 500px;
		height: auto;
	}

	.circle-cards {
		display: flex;
		flex-direction: column;
		gap: 12px;
		margin-bottom: 48px;
	}

	.circle-card {
		background: var(--bg-surface);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		padding: 20px;
	}

	.card-header {
		display: flex;
		align-items: center;
		gap: 12px;
		margin-bottom: 10px;
	}

	.circle-badge {
		font-size: 0.7rem;
		font-weight: 600;
		padding: 3px 10px;
		border-radius: 10px;
		border: 1px solid;
		white-space: nowrap;
	}

	.card-header h3 {
		font-size: 1rem;
		font-weight: 600;
		flex: 1;
	}

	.status-badge {
		font-size: 0.7rem;
		padding: 3px 10px;
		border-radius: 10px;
		background: var(--bg-hover);
		color: var(--text-muted);
		white-space: nowrap;
	}

	.status-badge.implemented {
		background: rgba(74, 222, 128, 0.15);
		color: var(--success);
	}

	.circle-card p {
		font-size: 0.9rem;
		color: var(--text-muted);
		line-height: 1.6;
	}

	.principles {
		background: var(--bg-surface);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		padding: 24px;
		margin-bottom: 48px;
	}

	.principles h3 {
		font-size: 1.1rem;
		font-weight: 600;
		margin-bottom: 20px;
	}

	.principle-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 20px;
	}

	.principle {
		padding: 16px;
		background: var(--bg);
		border-radius: var(--radius);
	}

	.principle strong {
		display: block;
		margin-bottom: 6px;
		font-size: 0.9rem;
	}

	.principle p {
		font-size: 0.8rem;
		color: var(--text-muted);
		line-height: 1.5;
	}
</style>
