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
		percentage >= 90
			? 'bg-[oklch(0.65_0.15_25)]'
			: percentage >= 70
				? 'bg-[oklch(0.75_0.14_85)]'
				: 'bg-primary'
	);
	const statusText = $derived(
		percentage >= 90 ? '超過注意' : percentage >= 70 ? 'やや超過' : ''
	);
</script>

<div class="space-y-2.5">
	<div class="flex items-center justify-between">
		<div class="flex items-center gap-2">
			<span class="text-base">{icon}</span>
			<span class="text-fluid-sm font-medium">{label}</span>
			{#if statusText}
				<span class="text-[10px] font-medium px-1.5 py-0.5 rounded-md {percentage >= 90 ? 'bg-[oklch(0.65_0.15_25)]/10 text-[oklch(0.65_0.15_25)]' : 'bg-[oklch(0.75_0.14_85)]/10 text-[oklch(0.75_0.14_85)]'}">
					{statusText}
				</span>
			{/if}
		</div>
		<span class="text-fluid-xs text-muted-foreground amount">
			{formatCurrency(spent)} / {formatCurrency(budget)}
		</span>
	</div>
	<div class="h-1.5 w-full overflow-hidden rounded-full bg-muted">
		<div
			class="h-full rounded-full transition-all duration-700 ease-out {color}"
			style="width: {percentage}%"
		></div>
	</div>
</div>
