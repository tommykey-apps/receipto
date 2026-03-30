<script lang="ts">
	import { onMount } from 'svelte';
	import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import BudgetProgress from '$lib/components/BudgetProgress.svelte';
	import AmountDisplay from '$lib/components/AmountDisplay.svelte';
	import { getBudgets, updateBudgets, getCategories } from '$lib/api';
	import { getCurrentMonth, formatCurrency } from '$lib/utils';

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
				const existing = budArray.find((b: any) => b.category_id === cat.id);
				map[cat.id] = {
					amount: existing?.amount ?? 0,
					spent: existing?.spent ?? 0,
					icon: cat.icon,
					name: cat.name
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

<div class="mx-auto max-w-2xl space-y-4 p-4 md:p-6">
	<div class="flex items-center justify-between">
		<h1 class="text-2xl font-bold">予算管理</h1>
		<Input
			type="month"
			bind:value={selectedMonth}
			onchange={loadData}
			class="w-40"
		/>
	</div>

	{#if loading}
		<div class="flex items-center justify-center py-12">
			<p class="text-muted-foreground">読み込み中...</p>
		</div>
	{:else}
		<Card class="rounded-xl">
			<CardContent class="pt-6">
				<p class="text-sm text-muted-foreground">月間予算合計</p>
				<AmountDisplay amount={totalBudget} size="lg" />
				<p class="mt-1 text-sm text-muted-foreground">
					消化: {formatCurrency(totalSpent)} ({totalBudget > 0 ? ((totalSpent / totalBudget) * 100).toFixed(0) : 0}%)
				</p>
			</CardContent>
		</Card>

		<Card class="rounded-xl">
			<CardHeader>
				<CardTitle class="text-base">カテゴリ別予算</CardTitle>
			</CardHeader>
			<CardContent class="space-y-6">
				{#each categories as cat}
					{@const b = budgetData[cat.id]}
					{#if b}
						<div class="space-y-2">
							<BudgetProgress
								label={cat.name}
								icon={cat.icon}
								spent={b.spent}
								budget={b.amount}
							/>
							<div class="flex items-center gap-2">
								<span class="text-xs text-muted-foreground">予算:</span>
								<Input
									type="number"
									class="h-8 w-32 text-sm"
									bind:value={b.amount}
									min={0}
									step={1000}
								/>
								<span class="text-xs text-muted-foreground">円</span>
							</div>
						</div>
					{/if}
				{/each}
			</CardContent>
		</Card>

		<Button class="w-full rounded-lg" onclick={handleSave} disabled={saving}>
			{saving ? '保存中...' : '予算を保存'}
		</Button>
	{/if}
</div>
