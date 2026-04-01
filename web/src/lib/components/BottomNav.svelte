<script lang="ts">
	import { page } from '$app/state';
	import { LayoutDashboard, Receipt, Camera, PiggyBank, Settings } from 'lucide-svelte';

	const items = [
		{ href: '/dashboard', label: 'ホーム', icon: LayoutDashboard },
		{ href: '/expenses', label: '支出', icon: Receipt },
		{ href: '/upload', label: '撮影', icon: Camera, fab: true },
		{ href: '/budget', label: '予算', icon: PiggyBank },
		{ href: '/settings', label: '設定', icon: Settings }
	];
</script>

<nav
	class="fixed bottom-0 left-0 right-0 z-50 glass md:hidden"
	style="padding-bottom: env(safe-area-inset-bottom)"
>
	<div class="flex items-end justify-around px-2 pt-1.5 pb-1.5">
		{#each items as item}
			{@const active = page.url.pathname.startsWith(item.href)}
			{#if item.fab}
				<a
					href={item.href}
					class="flex -mt-6 flex-col items-center justify-center rounded-2xl bg-primary p-3.5 text-primary-foreground shadow-lg shadow-primary/25 transition-transform active:scale-95"
				>
					<item.icon class="h-5 w-5" strokeWidth={2.5} />
				</a>
			{:else}
				<a
					href={item.href}
					class="flex flex-col items-center gap-0.5 px-3 py-1.5 transition-all {active
						? 'text-primary'
						: 'text-muted-foreground'}"
				>
					<item.icon class="h-5 w-5 transition-transform {active ? 'scale-110' : ''}" strokeWidth={active ? 2.5 : 1.5} />
					<span class="text-[10px] font-medium">{item.label}</span>
				</a>
			{/if}
		{/each}
	</div>
</nav>
