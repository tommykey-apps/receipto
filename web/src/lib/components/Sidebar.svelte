<script lang="ts">
	import { page } from '$app/state';
	import { LayoutDashboard, Receipt, Camera, PiggyBank, Settings, LogOut } from 'lucide-svelte';
	import { logout } from '$lib/stores/auth.svelte';

	const items = [
		{ href: '/dashboard', label: 'ダッシュボード', icon: LayoutDashboard },
		{ href: '/expenses', label: '支出一覧', icon: Receipt },
		{ href: '/upload', label: 'レシート撮影', icon: Camera },
		{ href: '/budget', label: '予算管理', icon: PiggyBank },
		{ href: '/settings', label: '設定', icon: Settings }
	];
</script>

<aside class="hidden md:flex md:w-60 md:flex-col md:border-r md:border-border bg-sidebar min-h-screen">
	<div class="flex items-center gap-2 px-6 py-5 border-b border-border">
		<div class="h-8 w-8 rounded-lg bg-primary flex items-center justify-center text-primary-foreground font-bold text-sm">
			¥
		</div>
		<span class="text-lg font-semibold text-sidebar-foreground">家計簿</span>
	</div>

	<nav class="flex-1 px-3 py-4 space-y-1">
		{#each items as item}
			{@const active = page.url.pathname.startsWith(item.href)}
			<a
				href={item.href}
				class="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors {active
					? 'bg-primary/10 text-primary'
					: 'text-sidebar-foreground hover:bg-sidebar-accent'}"
			>
				<item.icon class="h-5 w-5" />
				{item.label}
			</a>
		{/each}
	</nav>

	<div class="border-t border-border px-3 py-4">
		<button
			onclick={logout}
			class="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-sidebar-accent transition-colors"
		>
			<LogOut class="h-5 w-5" />
			ログアウト
		</button>
	</div>
</aside>
