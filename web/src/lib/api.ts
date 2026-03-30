import { getAuthState } from '$lib/stores/auth.svelte';

async function authFetch(path: string, options: RequestInit = {}): Promise<Response> {
	const auth = getAuthState();
	const headers = new Headers(options.headers);
	if (auth.token) {
		headers.set('Authorization', `Bearer ${auth.token}`);
	}
	headers.set('Content-Type', 'application/json');
	const res = await fetch(path, { ...options, headers });
	if (!res.ok) {
		throw new Error(`API error: ${res.status} ${res.statusText}`);
	}
	return res;
}

export async function getExpenses(month?: string, category?: string) {
	const params = new URLSearchParams();
	if (month) params.set('month', month);
	if (category) params.set('category', category);
	const query = params.toString();
	const res = await authFetch(`/api/expenses${query ? `?${query}` : ''}`);
	return res.json();
}

export async function createExpense(data: {
	store_name: string;
	amount: number;
	date: string;
	category_id: string;
	memo?: string;
}) {
	const res = await authFetch('/api/expenses', {
		method: 'POST',
		body: JSON.stringify(data)
	});
	return res.json();
}

export async function updateExpense(
	id: string,
	data: {
		store_name?: string;
		amount?: number;
		date?: string;
		category_id?: string;
		memo?: string;
	}
) {
	const res = await authFetch(`/api/expenses/${id}`, {
		method: 'PUT',
		body: JSON.stringify(data)
	});
	return res.json();
}

export async function deleteExpense(id: string) {
	await authFetch(`/api/expenses/${id}`, { method: 'DELETE' });
}

export async function getCategories() {
	const res = await authFetch('/api/categories');
	return res.json();
}

export async function createCategory(data: { name: string; icon?: string; color?: string }) {
	const res = await authFetch('/api/categories', {
		method: 'POST',
		body: JSON.stringify(data)
	});
	return res.json();
}

export async function getBudgets(month?: string) {
	const params = month ? `?month=${month}` : '';
	const res = await authFetch(`/api/budgets${params}`);
	return res.json();
}

export async function updateBudgets(data: { month: string; budgets: Record<string, number> }) {
	const res = await authFetch('/api/budgets', {
		method: 'PUT',
		body: JSON.stringify(data)
	});
	return res.json();
}

export async function getMonthlySummary(month: string) {
	const res = await authFetch(`/api/summary/monthly?month=${month}`);
	return res.json();
}

export async function getTrend(months: number) {
	const res = await authFetch(`/api/summary/trend?months=${months}`);
	return res.json();
}

export async function getUploadUrl(filename: string) {
	const res = await authFetch('/api/receipts/upload', {
		method: 'POST',
		body: JSON.stringify({ filename })
	});
	return res.json();
}

export async function getReceipt(id: string) {
	const res = await authFetch(`/api/receipts/${id}`);
	return res.json();
}
