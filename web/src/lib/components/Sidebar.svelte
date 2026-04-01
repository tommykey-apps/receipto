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

<aside class="hidden md:flex md:w-56 md:flex-col glass border-r-0 min-h-svh border-r border-glass-border">
	<div class="flex items-center gap-2.5 px-5 py-5">
		<div class="h-8 w-8 rounded-lg bg-gradient-to-br from-primary to-primary/70 flex items-center justify-center text-primary-foreground font-bold text-sm shadow-sm shadow-primary/20">
			R
		</div>
		<span class="text-sm font-semibold tracking-tight">Receipto</span>
	</div>

	<nav class="flex-1 px-3 py-2 space-y-0.5">
		{#each items as item}
			{@const active = page.url.pathname.startsWith(item.href)}
			<a
				href={item.href}
				class="group flex items-center gap-2.5 rounded-xl px-3 py-2 text-[13px] font-medium transition-all {active
					? 'bg-primary/10 text-primary'
					: 'text-muted-foreground hover:text-foreground hover:bg-muted'}"
			>
				<item.icon class="h-[18px] w-[18px] transition-transform group-hover:scale-105" strokeWidth={active ? 2.5 : 1.5} />
				{item.label}
			</a>
		{/each}
	</nav>

	<div class="border-t border-border/50 px-3 py-3">
		<button
			onclick={logout}
			class="flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-[13px] font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-all"
		>
			<LogOut class="h-[18px] w-[18px]" strokeWidth={1.5} />
			ログアウト
		</button>
	</div>
</aside>
