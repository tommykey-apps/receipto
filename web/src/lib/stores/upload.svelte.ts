import { getReceipt } from '$lib/api';

type UploadStatus = 'idle' | 'uploading' | 'processing' | 'completed' | 'failed';

interface UploadState {
	receiptId: string | null;
	status: UploadStatus;
	result: any;
	error: string;
}

const STORAGE_KEY = 'receipt_upload';

const initial: UploadState = { receiptId: null, status: 'idle', result: null, error: '' };

function loadFromStorage(): UploadState {
	if (typeof sessionStorage === 'undefined') return initial;
	try {
		const raw = sessionStorage.getItem(STORAGE_KEY);
		return raw ? JSON.parse(raw) : initial;
	} catch {
		return initial;
	}
}

function saveToStorage(state: UploadState) {
	if (typeof sessionStorage === 'undefined') return;
	if (state.status === 'idle') {
		sessionStorage.removeItem(STORAGE_KEY);
	} else {
		sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
	}
}

let state = $state<UploadState>(loadFromStorage());
let pollTimer: ReturnType<typeof setTimeout> | null = null;

export function getUploadState() {
	return {
		get receiptId() { return state.receiptId; },
		get status() { return state.status; },
		get result() { return state.result; },
		get error() { return state.error; }
	};
}

function update(partial: Partial<UploadState>) {
	Object.assign(state, partial);
	saveToStorage(state);
}

export function setUploading() {
	update({ status: 'uploading', error: '' });
}

export function startPolling(receiptId: string) {
	update({ receiptId, status: 'processing', error: '' });
	poll(receiptId, 2000);
}

function poll(receiptId: string, delay: number) {
	pollTimer = setTimeout(async () => {
		try {
			const receipt = await getReceipt(receiptId);
			if (receipt.status === 'completed') {
				update({ status: 'completed', result: receipt });
				return;
			}
			if (receipt.status === 'failed') {
				update({ status: 'failed', error: 'OCR処理に失敗しました' });
				return;
			}
		} catch {
			// keep polling
		}
		const nextDelay = Math.min(delay * 1.5, 15000);
		poll(receiptId, nextDelay);
	}, delay);
}

export function resumePollingIfNeeded() {
	if (state.status === 'processing' && state.receiptId && !pollTimer) {
		poll(state.receiptId, 2000);
	}
}

export function resetUpload() {
	if (pollTimer) {
		clearTimeout(pollTimer);
		pollTimer = null;
	}
	Object.assign(state, initial);
	saveToStorage(state);
}
