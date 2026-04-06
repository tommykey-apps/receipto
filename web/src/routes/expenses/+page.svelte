<script lang="ts">
	import { onMount } from 'svelte';
	import { Plus } from 'lucide-svelte';
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '$lib/components/ui/dialog';
	import { Select, SelectContent, SelectItem, SelectTrigger } from '$lib/components/ui/select';
	import ExpenseCard from '$lib/components/ExpenseCard.svelte';
	import { toast } from 'svelte-sonner';
	import { getExpenses, getCategories, createExpense, deleteExpense } from '$lib/api';
	import { getCurrentMonth, formatCurrency } from '$lib/utils';

	let expenses = $state<any[]>([]);
	let categories = $state<any[]>([]);
	let loading = $state(true);
	let selectedMonth = $state(getCurrentMonth());
	let selectedCategory = $state('');
	let dialogOpen = $state(false);

	let newExpense = $state({
		store_name: '',
		amount: 0,
		category: '',
		memo: ''
	});

	async function loadData() {
		loading = true;
		try {
			const [expData, catData] = await Promise.all([
				getExpenses(selectedMonth, selectedCategory || undefined).catch(() => []),
				getCategories().catch(() => [])
			]);
			expenses = Array.isArray(expData) ? expData : expData?.items ?? [];
			categories = Array.isArray(catData) ? catData : catData?.items ?? [];
		} finally {
			loading = false;
		}
	}

	onMount(loadData);

	async function handleCreate() {
		if (!newExpense.store_name || !newExpense.amount || !newExpense.category) return;
		try {
			await createExpense(newExpense);
			dialogOpen = false;
			newExpense = {
				store_name: '',
				amount: 0,
				category: '',
				memo: ''
			};
			await loadData();
		} catch {
			// TODO: error handling
		}
	}

	function handleDelete(id: string) {
		const backup = expenses.find(e => e.id === id);
		if (!backup) return;

		// Optimistic removal
		expenses = expenses.filter(e => e.id !== id);

		let undone = false;
		toast(`${backup.store_name} ${formatCurrency(backup.amount)} を削除しました`, {
			action: {
				label: '元に戻す',
				onClick: () => {
					undone = true;
					expenses = [...expenses, backup].sort((a, b) => b.created_at.localeCompare(a.created_at));
				}
			},
			duration: 8000,
			onDismiss: async () => {
				if (!undone) {
					await deleteExpense(id);
				}
			},
		});
	}

	function handleMonthChange() {
		loadData();
	}

	function handleCategoryChange() {
		loadData();
	}

	let editingExpense = $state<any>(null);
</script>

<div class="mx-auto max-w-2xl space-y-6 p-4 md:p-6">
	<!-- Page header -->
	<div class="flex items-center justify-between animate-fade-up">
		<h1 class="text-fluid-xl font-bold tracking-tight">支出一覧</h1>
		<Dialog bind:open={dialogOpen}>
			<DialogTrigger>
				{#snippet child({ props })}
					<Button {...props} class="rounded-xl gap-2 shadow-sm">
						<Plus class="h-4 w-4" />
						<span class="text-fluid-sm">追加</span>
					</Button>
				{/snippet}
			</DialogTrigger>
			<DialogContent class="glass rounded-2xl border-glass-border">
				<DialogHeader>
					<DialogTitle class="text-fluid-lg font-bold tracking-tight">支出を追加</DialogTitle>
				</DialogHeader>
				<form onsubmit={handleCreate} class="space-y-4">
					<div class="space-y-1.5">
						<label class="text-fluid-xs text-muted-foreground font-medium">店名</label>
						<Input placeholder="店名を入力" bind:value={newExpense.store_name} class="rounded-xl" required />
					</div>
					<div class="space-y-1.5">
						<label class="text-fluid-xs text-muted-foreground font-medium">金額</label>
						<Input type="number" placeholder="0" bind:value={newExpense.amount} min={1} class="rounded-xl amount" required />
					</div>
					<div class="space-y-1.5">
						<label class="text-fluid-xs text-muted-foreground font-medium">カテゴリ</label>
						<Select type="single" bind:value={newExpense.category}>
							<SelectTrigger class="rounded-xl">
								<span class="text-muted-foreground">{categories.find(c => c.name === newExpense.category)?.display_name ?? 'カテゴリを選択'}</span>
							</SelectTrigger>
							<SelectContent class="glass rounded-xl border-glass-border">
								{#each categories as cat}
									<SelectItem value={cat.name}>{cat.icon ?? '📦'} {cat.display_name}</SelectItem>
								{/each}
							</SelectContent>
						</Select>
					</div>
					<div class="space-y-1.5">
						<label class="text-fluid-xs text-muted-foreground font-medium">メモ</label>
						<Input placeholder="任意" bind:value={newExpense.memo} class="rounded-xl" />
					</div>
					<Button type="submit" class="w-full rounded-xl text-fluid-sm font-semibold mt-2">追加する</Button>
				</form>
			</DialogContent>
		</Dialog>
	</div>

	<!-- Filter bar -->
	<div class="glass rounded-2xl p-3 flex items-center gap-3 animate-fade-up" style="animation-delay: 80ms;">
		<Input
			type="month"
			bind:value={selectedMonth}
			onchange={handleMonthChange}
			class="w-40 rounded-xl bg-transparent border-glass-border"
		/>
		<Select type="single" bind:value={selectedCategory} onValueChange={handleCategoryChange}>
			<SelectTrigger class="w-40 rounded-xl bg-transparent border-glass-border">
				<span class="text-fluid-xs text-muted-foreground">{categories.find(c => c.name === selectedCategory)?.display_name ?? '全カテゴリ'}</span>
			</SelectTrigger>
			<SelectContent class="glass rounded-xl border-glass-border">
				<SelectItem value="">すべて</SelectItem>
				{#each categories as cat}
					<SelectItem value={cat.name}>{cat.icon ?? '📦'} {cat.display_name}</SelectItem>
				{/each}
			</SelectContent>
		</Select>
	</div>

	<!-- Content area -->
	{#if loading}
		<div class="space-y-3">
			{#each Array(5) as _}
				<div class="glass rounded-2xl p-4 flex items-center gap-3">
					<div class="skeleton h-10 w-10 rounded-xl shrink-0"></div>
					<div class="flex-1 space-y-2">
						<div class="skeleton h-4 w-2/3 rounded-lg"></div>
						<div class="skeleton h-3 w-1/3 rounded-lg"></div>
					</div>
					<div class="skeleton h-5 w-20 rounded-lg"></div>
				</div>
			{/each}
		</div>
	{:else if expenses.length === 0}
		<div class="glass rounded-2xl py-16 text-center animate-fade-up">
			<div class="flex justify-center items-center gap-3 mb-6 opacity-30">
				<div class="text-5xl -rotate-12">🧾</div>
				<div class="text-4xl rotate-6 translate-y-2">💸</div>
				<div class="text-5xl -rotate-6">📝</div>
			</div>
			<p class="text-fluid-base font-medium text-muted-foreground mb-1">支出がありません</p>
			<p class="text-fluid-xs text-muted-foreground/60">右上の「追加」ボタンから支出を記録しましょう</p>
		</div>
	{:else}
		<div class="space-y-2 stagger">
			{#each expenses as expense (expense.id)}
				<ExpenseCard {expense} ondelete={handleDelete} />
			{/each}
		</div>
	{/if}
</div>
