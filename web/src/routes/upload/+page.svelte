<script lang="ts">
	import { Camera, Upload, Check, Loader2 } from 'lucide-svelte';
	import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card';
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
		date: new Date().toISOString().split('T')[0],
		category_id: '',
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
						date: receipt.date ?? new Date().toISOString().split('T')[0],
						category_id: receipt.category_id ?? '',
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

<div class="mx-auto max-w-2xl space-y-4 p-4 md:p-6">
	<h1 class="text-2xl font-bold">レシート撮影</h1>

	{#if error}
		<div class="rounded-lg bg-destructive/10 p-3 text-sm text-destructive">{error}</div>
	{/if}

	{#if ocrResult}
		<Card class="rounded-xl">
			<CardHeader>
				<CardTitle class="text-base">読み取り結果を確認</CardTitle>
			</CardHeader>
			<CardContent>
				<form onsubmit={handleSave} class="space-y-4">
					<div>
						<label class="mb-1 block text-sm text-muted-foreground">店名</label>
						<Input bind:value={editForm.store_name} required />
					</div>
					<div>
						<label class="mb-1 block text-sm text-muted-foreground">金額</label>
						<Input type="number" bind:value={editForm.amount} min={1} required />
					</div>
					<div>
						<label class="mb-1 block text-sm text-muted-foreground">日付</label>
						<Input type="date" bind:value={editForm.date} required />
					</div>
					<div>
						<label class="mb-1 block text-sm text-muted-foreground">カテゴリ</label>
						<Select type="single" bind:value={editForm.category_id}>
							<SelectTrigger>
								<span class="text-muted-foreground">{categories.find(c => c.id === editForm.category_id)?.name ?? 'カテゴリを選択'}</span>
							</SelectTrigger>
							<SelectContent>
								{#each categories as cat}
									<SelectItem value={cat.id}>{cat.icon ?? '📦'} {cat.name}</SelectItem>
								{/each}
							</SelectContent>
						</Select>
					</div>
					<div>
						<label class="mb-1 block text-sm text-muted-foreground">メモ</label>
						<Input bind:value={editForm.memo} placeholder="任意" />
					</div>
					<div class="flex gap-2">
						<Button type="submit" class="flex-1 rounded-lg gap-2">
							<Check class="h-4 w-4" />
							保存する
						</Button>
						<Button type="button" variant="outline" class="rounded-lg" onclick={reset}>
							やり直し
						</Button>
					</div>
				</form>
			</CardContent>
		</Card>
	{:else if uploading || processing}
		<Card class="rounded-xl">
			<CardContent class="flex flex-col items-center gap-4 py-12">
				<Loader2 class="h-8 w-8 animate-spin text-primary" />
				<p class="text-muted-foreground">
					{uploading ? 'アップロード中...' : 'OCR処理中...'}
				</p>
			</CardContent>
		</Card>
	{:else}
		<Card class="rounded-xl">
			<CardContent class="pt-6">
				<input
					bind:this={fileInput}
					type="file"
					accept="image/*"
					capture="environment"
					class="hidden"
					onchange={handleFileSelect}
				/>

				{#if preview}
					<div class="space-y-4">
						<img src={preview} alt="レシートプレビュー" class="w-full rounded-lg" />
						<div class="flex gap-2">
							<Button class="flex-1 rounded-lg gap-2" onclick={handleUpload}>
								<Upload class="h-4 w-4" />
								アップロード
							</Button>
							<Button variant="outline" class="rounded-lg" onclick={reset}>
								撮り直し
							</Button>
						</div>
					</div>
				{:else}
					<!-- svelte-ignore a11y_no_static_element_interactions -->
					<div
						class="flex flex-col items-center gap-4 rounded-xl border-2 border-dashed border-border p-8 transition-colors {dragOver
							? 'border-primary bg-primary/5'
							: ''}"
						ondragover={(e) => {
							e.preventDefault();
							dragOver = true;
						}}
						ondragleave={() => (dragOver = false)}
						ondrop={handleDrop}
					>
						<Camera class="h-12 w-12 text-muted-foreground" />
						<div class="text-center">
							<p class="font-medium">レシートを撮影またはアップロード</p>
							<p class="text-sm text-muted-foreground">
								タップして撮影、またはファイルをドラッグ&ドロップ
							</p>
						</div>
						<Button class="rounded-lg" onclick={() => fileInput?.click()}>
							ファイルを選択
						</Button>
					</div>
				{/if}
			</CardContent>
		</Card>
	{/if}
</div>
