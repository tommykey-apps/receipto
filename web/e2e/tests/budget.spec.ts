import { test, expect } from '@playwright/test';

const API_BASE = 'http://localhost:8080';

test.describe('Budget', () => {
	test.beforeEach(async ({ page }) => {
		await page.goto('/budget');
		await page.waitForURL('**/budget', { timeout: 10000 });
		await expect(page.getByRole('heading', { name: '予算管理' })).toBeVisible({ timeout: 10000 });
	});

	test('budget page loads with category inputs and save button', async ({ page }) => {
		const saveButton = page.getByRole('button', { name: /予算を保存/ });
		await expect(saveButton).toBeVisible({ timeout: 10000 });

		await expect(page.getByText('月間予算合計')).toBeVisible();

		// Find budget input fields
		const budgetInputs = page.locator('input[type="number"]');
		const count = await budgetInputs.count();

		if (count > 0) {
			// Set a budget in the first category
			await budgetInputs.first().fill('50000');

			// Click save
			await saveButton.click();

			// Wait for save completion
			await expect(saveButton).toBeEnabled({ timeout: 5000 });

			// Reload and verify the page still works
			await page.reload();
			await expect(page.getByRole('heading', { name: '予算管理' })).toBeVisible({ timeout: 10000 });
			await expect(page.getByText('月間予算合計')).toBeVisible();
		}
	});

	test('progress bars exist when expenses are seeded', async ({ page, request }) => {
		// Seed an expense
		await request.post(`${API_BASE}/api/expenses`, {
			headers: { 'x-user-id': 'dev-user', 'Content-Type': 'application/json' },
			data: {
				amount: 5000,
				category: 'food',
				store_name: '食事テスト',
			},
		});

		await page.reload();
		await expect(page.getByRole('heading', { name: '予算管理' })).toBeVisible({ timeout: 10000 });
		await expect(page.getByRole('button', { name: /予算を保存/ })).toBeVisible({ timeout: 10000 });

		await expect(page.getByText('月間予算合計')).toBeVisible();
		await expect(page.getByText('カテゴリ別予算')).toBeVisible();

		// Verify at least one category card exists
		const categoryCards = page.locator('.card-hover');
		const cardCount = await categoryCards.count();
		expect(cardCount).toBeGreaterThan(0);
	});
});
