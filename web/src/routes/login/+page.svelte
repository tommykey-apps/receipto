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

<div class="flex min-h-screen flex-col md:flex-row">
	<!-- Brand side (left on desktop, top on mobile) -->
	<div
		class="relative flex flex-col items-center justify-center overflow-hidden px-8 py-12
			md:w-1/2 md:py-0"
		style="background: linear-gradient(145deg, oklch(0.18 0.04 265), oklch(0.13 0.008 60))"
	>
		<div class="relative z-10 text-center md:text-left animate-fade-up">
			<!-- Logo -->
			<div class="mb-6 flex items-center gap-3 justify-center md:justify-start">
				<div
					class="flex h-12 w-12 items-center justify-center rounded-xl text-xl font-bold text-white"
					style="background: linear-gradient(135deg, oklch(0.60 0.14 265), oklch(0.45 0.12 280))"
				>
					R
				</div>
				<span class="text-fluid-xl font-semibold tracking-tight text-white">Receipto</span>
			</div>

			<p class="text-fluid-base text-white/70 max-w-xs">
				レシートを撮るだけ。<br />
				家計をスマートに管理。
			</p>
		</div>
	</div>

	<!-- Form side (right on desktop, bottom on mobile) -->
	<div class="flex flex-1 items-center justify-center p-6 md:p-12">
		<div class="w-full max-w-sm animate-fade-up" style="animation-delay: 100ms">
			<div class="glass rounded-2xl p-8">
				<!-- Mobile-only compact logo -->
				<div class="mb-6 md:hidden flex items-center gap-2 justify-center">
					<div
						class="flex h-8 w-8 items-center justify-center rounded-lg text-sm font-bold text-white"
						style="background: linear-gradient(135deg, oklch(0.60 0.14 265), oklch(0.45 0.12 280))"
					>
						R
					</div>
					<span class="text-fluid-base font-semibold">Receipto</span>
				</div>

				<div class="mb-6 hidden md:block">
					<h2 class="text-fluid-lg font-semibold tracking-tight">おかえりなさい</h2>
					<p class="text-fluid-xs text-muted-foreground mt-1">アカウントにログインしてください</p>
				</div>

				{#if import.meta.env.DEV}
					<div class="mb-4 inline-flex items-center gap-1.5 rounded-full bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
						<span class="h-1.5 w-1.5 rounded-full bg-primary animate-pulse"></span>
						DEVモード
					</div>
				{/if}

				{#if error}
					<Alert variant="destructive" class="mb-4 rounded-xl">
						<AlertDescription>{error}</AlertDescription>
					</Alert>
				{/if}

				{#if showConfirm}
					<form onsubmit={handleConfirm} class="space-y-4">
						<p class="text-fluid-xs text-muted-foreground">
							<span class="font-medium text-foreground">{email}</span> に確認コードを送信しました
						</p>
						<Input
							type="text"
							placeholder="確認コード"
							bind:value={confirmCode}
							required
							class="rounded-xl bg-white/5 border-white/10"
						/>
						<Button
							type="submit"
							class="w-full bg-primary rounded-xl active:scale-[0.98] transition-transform"
							disabled={isLoading}
						>
							{isLoading ? '確認中...' : '確認'}
						</Button>
					</form>
				{:else}
					<Tabs bind:value={activeTab}>
						<TabsList class="grid w-full grid-cols-2 rounded-xl">
							<TabsTrigger value="login" class="rounded-lg">ログイン</TabsTrigger>
							<TabsTrigger value="signup" class="rounded-lg">新規登録</TabsTrigger>
						</TabsList>

						<TabsContent value="login">
							<form onsubmit={handleLogin} class="space-y-4 pt-5">
								<div class="space-y-3">
									<Input
										type="email"
										placeholder="メールアドレス"
										bind:value={email}
										required
										class="rounded-xl bg-white/5 border-white/10"
									/>
									<Input
										type="password"
										placeholder="パスワード"
										bind:value={password}
										required
										class="rounded-xl bg-white/5 border-white/10"
									/>
								</div>
								<Button
									type="submit"
									class="w-full bg-primary rounded-xl active:scale-[0.98] transition-transform"
									disabled={isLoading}
								>
									{isLoading ? 'ログイン中...' : 'ログイン'}
								</Button>
							</form>
						</TabsContent>

						<TabsContent value="signup">
							<form onsubmit={handleSignUp} class="space-y-4 pt-5">
								<div class="space-y-3">
									<Input
										type="email"
										placeholder="メールアドレス"
										bind:value={email}
										required
										class="rounded-xl bg-white/5 border-white/10"
									/>
									<Input
										type="password"
										placeholder="パスワード (8文字以上)"
										bind:value={password}
										minlength={8}
										required
										class="rounded-xl bg-white/5 border-white/10"
									/>
								</div>
								<Button
									type="submit"
									class="w-full bg-primary rounded-xl active:scale-[0.98] transition-transform"
									disabled={isLoading}
								>
									{isLoading ? '登録中...' : 'アカウント作成'}
								</Button>
							</form>
						</TabsContent>
					</Tabs>
				{/if}
			</div>
		</div>
	</div>
</div>
