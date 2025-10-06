<script lang="ts">
	import type { BankAttempt } from '../routes/+page';
	import MethodChip from './MethodChip.svelte';

	interface Props {
		bankName: string;
		attempts: BankAttempt[];
	}

	let { bankName, attempts }: Props = $props();

	interface DateWithComment {
		date: Date;
		success: boolean;
		comment_id: string;
	}

	interface MethodStats {
		method: string;
		successCount: number;
		failCount: number;
		dates: DateWithComment[];
	}

	const methodStats = $derived.by(() => {
		const stats = new Map<string, MethodStats>();

		for (const attempt of attempts) {
			if (!stats.has(attempt.method)) {
				stats.set(attempt.method, {
					method: attempt.method,
					successCount: 0,
					failCount: 0,
					dates: []
				});
			}

			const stat = stats.get(attempt.method)!;
			if (attempt.success) {
				stat.successCount++;
			} else {
				stat.failCount++;
			}
			stat.dates.push({
				date: new Date(attempt.timestamp * 1000),
				success: attempt.success,
				comment_id: attempt.comment_id
			});
		}

		return Array.from(stats.values()).sort((a, b) => {
			const totalA = a.successCount + a.failCount;
			const totalB = b.successCount + b.failCount;
			return totalB - totalA;
		});
	});
</script>

<div class="bank-card">
	<h2>{bankName}</h2>
	<div class="chips">
		{#each methodStats as stat, index (bankName + '-' + stat.method + '-' + index)}
			<MethodChip {stat} />
		{/each}
	</div>
</div>

<style>
	.bank-card {
		background: white;
		border: 1px solid #e0e0e0;
		border-radius: 8px;
		padding: 1rem;
		margin-bottom: 1rem;
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
	}

	h2 {
		margin: 0 0 0.75rem 0;
		font-size: 1.25rem;
		color: #333;
	}

	.chips {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem;
	}
</style>
