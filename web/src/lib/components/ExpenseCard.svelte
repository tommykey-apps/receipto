<script lang="ts">
	import { formatCurrency, formatDate, categoryIcon } from '$lib/utils';
	import CategoryBadge from './CategoryBadge.svelte';

	interface Props {
		expense: {
			id: string;
			store_name: string;
			amount: number;
			category: string;
			created_at: string;
			memo?: string;
			receipt_id?: string | null;
		};
		onclick?: () => void;
	}

	let { expense, onclick }: Props = $props();
</script>

<button
	type="button"
	class="flex w-full items-center gap-3 rounded-2xl glass p-4 text-left card-hover"
	{onclick}
>
	<CategoryBadge icon={categoryIcon(expense.category)} name={expense.category} />
	<div class="flex-1 min-w-0">
		<p class="truncate font-medium text-fluid-sm">{expense.store_name}</p>
		<p class="text-fluid-xs text-muted-foreground">{formatDate(expense.created_at)}</p>
	</div>
	<span class="amount text-fluid-sm">
		{formatCurrency(expense.amount)}
	</span>
</button>
