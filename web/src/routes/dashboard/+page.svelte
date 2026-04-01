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

<div class="mx-auto max-w-5xl p-4 md:p-6">
	<!-- Header -->
	<div class="mb-6 flex items-end justify-between">
		<div>
			<p class="text-fluid-sm text-muted-foreground">ダッシュボード</p>
			<h1 class="text-fluid-lg font-semibold tracking-tight">支出サマリー</h1>
		</div>
		<a href="/upload">
			<Button class="rounded-xl gap-2 px-5 py-2.5">
				<Camera class="h-4 w-4" />
				レシート撮影
			</Button>
		</a>
	</div>

	{#if loading}
		<!-- Skeleton bento grid -->
		<div class="grid grid-cols-1 gap-4 md:grid-cols-3 md:auto-rows-[180px] stagger">
			<div class="skeleton rounded-2xl md:col-span-2 md:row-span-1 h-[180px]"></div>
			<div class="skeleton rounded-2xl h-[180px]"></div>
			<div class="skeleton rounded-2xl h-[180px]"></div>
			<div class="skeleton rounded-2xl md:col-span-2 h-[180px]"></div>
		</div>
	{:else if !summary && recentExpenses.length === 0}
		<!-- Empty state -->
		<div class="glass rounded-2xl flex flex-col items-center justify-center py-20 px-8 text-center animate-fade-up">
			<div class="mb-6 flex h-20 w-20 items-center justify-center rounded-2xl bg-primary/10">
				<Camera class="h-10 w-10 text-primary" />
			</div>
			<h2 class="text-fluid-lg font-semibold mb-2">まだ記録がありません</h2>
			<p class="text-muted-foreground text-fluid-sm max-w-sm mb-6">
				レシートを撮影するか、手動で支出を追加して家計管理をはじめましょう
			</p>
			<a href="/upload">
				<Button class="rounded-xl gap-2 px-6 py-3">
					<Camera class="h-4 w-4" />
					最初のレシートを撮影
				</Button>
			</a>
		</div>
	{:else}
		<!-- Bento grid -->
		<div class="grid grid-cols-1 gap-4 md:grid-cols-3 md:auto-rows-[180px] stagger">

			<!-- Hero amount — spans 2 cols -->
			<div class="glass rounded-2xl card-hover p-6 md:p-8 flex flex-col justify-between md:col-span-2">
				<p class="text-fluid-sm text-muted-foreground">
					今月は
				</p>
				<div>
					<AmountDisplay amount={totalSpent} size="hero" animate />
					<p class="text-fluid-sm text-muted-foreground mt-1">使いました</p>
				</div>
				<div class="flex items-center gap-4 text-fluid-xs">
					{#if lastMonthDiff !== 0}
						<span
							class="inline-flex items-center gap-1 rounded-lg px-2 py-0.5 {lastMonthDiff > 0
								? 'bg-[oklch(0.75_0.14_85/0.15)] text-[oklch(0.55_0.14_85)]'
								: 'bg-primary/10 text-primary'}"
						>
							{lastMonthDiff > 0 ? '↑' : '↓'}{Math.abs(lastMonthDiff).toFixed(1)}% 先月比
						</span>
					{/if}
					{#if totalBudget > 0}
						<span class="text-muted-foreground">
							残り <span class="amount">{formatCurrency(remaining)}</span>
						</span>
					{/if}
				</div>
			</div>

			<!-- Category donut / breakdown — tall card -->
			{#if categoryBreakdown.length > 0}
				<div class="glass rounded-2xl card-hover p-5 flex flex-col md:row-span-2 overflow-hidden">
					<h3 class="text-fluid-xs font-medium text-muted-foreground mb-3">カテゴリ別</h3>
					<div class="flex-1 space-y-2.5 overflow-y-auto no-scrollbar">
						{#each categoryBreakdown as cat}
							{@const pct = totalSpent > 0 ? (cat.amount / totalSpent * 100) : 0}
							<div class="flex items-center gap-2.5">
								<span class="text-base shrink-0">{cat.icon ?? '📦'}</span>
								<div class="flex-1 min-w-0">
									<div class="flex items-center justify-between mb-0.5">
										<span class="text-fluid-xs truncate">{cat.name}</span>
										<span class="amount text-fluid-xs shrink-0 ml-2">{formatCurrency(cat.amount)}</span>
									</div>
									<div class="h-1 rounded-full bg-muted overflow-hidden">
										<div
											class="h-full rounded-full bg-primary/60 transition-all duration-500"
											style="width: {pct}%"
										></div>
									</div>
								</div>
							</div>
						{/each}
					</div>
				</div>
			{/if}

			<!-- Budget progress -->
			{#if budgets.length > 0}
				<div class="glass rounded-2xl card-hover p-5 flex flex-col {categoryBreakdown.length === 0 ? 'md:col-span-1' : 'md:col-span-2'}">
					<h3 class="text-fluid-xs font-medium text-muted-foreground mb-3">予算消化</h3>
					<div class="flex-1 space-y-3 overflow-y-auto no-scrollbar">
						{#each budgets as b}
							<BudgetProgress
								label={b.category}
								icon={b.icon}
								spent={b.spent ?? 0}
								budget={b.amount ?? 0}
							/>
						{/each}
					</div>
				</div>
			{/if}

			<!-- Recent expenses -->
			<div class="glass rounded-2xl card-hover p-5 flex flex-col md:col-span-{categoryBreakdown.length > 0 ? '2' : '3'} md:row-span-{recentExpenses.length > 3 ? '2' : '1'}">
				<div class="flex items-center justify-between mb-3">
					<h3 class="text-fluid-xs font-medium text-muted-foreground">最近の支出</h3>
					<a href="/expenses" class="text-fluid-xs text-primary hover:underline">すべて見る</a>
				</div>
				{#if recentExpenses.length === 0}
					<div class="flex-1 flex flex-col items-center justify-center text-center py-6">
						<Camera class="h-8 w-8 text-muted-foreground/40 mb-2" />
						<p class="text-fluid-xs text-muted-foreground">
							レシートを撮影して支出を記録しましょう
						</p>
					</div>
				{:else}
					<div class="flex-1 space-y-2 overflow-y-auto no-scrollbar">
						{#each recentExpenses as expense}
							<ExpenseCard {expense} onclick={() => window.location.href = `/expenses`} />
						{/each}
					</div>
				{/if}
			</div>
		</div>
	{/if}
</div>
