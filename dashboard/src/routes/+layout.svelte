<script lang="ts">
	import '../app.css';
	import { page } from '$app/state';

	let { children } = $props();

	const nav = [
		{ href: '/', label: 'Boluses' },
		{ href: '/injection', label: 'Injection' },
		{ href: '/agents', label: 'Agents' }
	];
</script>

<svelte:head>
	<title>Anamnesis</title>
</svelte:head>

<div class="shell">
	<nav class="sidebar">
		<div class="logo">
			<h1>anamnesis</h1>
			<span class="version">v0.1.0</span>
		</div>
		<ul>
			{#each nav as item}
				<li>
					<a href={item.href} class:active={page.url.pathname === item.href}>
						{item.label}
					</a>
				</li>
			{/each}
		</ul>
	</nav>
	<main class="content">
		{@render children()}
	</main>
</div>

<style>
	.shell {
		display: flex;
		min-height: 100vh;
	}

	.sidebar {
		width: 220px;
		background: var(--bg-surface);
		border-right: 1px solid var(--border);
		padding: 24px 16px;
		flex-shrink: 0;
	}

	.logo h1 {
		font-size: 1.2rem;
		font-weight: 600;
		letter-spacing: -0.02em;
	}

	.version {
		font-size: 0.75rem;
		color: var(--text-muted);
	}

	ul {
		list-style: none;
		margin-top: 32px;
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	a {
		display: block;
		padding: 8px 12px;
		border-radius: var(--radius);
		color: var(--text-muted);
		font-size: 0.9rem;
		transition: all 0.15s;
	}

	a:hover {
		background: var(--bg-hover);
		color: var(--text);
	}

	a.active {
		background: var(--bg-hover);
		color: var(--accent);
	}

	.content {
		flex: 1;
		padding: 32px 40px;
		overflow-y: auto;
	}
</style>
