<script lang="ts">
	import { onMount } from 'svelte';
	import { Camera } from 'lucide-svelte';
	import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { Button } from '$lib/components/ui/button';
	import AmountDisplay from '$lib/components/AmountDisplay.svelte';
	import ExpenseCard from '$lib/components/ExpenseCard.svelte';
	import BudgetProgress from '$lib/components/BudgetProgress.svelte';
	import { getMonthlySummary, getExpenses, getBudgets } from '$lib/api';
	import { getCurrentMonth, formatCurrency } from '$lib/utils';

	let summary = $state<any>(null);
	let recentExpenses = $state<any[]>([]);
	let budgets = $state<any[]>([]);
	let loading = $state(true);

	onMount(async () => {
		try {
			const month = getCurrentMonth();
			const [summaryData, expensesData, budgetsData] = await Promise.all([
				getMonthlySummary(month).catch(() => null),
				getExpenses(month).catch(() => []),
				getBudgets(month).catch(() => [])
			]);
			summary = summaryData;
			recentExpenses = (Array.isArray(expensesData) ? expensesData : expensesData?.items ?? []).slice(0, 5);
			budgets = Array.isArray(budgetsData) ? budgetsData : budgetsData?.items ?? [];
		} finally {
			loading = false;
		}
	});

	const totalSpent = $derived(summary?.total_spent ?? 0);
	const lastMonthDiff = $derived(summary?.last_month_diff ?? 0);
	const totalBudget = $derived(summary?.total_budget ?? 0);
	const remaining = $derived(totalBudget - totalSpent);
	const categoryBreakdown = $derived(summary?.by_category ?? []);
</script>

<div class="mx-auto max-w-2xl space-y-6 p-4 md:p-6">
	<div class="flex items-center justify-between">
		<h1 class="text-2xl font-bold">ダッシュボード</h1>
		<a href="/upload">
			<Button class="rounded-lg gap-2">
				<Camera class="h-4 w-4" />
				レシート撮影
			</Button>
		</a>
	</div>

	{#if loading}
		<div class="flex items-center justify-center py-12">
			<p class="text-muted-foreground">読み込み中...</p>
		</div>
	{:else}
		<Card class="rounded-xl">
			<CardContent class="pt-6">
				<p class="text-sm text-muted-foreground">今月の支出</p>
				<AmountDisplay amount={totalSpent} size="xl" />
				<div class="mt-2 flex items-center gap-4 text-sm">
					{#if lastMonthDiff !== 0}
						<span class={lastMonthDiff > 0 ? 'text-destructive' : 'text-primary'}>
							{lastMonthDiff > 0 ? '+' : ''}{lastMonthDiff.toFixed(1)}% 先月比
						</span>
					{/if}
					{#if totalBudget > 0}
						<span class="text-muted-foreground">
							残り {formatCurrency(remaining)}
						</span>
					{/if}
				</div>
			</CardContent>
		</Card>

		{#if categoryBreakdown.length > 0}
			<Card class="rounded-xl">
				<CardHeader>
					<CardTitle class="text-base">カテゴリ別</CardTitle>
				</CardHeader>
				<CardContent class="space-y-3">
					{#each categoryBreakdown as cat}
						<div class="flex items-center justify-between">
							<div class="flex items-center gap-2">
								<span>{cat.icon ?? '📦'}</span>
								<span class="text-sm">{cat.name}</span>
							</div>
							<span class="text-sm font-medium tabular-nums">
								{formatCurrency(cat.amount)}
							</span>
						</div>
					{/each}
				</CardContent>
			</Card>
		{/if}

		{#if budgets.length > 0}
			<Card class="rounded-xl">
				<CardHeader>
					<CardTitle class="text-base">予算消化</CardTitle>
				</CardHeader>
				<CardContent class="space-y-4">
					{#each budgets as b}
						<BudgetProgress
							label={b.category_name ?? b.category_id}
							icon={b.icon}
							spent={b.spent ?? 0}
							budget={b.amount ?? 0}
						/>
					{/each}
				</CardContent>
			</Card>
		{/if}

		<Card class="rounded-xl">
			<CardHeader>
				<CardTitle class="text-base">最近の支出</CardTitle>
			</CardHeader>
			<CardContent>
				{#if recentExpenses.length === 0}
					<p class="py-4 text-center text-sm text-muted-foreground">
						まだ支出がありません
					</p>
				{:else}
					<div class="space-y-2">
						{#each recentExpenses as expense}
							<ExpenseCard {expense} onclick={() => window.location.href = `/expenses`} />
						{/each}
					</div>
				{/if}
			</CardContent>
		</Card>
	{/if}
</div>
