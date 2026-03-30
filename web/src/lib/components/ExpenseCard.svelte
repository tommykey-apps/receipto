<script lang="ts">
	import { formatCurrency, formatDate } from '$lib/utils';
	import CategoryBadge from './CategoryBadge.svelte';

	interface Props {
		expense: {
			id: string;
			store_name: string;
			amount: number;
			date: string;
			category_id: string;
			category_name?: string;
			category_icon?: string;
		};
		onclick?: () => void;
	}

	let { expense, onclick }: Props = $props();
</script>

<button
	type="button"
	class="flex w-full items-center gap-3 rounded-xl bg-card p-4 text-left transition-colors hover:bg-muted/50"
	{onclick}
>
	<CategoryBadge icon={expense.category_icon} name={expense.category_name} />
	<div class="flex-1 min-w-0">
		<p class="truncate font-medium text-card-foreground">{expense.store_name}</p>
		<p class="text-xs text-muted-foreground">{formatDate(expense.date)}</p>
	</div>
	<span class="text-sm font-semibold tabular-nums text-card-foreground">
		{formatCurrency(expense.amount)}
	</span>
</button>
