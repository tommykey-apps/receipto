import { test, expect } from '@playwright/test';

const API_BASE = 'http://localhost:8080';

/** Helper: seed an expense via the API directly */
async function seedExpense(
	request: any,
	data: { amount: number; category?: string; store_name?: string }
) {
	const payload = {
		amount: data.amount,
		category: data.category ?? 'food',
		store_name: data.store_name ?? 'テスト店',
		memo: '',
	};
	const res = await request.post(`${API_BASE}/api/expenses`, {
		headers: { 'x-user-id': 'dev-user', 'Content-Type': 'application/json' },
		data: payload,
	});
	expect(res.ok()).toBeTruthy();
	return res.json();
}

test.describe('Dashboard', () => {
	test('auto-login in DEV mode redirects to dashboard', async ({ page }) => {
		await page.goto('/login');
		// DEV mode auto-authenticates, should redirect to /dashboard
		await page.waitForURL('**/dashboard', { timeout: 15000 });
		await expect(page.getByRole('heading', { name: '支出サマリー' })).toBeVisible({ timeout: 5000 });
	});

	test('seeded expense amount is displayed on dashboard', async ({ page, request }) => {
		// Seed an expense with a unique amount
		await seedExpense(request, { amount: 7777, store_name: 'ダッシュボードテスト店' });

		await page.goto('/dashboard');
		await page.waitForURL('**/dashboard', { timeout: 10000 });
		await expect(page.getByRole('heading', { name: '支出サマリー' })).toBeVisible({ timeout: 10000 });

		// The total should include our 7,777 amount (formatted with commas)
		await expect(page.getByText(/7,777/)).toBeVisible({ timeout: 10000 });
	});

	test('recent expenses section exists when expenses are seeded', async ({ page, request }) => {
		await seedExpense(request, { amount: 2000, category: 'food', store_name: 'ランチ店' });

		await page.goto('/dashboard');
		await page.waitForURL('**/dashboard', { timeout: 10000 });
		await expect(page.getByRole('heading', { name: '支出サマリー' })).toBeVisible({ timeout: 10000 });

		// Should show the recent expenses section
		await expect(page.getByText('最近の支出')).toBeVisible({ timeout: 10000 });
	});
});
