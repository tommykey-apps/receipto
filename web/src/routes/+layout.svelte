<script lang="ts">
	import '../app.css';
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { initAuth, getAuthState } from '$lib/stores/auth.svelte';
	import BottomNav from '$lib/components/BottomNav.svelte';
	import Sidebar from '$lib/components/Sidebar.svelte';
	import { Toaster } from '$lib/components/ui/sonner';

	let { children } = $props();

	const publicPaths = ['/login'];
	const auth = getAuthState();
	const isPublic = $derived(publicPaths.includes(page.url.pathname));
	const needsRedirect = $derived(!auth.loading && !auth.isAuthenticated && !isPublic);
	const showNav = $derived(auth.isAuthenticated && !isPublic);

	$effect(() => {
		initAuth();
	});

	$effect(() => {
		if (needsRedirect) goto('/login');
	});

	$effect(() => {
		document.documentElement.classList.add('dark');
	});
</script>

<Toaster />

<svelte:head>
	<title>Receipto</title>
	<meta name="description" content="レシート撮影で簡単支出管理" />
</svelte:head>

{#if auth.loading}
	<div class="relative z-10 flex min-h-svh items-center justify-center">
		<div class="flex flex-col items-center gap-3 animate-fade-in">
			<div class="h-10 w-10 rounded-xl bg-primary/20 flex items-center justify-center">
				<span class="text-primary text-lg font-bold">R</span>
			</div>
			<div class="h-1 w-16 rounded-full overflow-hidden bg-muted">
				<div class="h-full w-1/2 rounded-full bg-primary animate-pulse"></div>
			</div>
		</div>
	</div>
{:else if needsRedirect}
	<div class="relative z-10 flex min-h-svh items-center justify-center">
		<p class="text-muted-foreground text-fluid-sm animate-fade-in">リダイレクト中...</p>
	</div>
{:else}
	<div class="relative z-10 flex min-h-svh">
		{#if showNav}
			<Sidebar />
		{/if}
		<main class="flex-1 overflow-x-hidden {showNav ? 'pb-20 md:pb-0' : ''}">
			{@render children()}
		</main>
		{#if showNav}
			<BottomNav />
		{/if}
	</div>
{/if}
