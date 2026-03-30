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
	class="fixed bottom-0 left-0 right-0 z-50 border-t border-border bg-background/95 backdrop-blur-sm md:hidden"
	style="padding-bottom: env(safe-area-inset-bottom)"
>
	<div class="flex items-end justify-around px-2 pt-1 pb-1">
		{#each items as item}
			{@const active = page.url.pathname.startsWith(item.href)}
			{#if item.fab}
				<a
					href={item.href}
					class="flex -mt-5 flex-col items-center justify-center rounded-full bg-primary p-3 text-primary-foreground shadow-lg"
				>
					<item.icon class="h-6 w-6" />
				</a>
			{:else}
				<a
					href={item.href}
					class="flex flex-col items-center gap-0.5 px-3 py-1.5 text-xs transition-colors {active
						? 'text-primary'
						: 'text-muted-foreground'}"
				>
					<item.icon class="h-5 w-5" />
					<span>{item.label}</span>
				</a>
			{/if}
		{/each}
	</div>
</nav>
