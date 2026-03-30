<script lang="ts">
	import { onMount } from 'svelte';
	import { Plus } from 'lucide-svelte';
	import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '$lib/components/ui/dialog';
	import { Select, SelectContent, SelectItem, SelectTrigger } from '$lib/components/ui/select';
	import ExpenseCard from '$lib/components/ExpenseCard.svelte';
	import { getExpenses, getCategories, createExpense, deleteExpense } from '$lib/api';
	import { getCurrentMonth } from '$lib/utils';

	let expenses = $state<any[]>([]);
	let categories = $state<any[]>([]);
	let loading = $state(true);
	let selectedMonth = $state(getCurrentMonth());
	let selectedCategory = $state('');
	let dialogOpen = $state(false);

	let newExpense = $state({
		store_name: '',
		amount: 0,
		date: new Date().toISOString().split('T')[0],
		category_id: '',
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
		if (!newExpense.store_name || !newExpense.amount) return;
		try {
			await createExpense(newExpense);
			dialogOpen = false;
			newExpense = {
				store_name: '',
				amount: 0,
				date: new Date().toISOString().split('T')[0],
				category_id: '',
				memo: ''
			};
			await loadData();
		} catch {
			// TODO: error handling
		}
	}

	async function handleDelete(id: string) {
		await deleteExpense(id);
		await loadData();
	}

	function handleMonthChange() {
		loadData();
	}

	function handleCategoryChange() {
		loadData();
	}

	let editingExpense = $state<any>(null);
</script>

<div class="mx-auto max-w-2xl space-y-4 p-4 md:p-6">
	<div class="flex items-center justify-between">
		<h1 class="text-2xl font-bold">支出一覧</h1>
		<Dialog bind:open={dialogOpen}>
			<DialogTrigger>
				{#snippet child({ props })}
					<Button {...props} class="rounded-lg gap-2">
						<Plus class="h-4 w-4" />
						追加
					</Button>
				{/snippet}
			</DialogTrigger>
			<DialogContent>
				<DialogHeader>
					<DialogTitle>支出を追加</DialogTitle>
				</DialogHeader>
				<form onsubmit={handleCreate} class="space-y-4">
					<Input placeholder="店名" bind:value={newExpense.store_name} required />
					<Input type="number" placeholder="金額" bind:value={newExpense.amount} min={1} required />
					<Input type="date" bind:value={newExpense.date} required />
					<Select type="single" bind:value={newExpense.category_id}>
						<SelectTrigger>
							<span class="text-muted-foreground">{categories.find(c => c.id === newExpense.category_id)?.name ?? 'カテゴリを選択'}</span>
						</SelectTrigger>
						<SelectContent>
							{#each categories as cat}
								<SelectItem value={cat.id}>{cat.icon ?? '📦'} {cat.name}</SelectItem>
							{/each}
						</SelectContent>
					</Select>
					<Input placeholder="メモ (任意)" bind:value={newExpense.memo} />
					<Button type="submit" class="w-full rounded-lg">追加する</Button>
				</form>
			</DialogContent>
		</Dialog>
	</div>

	<div class="flex gap-2">
		<Input
			type="month"
			bind:value={selectedMonth}
			onchange={handleMonthChange}
			class="w-40"
		/>
		<Select type="single" bind:value={selectedCategory} onValueChange={handleCategoryChange}>
			<SelectTrigger class="w-40">
				<span class="text-muted-foreground">{categories.find(c => c.id === selectedCategory)?.name ?? '全カテゴリ'}</span>
			</SelectTrigger>
			<SelectContent>
				<SelectItem value="">すべて</SelectItem>
				{#each categories as cat}
					<SelectItem value={cat.id}>{cat.icon ?? '📦'} {cat.name}</SelectItem>
				{/each}
			</SelectContent>
		</Select>
	</div>

	{#if loading}
		<div class="flex items-center justify-center py-12">
			<p class="text-muted-foreground">読み込み中...</p>
		</div>
	{:else if expenses.length === 0}
		<Card class="rounded-xl">
			<CardContent class="py-12 text-center">
				<p class="text-muted-foreground">支出がありません</p>
			</CardContent>
		</Card>
	{:else}
		<div class="space-y-2">
			{#each expenses as expense}
				<ExpenseCard {expense} />
			{/each}
		</div>
	{/if}
</div>
