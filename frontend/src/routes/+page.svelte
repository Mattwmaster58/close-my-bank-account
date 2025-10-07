<script lang="ts">
	import type { PageData } from './$types';
	import BankCard from '$lib/BankCard.svelte';

	let { data }: { data: PageData } = $props();

	let searchQuery = $state('');

	const bankEntries = $derived(Object.entries(data.banks));

	const filteredBanks = $derived.by(() => {
		if (!searchQuery.trim()) return bankEntries;

		const query = searchQuery.toLowerCase();
		return bankEntries.filter(([bankName]) => bankName.toLowerCase().includes(query));
	});

	const resultCount = $derived(filteredBanks.length);
</script>

<svelte:head>
	<title>Close My Bank Account</title>
</svelte:head>

<a href="https://github.com/Mattwmaster58/close-my-bank-account/issues" target="_blank" rel="noopener noreferrer" class="top-right-link">
	Found an issue? Report it on GitHub
</a>

<div class="container">
	<header>
		<h1>Close My Bank Account</h1>
		<p class="subtitle">
			Search bank closure methods and their success rates. Data from 
			<a href="https://www.doctorofcredit.com/complete-list-of-ways-to-close-bank-accounts-at-each-bank/?utm_source=closemybankaccount" target="_blank" rel="noopener noreferrer">Doctor of Credit</a>
		</p>
	</header>

	<div class="search-section">
		<input
			type="search"
			bind:value={searchQuery}
			placeholder="Search banks..."
			class="search-input"
			autofocus
		/>
		<div class="search-footer">
			<p class="result-count">
				{resultCount} {resultCount === 1 ? 'bank' : 'banks'} found
			</p>
			<a href="https://www.doctorofcredit.com/complete-list-of-ways-to-close-bank-accounts-at-each-bank/?utm_source=closemybankaccount" target="_blank" rel="noopener noreferrer" class="contribute-link">
				Have your own datapoint? Add it here
			</a>
		</div>
	</div>

	<div class="results">
		{#each filteredBanks as [bankName, attempts] (bankName)}
			<BankCard {bankName} {attempts} />
		{:else}
			<p class="no-results">No banks found matching "{searchQuery}"</p>
		{/each}
	</div>
</div>

<style>
	:global(body) {
		margin: 0;
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial,
			sans-serif;
		background: #f8f9fa;
		color: #333;
	}

	.top-right-link {
		position: absolute;
		top: 1rem;
		right: 1rem;
		color: #4a90e2;
		text-decoration: none;
		font-size: 0.9rem;
		z-index: 100;
	}

	.top-right-link:hover {
		text-decoration: underline;
	}

	.container {
		max-width: 1200px;
		margin: 0 auto;
		padding: 2rem 1rem;
	}

	header {
		text-align: center;
		margin-bottom: 2rem;
	}

	h1 {
		margin: 0;
		font-size: 2.5rem;
		color: #1a1a1a;
		font-weight: 700;
	}

	.subtitle {
		margin: 0.5rem 0 0 0;
		color: #666;
		font-size: 1.1rem;
	}

	.search-section {
		margin-bottom: 2rem;
		position: sticky;
		top: 0;
		background: #f8f9fa;
		padding: 1rem 0;
		z-index: 10;
	}

	.search-input {
		width: 100%;
		padding: 1rem 1.5rem;
		font-size: 1.125rem;
		border: 2px solid #ddd;
		border-radius: 12px;
		box-sizing: border-box;
		transition: all 0.2s ease;
		font-family: inherit;
	}

	.search-input:focus {
		outline: none;
		border-color: #4a90e2;
		box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.1);
	}

	.search-footer {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-top: 0.75rem;
	}

	.result-count {
		margin: 0;
		color: #666;
		font-size: 0.9rem;
	}

	.contribute-link {
		color: #4a90e2;
		text-decoration: none;
		font-size: 0.9rem;
	}

	.contribute-link:hover {
		text-decoration: underline;
	}

	.results {
		animation: fadeIn 0.3s ease;
	}

	@keyframes fadeIn {
		from {
			opacity: 0;
		}
		to {
			opacity: 1;
		}
	}

	.no-results {
		text-align: center;
		color: #999;
		font-size: 1.1rem;
		padding: 3rem 1rem;
	}
</style>
