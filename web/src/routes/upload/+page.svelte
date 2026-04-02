<script lang="ts">
	import { Camera, Upload, Check } from 'lucide-svelte';
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import { Select, SelectContent, SelectItem, SelectTrigger } from '$lib/components/ui/select';
	import { getUploadUrl, getReceipt, getCategories, createExpense } from '$lib/api';
	import { goto } from '$app/navigation';

	let fileInput = $state<HTMLInputElement | null>(null);
	let preview = $state<string | null>(null);
	let selectedFile = $state<File | null>(null);
	let uploading = $state(false);
	let processing = $state(false);
	let ocrResult = $state<any>(null);
	let categories = $state<any[]>([]);
	let dragOver = $state(false);
	let error = $state('');

	let editForm = $state({
		store_name: '',
		amount: 0,
		category: '',
		memo: ''
	});

	$effect(() => {
		getCategories()
			.then((data) => {
				categories = Array.isArray(data) ? data : data?.items ?? [];
			})
			.catch(() => {});
	});

	function handleFileSelect(e: Event) {
		const input = e.target as HTMLInputElement;
		if (input.files?.[0]) {
			setFile(input.files[0]);
		}
	}

	function handleDrop(e: DragEvent) {
		e.preventDefault();
		dragOver = false;
		if (e.dataTransfer?.files?.[0]) {
			setFile(e.dataTransfer.files[0]);
		}
	}

	function setFile(file: File) {
		selectedFile = file;
		const reader = new FileReader();
		reader.onload = (e) => {
			preview = e.target?.result as string;
		};
		reader.readAsDataURL(file);
	}

	async function handleUpload() {
		if (!selectedFile) return;
		error = '';
		uploading = true;
		try {
			const { upload_url, receipt_id } = await getUploadUrl(selectedFile.name);
			await fetch(upload_url, {
				method: 'PUT',
				body: selectedFile,
				headers: { 'Content-Type': selectedFile.type }
			});
			uploading = false;
			processing = true;
			await pollReceipt(receipt_id);
		} catch (e: any) {
			error = e.message || 'アップロードに失敗しました';
			uploading = false;
		}
	}

	async function pollReceipt(receiptId: string) {
		const maxAttempts = 30;
		for (let i = 0; i < maxAttempts; i++) {
			await new Promise((r) => setTimeout(r, 2000));
			try {
				const receipt = await getReceipt(receiptId);
				if (receipt.status === 'completed') {
					ocrResult = receipt;
					editForm = {
						store_name: receipt.store_name ?? '',
						amount: receipt.amount ?? 0,
						category: receipt.category ?? '',
						memo: ''
					};
					processing = false;
					return;
				}
				if (receipt.status === 'failed') {
					error = 'OCR処理に失敗しました';
					processing = false;
					return;
				}
			} catch {
				// keep polling
			}
		}
		error = 'タイムアウトしました';
		processing = false;
	}

	async function handleSave() {
		try {
			await createExpense(editForm);
			goto('/expenses');
		} catch (e: any) {
			error = e.message || '保存に失敗しました';
		}
	}

	function reset() {
		preview = null;
		selectedFile = null;
		ocrResult = null;
		error = '';
		uploading = false;
		processing = false;
	}
</script>

