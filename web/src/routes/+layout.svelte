<script lang="ts">
	import '../app.css';
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { initAuth, getAuthState } from '$lib/stores/auth.svelte';
	import BottomNav from '$lib/components/BottomNav.svelte';
	import Sidebar from '$lib/components/Sidebar.svelte';

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

<svelte:head>
	<title>家計簿</title>
	<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
</svelte:head>

{#if auth.loading}
	<div class="flex min-h-screen items-center justify-center bg-background text-foreground">
		<p class="text-muted-foreground">読み込み中...</p>
	</div>
{:else if needsRedirect}
	<div class="flex min-h-screen items-center justify-center bg-background text-foreground">
		<p class="text-muted-foreground">リダイレクト中...</p>
	</div>
{:else}
	<div class="flex min-h-screen bg-background text-foreground">
		{#if showNav}
			<Sidebar />
		{/if}
		<main class="flex-1 {showNav ? 'pb-20 md:pb-0' : ''}">
			{@render children()}
		</main>
		{#if showNav}
			<BottomNav />
		{/if}
	</div>
{/if}
