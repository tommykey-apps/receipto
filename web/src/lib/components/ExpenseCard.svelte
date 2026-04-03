<script lang="ts">
	import { Trash2 } from 'lucide-svelte';
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
		ondelete?: (id: string) => void;
	}

	let { expense, onclick, ondelete }: Props = $props();
</script>

<div class="flex w-full items-center gap-3 rounded-2xl glass p-4 card-hover">
	<button
		type="button"
		class="flex flex-1 items-center gap-3 text-left min-w-0"
		onclick={onclick}
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
	{#if ondelete}
		<button
			type="button"
			class="shrink-0 p-2 rounded-lg text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors"
			aria-label="削除: {expense.store_name} {formatCurrency(expense.amount)}"
			onclick={(e) => { e.stopPropagation(); ondelete?.(expense.id); }}
		>
			<Trash2 class="h-4 w-4" />
		</button>
	{/if}
</div>