<div class="mx-auto max-w-2xl space-y-6 p-4 md:p-6">
	<!-- Page header -->
	<h1 class="text-fluid-xl font-bold tracking-tight animate-fade-up">レシート撮影</h1>

	{#if error}
		<div class="glass rounded-2xl border-destructive/20 bg-destructive/5 p-4 text-fluid-sm text-destructive animate-fade-up">
			{error}
		</div>
	{/if}

	{#if ocrResult}
		<!-- OCR result form -->
		<div class="glass rounded-2xl p-6 animate-fade-up space-y-6">
			<div class="flex items-center gap-3">
				<div class="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
					<Check class="h-5 w-5" />
				</div>
				<h2 class="text-fluid-lg font-bold tracking-tight">読み取り結果を確認</h2>
			</div>
			<form onsubmit={handleSave} class="space-y-4">
				<div class="space-y-1.5">
					<label class="text-fluid-xs text-muted-foreground font-medium block">店名</label>
					<Input bind:value={editForm.store_name} class="rounded-xl" required />
				</div>
				<div class="space-y-1.5">
					<label class="text-fluid-xs text-muted-foreground font-medium block">金額</label>
					<Input type="number" bind:value={editForm.amount} min={1} class="rounded-xl amount" required />
				</div>
				<div class="space-y-1.5">
					<label class="text-fluid-xs text-muted-foreground font-medium block">カテゴリ</label>
					<Select type="single" bind:value={editForm.category}>
						<SelectTrigger class="rounded-xl">
							<span class="text-muted-foreground">{categories.find(c => c.name === editForm.category)?.display_name ?? 'カテゴリを選択'}</span>
						</SelectTrigger>
						<SelectContent class="glass rounded-xl border-glass-border">
							{#each categories as cat}
								<SelectItem value={cat.name}>{cat.icon ?? '📦'} {cat.display_name}</SelectItem>
							{/each}
						</SelectContent>
					</Select>
				</div>
				<div class="space-y-1.5">
					<label class="text-fluid-xs text-muted-foreground font-medium block">メモ</label>
					<Input bind:value={editForm.memo} placeholder="任意" class="rounded-xl" />
				</div>
				<div class="flex gap-3 pt-2">
					<Button type="submit" class="flex-1 rounded-xl gap-2 text-fluid-sm font-semibold">
						<Check class="h-4 w-4" />
						保存する
					</Button>
					<Button type="button" variant="outline" class="rounded-xl text-fluid-sm" onclick={reset}>
						やり直し
					</Button>
				</div>
			</form>
		</div>
	{:else if uploading || processing}
		<!-- Uploading / Processing state -->
		<div class="glass rounded-2xl flex flex-col items-center gap-6 py-16 animate-fade-up">
			{#if uploading}
				<div class="relative">
					<Upload class="h-12 w-12 text-primary animate-bounce" />
				</div>
				<p class="text-fluid-sm text-muted-foreground font-medium">アップロード中...</p>
			{:else}
				<!-- Pulsing receipt icon for OCR processing -->
				<div class="relative flex items-center justify-center">
					<div class="absolute h-20 w-20 rounded-full bg-primary/10 animate-ping" style="animation-duration: 2s;"></div>
					<div class="absolute h-14 w-14 rounded-full bg-primary/15 animate-pulse"></div>
					<span class="relative text-4xl">🧾</span>
				</div>
				<div class="text-center space-y-1">
					<p class="text-fluid-sm text-foreground font-medium">OCR処理中</p>
					<p class="text-fluid-xs text-muted-foreground">レシートを解析しています...</p>
				</div>
			{/if}
		</div>
	{:else}
		<input
			bind:this={fileInput}
			type="file"
			accept="image/*"
			class="hidden"
			onchange={handleFileSelect}
		/>

		{#if preview}
			<!-- Image preview -->
			<div class="space-y-4 animate-fade-up">
				<div class="glass rounded-2xl p-3 overflow-hidden">
					<img src={preview} alt="レシートプレビュー" class="w-full rounded-xl shadow-lg" />
				</div>
				<div class="flex gap-3">
					<Button class="flex-1 rounded-xl gap-2 text-fluid-sm font-semibold" onclick={handleUpload}>
						<Upload class="h-4 w-4" />
						アップロード
					</Button>
					<Button variant="outline" class="rounded-xl text-fluid-sm" onclick={reset}>
						撮り直し
					</Button>
				</div>
			</div>
		{:else}
			<!-- Drop zone -->
			<!-- svelte-ignore a11y_no_static_element_interactions -->
			<div
				class="glass rounded-2xl border-2 border-dashed transition-all duration-300 {dragOver
					? 'border-primary shadow-[0_0_30px_oklch(0.55_0.15_165_/_0.2)]'
					: 'border-glass-border'}"
				ondragover={(e) => {
					e.preventDefault();
					dragOver = true;
				}}
				ondragleave={() => (dragOver = false)}
				ondrop={handleDrop}
			>
				<div class="flex flex-col items-center gap-5 p-10 md:p-14 animate-fade-up">
					<!-- Camera icon with glow -->
					<div class="relative">
						<div class="absolute inset-0 h-16 w-16 rounded-full bg-primary/20 blur-xl"></div>
						<Camera class="relative h-16 w-16 text-primary" />
					</div>

					<div class="text-center space-y-1.5">
						<p class="text-fluid-base font-semibold">レシートを撮影またはアップロード</p>
						<p class="text-fluid-xs text-muted-foreground">
							タップして撮影、またはファイルをドラッグ&ドロップ
						</p>
					</div>

					<!-- Mobile camera button -->
					<Button
						class="w-full max-w-xs rounded-xl gap-2 text-fluid-sm font-semibold bg-gradient-to-r from-primary to-primary/80 shadow-lg shadow-primary/20 md:w-auto md:px-8"
						onclick={() => fileInput?.click()}
					>
						<Camera class="h-5 w-5" />
						撮影・ファイルを選択
					</Button>
				</div>
			</div>
		{/if}
	{/if}
</div>
