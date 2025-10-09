<script lang="ts">
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

	interface Props {
		stat: MethodStats;
	}

	let { stat }: Props = $props();

	let expanded = $state(false);

	const methodIcons: Record<string, string> = {
		chat: '💬',
		'secure-message': '📧',
		phone: '📞',
		'in-branch': '🏢',
		'on-platform': '🌐',
		'0-balance': '💰',
		unknown: '❓'
	};

	const getMethodIcon = (method: string) => {
		return methodIcons[method] || '📋';
	};

	const formatMethodName = (method: string) => {
		return method
			.split('-')
			.map((word) => word.charAt(0).toUpperCase() + word.slice(1))
			.join(' ');
	};

	const formatDate = (date: Date) => {
		return date.toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric'
		});
	};

	const getCommentUrl = (commentId: string) => {
		return `https://www.doctorofcredit.com/complete-list-of-ways-to-close-bank-accounts-at-each-bank/?utm_source=closemybankaccount#comment-${commentId}`;
	};

	const sortedDates = $derived(
		[...stat.dates].sort((a, b) => b.date.getTime() - a.date.getTime())
	);
</script>

<div class="chip-container">
	<button class="chip" onclick={() => (expanded = !expanded)} title={formatMethodName(stat.method)}>
		<span class="method-icon">{getMethodIcon(stat.method)}</span>
		<span class="method">{formatMethodName(stat.method)}</span>
		{#if stat.successCount > 0}
			<span class="badge success">{stat.successCount}✓</span>
		{/if}
		{#if stat.failCount > 0}
			<span class="badge fail">{stat.failCount}✗</span>
		{/if}
		<span class="expand-icon">{expanded ? '▼' : '▶'}</span>
	</button>

	{#if expanded}
		<ul class="dates">
			{#each sortedDates as { date, success, comment_id }, index (comment_id + '-' + index)}
				<li class="date-item">
					<a href={getCommentUrl(comment_id)} target="_blank" rel="noopener noreferrer" class:success class:fail={!success}>
						<span class="status-icon">{success ? '✓' : '✗'}</span>
						<span>{formatDate(date)}</span>
					</a>
				</li>
			{/each}
		</ul>
	{/if}
</div>

<style>
	.chip-container {
		display: flex;
		flex-direction: column;
	}

	.chip {
		display: inline-flex;
		align-items: center;
		gap: 0.375rem;
		padding: 0.375rem 0.75rem;
		background: #f5f5f5;
		border: 1px solid #ddd;
		border-radius: 16px;
		font-size: 0.875rem;
		cursor: pointer;
		transition: all 0.15s ease;
		font-family: inherit;
	}

	.chip:hover {
		background: #e8e8e8;
		border-color: #ccc;
	}

	.method-icon {
		font-size: 1rem;
		line-height: 1;
	}

	.method {
		color: #555;
		font-weight: 500;
	}

	.badge {
		padding: 0.125rem 0.375rem;
		border-radius: 10px;
		font-size: 0.75rem;
		font-weight: 600;
	}

	.badge.success {
		background: #d4edda;
		color: #155724;
	}

	.badge.fail {
		background: #f8d7da;
		color: #721c24;
	}

	.expand-icon {
		font-size: 0.625rem;
		color: #888;
	}

	.dates {
		margin: 0.5rem 0 0 0;
		padding: 0.5rem 0.5rem 0.5rem 1.5rem;
		list-style: none;
	}

	.date-item {
		margin-bottom: 0.25rem;
		position: relative;
	}

	.date-item::before {
		content: '•';
		position: absolute;
		left: -1rem;
		font-size: 1.2rem;
		line-height: 1.4;
	}

	.date-item a {
		display: inline-flex;
		align-items: center;
		gap: 0.375rem;
		font-size: 0.8125rem;
		text-decoration: none;
		color: inherit;
		padding: 0.125rem 0;
		transition: opacity 0.15s ease;
	}

	a:hover {
		opacity: 0.7;
		text-decoration: underline;
	}

	.date-item a.success {
		color: #2e7d32;
	}

	.date-item a.fail {
		color: #c62828;
	}

	.status-icon {
		font-weight: bold;
		font-size: 0.875rem;
	}
</style>
