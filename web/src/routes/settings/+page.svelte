<script lang="ts">
	import { onMount } from 'svelte';
	import { Plus, Trash2, Sun, Moon, LogOut } from 'lucide-svelte';
	import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import { Separator } from '$lib/components/ui/separator';
	import { getAuthState, logout } from '$lib/stores/auth.svelte';
	import { getCategories, createCategory } from '$lib/api';

	const auth = getAuthState();

	let categories = $state<any[]>([]);
	let newCategoryName = $state('');
	let newCategoryIcon = $state('');
	let isDark = $state(true);

	onMount(async () => {
		isDark = document.documentElement.classList.contains('dark');
		try {
			const data = await getCategories();
			categories = Array.isArray(data) ? data : data?.items ?? [];
		} catch {
			// ignore
		}
	});

	function toggleTheme() {
		isDark = !isDark;
		document.documentElement.classList.toggle('dark', isDark);
	}

	async function handleAddCategory() {
		if (!newCategoryName.trim()) return;
		try {
			await createCategory({
				name: newCategoryName.trim(),
				icon: newCategoryIcon.trim() || undefined
			});
			const data = await getCategories();
			categories = Array.isArray(data) ? data : data?.items ?? [];
			newCategoryName = '';
			newCategoryIcon = '';
		} catch {
			// ignore
		}
	}
</script>

<div class="mx-auto max-w-2xl space-y-4 p-4 md:p-6">
	<h1 class="text-2xl font-bold">設定</h1>

	<Card class="rounded-xl">
		<CardHeader>
			<CardTitle class="text-base">プロフィール</CardTitle>
		</CardHeader>
		<CardContent>
			<p class="text-sm text-muted-foreground">メールアドレス</p>
			<p class="font-medium">{auth.user?.email ?? '-'}</p>
		</CardContent>
	</Card>

	<Card class="rounded-xl">
		<CardHeader>
			<CardTitle class="text-base">カテゴリ管理</CardTitle>
		</CardHeader>
		<CardContent class="space-y-3">
			{#each categories as cat}
				<div class="flex items-center justify-between rounded-lg bg-muted/50 px-3 py-2">
					<div class="flex items-center gap-2">
						<span>{cat.icon ?? '📦'}</span>
						<span class="text-sm">{cat.name}</span>
					</div>
				</div>
			{/each}

			<Separator />

			<div class="flex gap-2">
				<Input
					placeholder="アイコン"
					bind:value={newCategoryIcon}
					class="w-16 text-center"
				/>
				<Input
					placeholder="カテゴリ名"
					bind:value={newCategoryName}
					class="flex-1"
				/>
				<Button variant="outline" size="icon" class="rounded-lg" onclick={handleAddCategory}>
					<Plus class="h-4 w-4" />
				</Button>
			</div>
		</CardContent>
	</Card>

	<Card class="rounded-xl">
		<CardHeader>
			<CardTitle class="text-base">テーマ</CardTitle>
		</CardHeader>
		<CardContent>
			<Button variant="outline" class="w-full rounded-lg gap-2" onclick={toggleTheme}>
				{#if isDark}
					<Sun class="h-4 w-4" />
					ライトモードに切替
				{:else}
					<Moon class="h-4 w-4" />
					ダークモードに切替
				{/if}
			</Button>
		</CardContent>
	</Card>

	<Button variant="destructive" class="w-full rounded-lg gap-2" onclick={logout}>
		<LogOut class="h-4 w-4" />
		ログアウト
	</Button>
</div>
