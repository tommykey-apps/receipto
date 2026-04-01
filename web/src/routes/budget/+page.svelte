<script lang="ts">
	import { onMount } from 'svelte';
	import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import BudgetProgress from '$lib/components/BudgetProgress.svelte';
	import AmountDisplay from '$lib/components/AmountDisplay.svelte';
	import { getBudgets, updateBudgets, getCategories } from '$lib/api';
	import { getCurrentMonth, formatCurrency, categoryIcon } from '$lib/utils';

	let categories = $state<any[]>([]);
	let budgetData = $state<Record<string, { amount: number; spent: number; icon?: string; name?: string }>>({});
	let loading = $state(true);
	let saving = $state(false);
	let selectedMonth = $state(getCurrentMonth());

	async function loadData() {
		loading = true;
		try {
			const [catData, budData] = await Promise.all([
				getCategories().catch(() => []),
				getBudgets(selectedMonth).catch(() => [])
			]);
			categories = Array.isArray(catData) ? catData : catData?.items ?? [];
			const budArray = Array.isArray(budData) ? budData : budData?.items ?? [];

			const map: typeof budgetData = {};
			for (const cat of categories) {
				const existing = budArray.find((b: any) => b.category === cat.name);
				map[cat.name] = {
					amount: existing?.amount ?? 0,
					spent: existing?.spent ?? 0,
					icon: cat.icon,
					name: cat.display_name
				};
			}
			budgetData = map;
		} finally {
			loading = false;
		}
	}

	onMount(loadData);

	const totalBudget = $derived(
		Object.values(budgetData).reduce((sum, b) => sum + b.amount, 0)
	);
	const totalSpent = $derived(
		Object.values(budgetData).reduce((sum, b) => sum + b.spent, 0)
	);
	const overallPct = $derived(
		totalBudget > 0 ? Math.min((totalSpent / totalBudget) * 100, 100) : 0
	);

	async function handleSave() {
		saving = true;
		try {
			const budgets: Record<string, number> = {};
			for (const [id, b] of Object.entries(budgetData)) {
				budgets[id] = b.amount;
			}
			await updateBudgets({ month: selectedMonth, budgets });
		} finally {
			saving = false;
		}
	}
</script>

<div class="mx-auto max-w-3xl space-y-6 p-4 pb-28 md:p-6 md:pb-6">
	<!-- Page header -->
	<div class="flex items-center justify-between animate-fade-up">
		<h1 class="text-fluid-xl font-bold tracking-tight">予算管理</h1>
		<Input
			type="month"
			bind:value={selectedMonth}
			onchange={loadData}
			class="w-40 glass rounded-xl border-glass-border"
		/>
	</div>

	{#if loading}
		<!-- Skeleton loading state -->
		<div class="space-y-6">
			<div class="glass rounded-2xl p-6">
				<div class="skeleton h-4 w-24 mb-3"></div>
				<div class="skeleton h-10 w-48 mb-3"></div>
				<div class="skeleton h-3 w-full rounded-full"></div>
			</div>
			<div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
				{#each Array(4) as _}
					<div class="glass rounded-2xl p-5">
						<div class="flex items-center gap-3 mb-4">
							<div class="skeleton h-10 w-10 rounded-xl"></div>
							<div class="skeleton h-4 w-24"></div>
						</div>
						<div class="skeleton h-3 w-full rounded-full mb-2"></div>
						<div class="skeleton h-4 w-20"></div>
					</div>
				{/each}
			</div>
		</div>
	{:else}
		<!-- Hero summary card -->
		<div class="glass rounded-2xl p-6 md:p-8 animate-fade-up">
			<p class="text-fluid-sm text-muted-foreground mb-1">月間予算合計</p>
			<p class="text-fluid-2xl amount animate-count-up text-foreground">
				{formatCurrency(totalBudget)}
			</p>

			<!-- Overall progress bar -->
			<div class="mt-4 mb-2">
				<div class="h-2.5 w-full rounded-full bg-muted/60 overflow-hidden">
					<div
						class="h-full rounded-full transition-all duration-700 ease-out"
						style="width: {overallPct}%; background: {overallPct > 90 ? 'oklch(0.65 0.18 25)' : overallPct > 70 ? 'oklch(0.75 0.14 85)' : 'oklch(0.65 0.14 265)'};"
					></div>
				</div>
			</div>
			<p class="text-fluid-sm text-muted-foreground">
				消化: <span class="amount text-foreground">{formatCurrency(totalSpent)}</span>
				<span class="ml-1 opacity-60">({overallPct.toFixed(0)}%)</span>
			</p>
		</div>

		<!-- Category bento grid -->
		<div>
			<h2 class="text-fluid-base font-semibold tracking-tight mb-4 text-muted-foreground">カテゴリ別予算</h2>
			<div class="grid grid-cols-1 sm:grid-cols-2 gap-4 stagger">
				{#each categories as cat}
					{@const b = budgetData[cat.name]}
					{#if b}
						{@const pct = b.amount > 0 ? Math.min((b.spent / b.amount) * 100, 100) : 0}
						<div class="glass rounded-2xl p-5 card-hover">
							<!-- Category header -->
							<div class="flex items-center gap-3 mb-4">
								<span class="flex items-center justify-center h-10 w-10 rounded-xl bg-muted/50 text-lg">
									{categoryIcon(cat.name)}
								</span>
								<span class="text-fluid-base font-medium truncate">{cat.display_name}</span>
							</div>

							<!-- Progress bar -->
							<div class="h-1.5 w-full rounded-full bg-muted/60 overflow-hidden mb-3">
								<div
									class="h-full rounded-full transition-all duration-500 ease-out"
									style="width: {pct}%; background: {pct > 90 ? 'oklch(0.65 0.18 25)' : pct > 70 ? 'oklch(0.75 0.14 85)' : 'oklch(0.65 0.14 265)'};"
								></div>
							</div>

							<!-- Amounts -->
							<div class="flex items-baseline justify-between mb-3">
								<span class="text-fluid-sm amount">{formatCurrency(b.spent)}</span>
								<span class="text-fluid-xs text-muted-foreground">/ {formatCurrency(b.amount)}</span>
							</div>

							<!-- Inline editable budget -->
							<div class="flex items-center gap-2 pt-2 border-t border-glass-border">
								<span class="text-fluid-xs text-muted-foreground shrink-0">予算:</span>
								<Input
									type="number"
									class="h-8 flex-1 text-sm rounded-lg bg-muted/30 border-transparent focus:border-primary/30"
									bind:value={b.amount}
									min={0}
									step={1000}
								/>
								<span class="text-fluid-xs text-muted-foreground">円</span>
							</div>
						</div>
					{/if}
				{/each}
			</div>
		</div>

		<!-- Save button: sticky on mobile, inline on desktop -->
		<div class="fixed bottom-0 inset-x-0 p-4 md:static md:p-0 z-10">
			<div class="md:hidden absolute inset-0 bg-gradient-to-t from-background via-background/80 to-transparent pointer-events-none"></div>
			<Button
				class="relative w-full rounded-xl py-3 text-fluid-base font-semibold active:scale-[0.98] transition-transform"
				onclick={handleSave}
				disabled={saving}
			>
				{saving ? '保存中...' : '予算を保存'}
			</Button>
		</div>
	{/if}
</div>
