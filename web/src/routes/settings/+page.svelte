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

<div class="mx-auto max-w-2xl space-y-6 p-4 md:p-6">
	<!-- Page header -->
	<h1 class="text-fluid-xl font-bold tracking-tight animate-fade-up">設定</h1>

	<div class="stagger space-y-6">
		<!-- Profile section -->
		<div class="glass rounded-2xl p-6">
			<div class="flex items-center gap-4">
				<!-- Avatar circle -->
				<div class="flex items-center justify-center h-12 w-12 rounded-full bg-primary/15 text-primary text-fluid-lg font-bold shrink-0">
					{(auth.user?.email ?? '?')[0].toUpperCase()}
				</div>
				<div class="min-w-0">
					<p class="text-fluid-xs text-muted-foreground mb-0.5">メールアドレス</p>
					<p class="text-fluid-base font-medium truncate">{auth.user?.email ?? '-'}</p>
				</div>
			</div>
		</div>

		<!-- Category management -->
		<div class="glass rounded-2xl p-6">
			<h2 class="text-fluid-base font-semibold tracking-tight mb-4">カテゴリ管理</h2>

			<!-- Category pills -->
			<div class="flex flex-wrap gap-2 mb-5">
				{#each categories as cat}
					<span class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-muted/50 text-fluid-sm card-hover cursor-default">
						<span>{cat.icon ?? '📦'}</span>
						<span>{cat.name}</span>
					</span>
				{/each}
				{#if categories.length === 0}
					<p class="text-fluid-sm text-muted-foreground">カテゴリがありません</p>
				{/if}
			</div>

			<!-- Inline add form -->
			<div class="flex items-center gap-2 pt-4 border-t border-glass-border">
				<Input
					placeholder="🏷"
					bind:value={newCategoryIcon}
					class="w-14 text-center rounded-xl bg-muted/30 border-transparent focus:border-primary/30"
				/>
				<Input
					placeholder="カテゴリ名"
					bind:value={newCategoryName}
					class="flex-1 rounded-xl bg-muted/30 border-transparent focus:border-primary/30"
				/>
				<button
					onclick={handleAddCategory}
					class="flex items-center justify-center h-10 w-10 rounded-xl bg-primary/15 text-primary hover:bg-primary/25 active:scale-[0.95] transition-all shrink-0"
				>
					<Plus class="h-4 w-4" />
				</button>
			</div>
		</div>

		<!-- Theme toggle -->
		<div class="glass rounded-2xl p-6">
			<div class="flex items-center justify-between">
				<div>
					<h2 class="text-fluid-base font-semibold tracking-tight">テーマ</h2>
					<p class="text-fluid-xs text-muted-foreground mt-0.5">
						{isDark ? 'ダークモード' : 'ライトモード'}
					</p>
				</div>
				<!-- Toggle switch -->
				<button
					onclick={toggleTheme}
					class="relative inline-flex h-8 w-14 items-center rounded-full transition-colors duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
					style="background: {isDark ? 'oklch(0.35 0.06 260)' : 'oklch(0.85 0.10 85)'};"
					aria-label="テーマ切替"
				>
					<span
						class="inline-flex h-6 w-6 items-center justify-center rounded-full bg-white shadow-sm transition-transform duration-300"
						style="transform: translateX({isDark ? '1.625rem' : '0.25rem'});"
					>
						{#if isDark}
							<Moon class="h-3.5 w-3.5 text-indigo-500" />
						{:else}
							<Sun class="h-3.5 w-3.5 text-amber-500" />
						{/if}
					</span>
				</button>
			</div>
		</div>

		<!-- Logout -->
		<div class="pt-4">
			<button
				onclick={logout}
				class="flex items-center gap-2 mx-auto text-fluid-sm text-muted-foreground hover:text-foreground transition-colors"
			>
				<LogOut class="h-4 w-4" />
				<span>ログアウト</span>
			</button>
		</div>
	</div>
</div>
