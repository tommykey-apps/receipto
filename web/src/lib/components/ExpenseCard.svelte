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
	class="flex w-full items-center gap-3 rounded-2xl glass p-4 text-left card-hover"
	{onclick}
>
	<CategoryBadge icon={expense.category_icon} name={expense.category_name} />
	<div class="flex-1 min-w-0">
		<p class="truncate font-medium text-fluid-sm">{expense.store_name}</p>
		<p class="text-fluid-xs text-muted-foreground">{formatDate(expense.date)}</p>
	</div>
	<span class="amount text-fluid-sm">
		{formatCurrency(expense.amount)}
	</span>
</button>
