<script lang="ts">
  import type { PageData } from './$types';
  import BankCard from '$lib/BankCard.svelte';

  let {data}: { data: PageData } = $props();

  interface MatchChunk {
    type: "full" | "prefix"
    chunk: string
  }


  function* generateMatchChunkPermutations(query: string) {
    // this considers that each chunk of the query may be an abbreviation (cu -> credit union)
    const chunks = query
      .split(/\s+/)
    const chunkIndexes = chunks
      .entries()
      .toArray()
      .sort((chunk1, chunk2) => chunk2.length - chunk1.length)
      .map(([index, _]) => index);
    // shorter chunks are more likely to be abbreviations so we yield those first
    for (const abbreviationChunkIndex of chunkIndexes) {
      let permutation: string[] = [];
      for (const [chunkIndex, chunk] of chunks.entries()) {
        if (chunkIndex === abbreviationChunkIndex) {
          // selected for expansion
          permutation.push(...[...chunk])
        } else {
          permutation.push(chunk);
        }
      }
      yield permutation;
    }
  }

  let searchQuery = $state('');

  const bankEntries = $derived(Object.entries(data.banks));

  const spaceNormalize = (str: string) => str.toLowerCase().replace(/\./g, '').replace(/\s+/g, ' ').trim();
  const zip = (...arrays) => {
    const minLen = Math.min(...arrays.map(arr => arr.length));
    return Array.from({length: minLen}, (_, i) => arrays.map(arr => arr[i]));
  }

  const filteredBanks = $derived.by(() => {
    if (!searchQuery.trim()) return bankEntries;

    const query = spaceNormalize(searchQuery);
    return bankEntries
      .map(([bankName, attempts]) => {
        const normalized = spaceNormalize(bankName);
        const idx = normalized.indexOf(query);
        if (idx !== -1) {
          return {bankName, attempts, idx, rank: 0};
        }

        // Abbreviation match - you can search "alliant cu"
        // this is generalized, and more complicated than it needed to be
        const bankNameChunks = normalized.split(/\s+/);
        for (const perms of generateMatchChunkPermutations(query)) {
          if (perms.length > bankNameChunks.length) continue;
          // needs a lot more work
        }

        return null;
      })
      .filter(Boolean)
      .sort((a, b) => a.rank - b.rank || a.idx - b.idx)
      .map(({bankName, attempts}) => [bankName, attempts]);
  });

  const resultCount = $derived(filteredBanks.length);
  const resultDatapoints = $derived(filteredBanks.reduce((sum, [_, attempts]) => sum + attempts.length, 0));

  const lastUpdatedDate = $derived(new Date(data.metadata.lastUpdated).toLocaleString());
</script>

<!-- svelte-ignore a11y-autofocus -->
<svelte:head>
    <title>Close My Bank Account</title>
</svelte:head>

<a href="https://github.com/Mattwmaster58/close-my-bank-account/actions" target="_blank" rel="noopener noreferrer"
   class="top-left-link" title="Last updated: {lastUpdatedDate}">
    <span class="desktop-text">Last updated: {lastUpdatedDate}</span>
    <span class="mobile-icon">🔄</span>
</a>

<a href="https://github.com/Mattwmaster58/close-my-bank-account/issues" target="_blank" rel="noopener noreferrer"
   class="top-right-link">
    Found an issue? Report it on GitHub
</a>

<div class="container">
    <header>
        <h1>Close My Bank Account</h1>
        <p class="subtitle">
            Search bank closure methods and their success rates. Data from
            <a href="https://www.doctorofcredit.com/complete-list-of-ways-to-close-bank-accounts-at-each-bank/?utm_source=closemybankaccount#comments"
               target="_blank" rel="noopener noreferrer">Doctor of Credit</a>
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
                {resultCount} {resultCount === 1 ? 'bank' : 'banks'} / {resultDatapoints} datapoints
            </p>
            <a href="https://www.doctorofcredit.com/complete-list-of-ways-to-close-bank-accounts-at-each-bank/?utm_source=closemybankaccount"
               target="_blank" rel="noopener noreferrer" class="contribute-link">
                Have your own datapoint? Add it here
            </a>
        </div>
    </div>

    <div class="results">
        {#each filteredBanks as [bankName, attempts] (bankName)}
            <BankCard {bankName} {attempts}/>
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

    .top-left-link {
        position: absolute;
        top: 1rem;
        left: 1rem;
        color: #4a90e2;
        text-decoration: none;
        font-size: 0.9rem;
        z-index: 100;
    }

    .top-left-link:hover {
        text-decoration: underline;
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

    .subtitle a {
        color: #4a90e2;
        text-decoration: none;
    }

    .subtitle a:hover {
        text-decoration: underline;
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

    .desktop-text {
        display: inline;
    }

    .mobile-icon {
        display: none;
        font-size: 1.2rem;
    }

    @media (max-width: 768px) {
        .top-left-link {
            top: 0.5rem;
            left: 0.5rem;
            font-size: 1.2rem;
        }

        .top-right-link {
            display: none;
        }

        .desktop-text {
            display: none;
        }

        .mobile-icon {
            display: inline;
        }

        .container {
            padding: 3rem 0.5rem 1rem;
        }

        h1 {
            font-size: 2rem;
        }

        .subtitle {
            font-size: 1rem;
            padding: 0 1rem;
        }

        .search-section {
            padding: 0.5rem;
        }

        .search-input {
            font-size: 1rem;
            padding: 0.75rem 1rem;
        }

        .search-footer {
            flex-direction: column;
            align-items: flex-start;
            gap: 0.5rem;
            padding: 0 0.5rem;
        }

        .contribute-link {
            align-self: flex-end;
        }
    }

    @media (max-width: 480px) {
        h1 {
            font-size: 1.75rem;
        }

        .subtitle {
            font-size: 0.9rem;
        }
    }
</style>
