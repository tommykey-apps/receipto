<script lang="ts">
	import { goto } from '$app/navigation';
	import { signUp, confirmSignUp, login } from '$lib/auth';
	import { setAuth, getAuthState } from '$lib/stores/auth.svelte';
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '$lib/components/ui/card';
	import { Tabs, TabsContent, TabsList, TabsTrigger } from '$lib/components/ui/tabs';
	import { Alert, AlertDescription } from '$lib/components/ui/alert';

	const auth = getAuthState();

	let email = $state('');
	let password = $state('');
	let confirmCode = $state('');
	let error = $state('');
	let isLoading = $state(false);
	let showConfirm = $state(false);
	let activeTab = $state('login');

	$effect(() => {
		if (auth.isAuthenticated) goto('/dashboard');
	});

	async function handleLogin() {
		error = '';
		isLoading = true;
		try {
			if (import.meta.env.DEV) {
				setAuth({ sub: 'dev-user', email: email || 'dev@local' }, 'dev-token');
				goto('/dashboard');
				return;
			}
			const session = await login(email, password);
			const idToken = session.getIdToken();
			setAuth(
				{ sub: idToken.payload.sub!, email: idToken.payload.email as string },
				session.getAccessToken().getJwtToken()
			);
			goto('/dashboard');
		} catch (e: any) {
			error = e.message || 'ログインに失敗しました';
		} finally {
			isLoading = false;
		}
	}

	async function handleSignUp() {
		error = '';
		isLoading = true;
		try {
			await signUp(email, password);
			showConfirm = true;
		} catch (e: any) {
			error = e.message || 'アカウント作成に失敗しました';
		} finally {
			isLoading = false;
		}
	}

	async function handleConfirm() {
		error = '';
		isLoading = true;
		try {
			await confirmSignUp(email, confirmCode);
			const session = await login(email, password);
			const idToken = session.getIdToken();
			setAuth(
				{ sub: idToken.payload.sub!, email: idToken.payload.email as string },
				session.getAccessToken().getJwtToken()
			);
			goto('/dashboard');
		} catch (e: any) {
			error = e.message || '確認に失敗しました';
		} finally {
			isLoading = false;
		}
	}
</script>

<div class="flex min-h-screen items-center justify-center p-4">
	<Card class="w-full max-w-sm">
		<CardHeader class="text-center">
			<div class="mx-auto mb-2 flex h-12 w-12 items-center justify-center rounded-xl bg-primary text-xl font-bold text-primary-foreground">
				¥
			</div>
			<CardTitle class="text-xl">家計簿</CardTitle>
			<CardDescription>レシート撮影で簡単支出管理</CardDescription>
		</CardHeader>
		<CardContent>
			{#if import.meta.env.DEV}
				<div class="mb-4 rounded-lg bg-primary/10 p-2 text-center text-xs text-primary">
					DEVモード — そのままログインできます
				</div>
			{/if}

			{#if error}
				<Alert variant="destructive" class="mb-4">
					<AlertDescription>{error}</AlertDescription>
				</Alert>
			{/if}

			{#if showConfirm}
				<form onsubmit={handleConfirm} class="space-y-4">
					<p class="text-sm text-muted-foreground">
						{email} に確認コードを送信しました
					</p>
					<Input
						type="text"
						placeholder="確認コード"
						bind:value={confirmCode}
						required
					/>
					<Button type="submit" class="w-full rounded-lg" disabled={isLoading}>
						{isLoading ? '確認中...' : '確認'}
					</Button>
				</form>
			{:else}
				<Tabs bind:value={activeTab}>
					<TabsList class="grid w-full grid-cols-2">
						<TabsTrigger value="login">ログイン</TabsTrigger>
						<TabsTrigger value="signup">新規登録</TabsTrigger>
					</TabsList>

					<TabsContent value="login">
						<form onsubmit={handleLogin} class="space-y-4 pt-4">
							<Input type="email" placeholder="メールアドレス" bind:value={email} required />
							<Input type="password" placeholder="パスワード" bind:value={password} required />
							<Button type="submit" class="w-full rounded-lg" disabled={isLoading}>
								{isLoading ? 'ログイン中...' : 'ログイン'}
							</Button>
						</form>
					</TabsContent>

					<TabsContent value="signup">
						<form onsubmit={handleSignUp} class="space-y-4 pt-4">
							<Input type="email" placeholder="メールアドレス" bind:value={email} required />
							<Input
								type="password"
								placeholder="パスワード (8文字以上)"
								bind:value={password}
								minlength={8}
								required
							/>
							<Button type="submit" class="w-full rounded-lg" disabled={isLoading}>
								{isLoading ? '登録中...' : 'アカウント作成'}
							</Button>
						</form>
					</TabsContent>
				</Tabs>
			{/if}
		</CardContent>
	</Card>
</div>
