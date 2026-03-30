<script lang="ts">
	import { formatCurrency } from '$lib/utils';

	interface Props {
		label: string;
		icon?: string;
		spent: number;
		budget: number;
	}

	let { label, icon = '📦', spent, budget }: Props = $props();

	const percentage = $derived(budget > 0 ? Math.min((spent / budget) * 100, 100) : 0);
	const color = $derived(
		percentage >= 90 ? 'bg-destructive' : percentage >= 70 ? 'bg-yellow-500' : 'bg-primary'
	);
</script>

<div class="space-y-2">
	<div class="flex items-center justify-between">
		<div class="flex items-center gap-2">
			<span class="text-base">{icon}</span>
			<span class="text-sm font-medium">{label}</span>
		</div>
		<span class="text-xs text-muted-foreground tabular-nums">
			{formatCurrency(spent)} / {formatCurrency(budget)}
		</span>
	</div>
	<div class="h-2 w-full overflow-hidden rounded-full bg-muted">
		<div
			class="h-full rounded-full transition-all duration-500 {color}"
			style="width: {percentage}%"
		></div>
	</div>
</div>
