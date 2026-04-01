import { test, expect } from '@playwright/test';

test.describe('Upload', () => {
	test.beforeEach(async ({ page }) => {
		// DEV mode auto-authenticates
		await page.goto('/upload');
		await page.waitForURL('**/upload', { timeout: 10000 });
		// Wait for the page header to be visible
		await expect(page.getByText('レシート撮影').first()).toBeVisible({ timeout: 10000 });
	});

	test('drop zone is visible with camera prompt', async ({ page }) => {
		// Drop zone should show the camera prompt
		await expect(page.getByText('レシートを撮影またはアップロード')).toBeVisible();
		await expect(page.getByText(/ファイルをドラッグ/)).toBeVisible();

		// The camera/select button should be visible
		await expect(page.getByRole('button', { name: /撮影/ })).toBeVisible();
	});

	test('selecting a file shows preview image', async ({ page }) => {
		// Create a minimal valid PNG image (1x1 red pixel)
		const pngSignature = [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a];
		const ihdr = [
			0x00, 0x00, 0x00, 0x0d, 0x49, 0x48, 0x44, 0x52,
			0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
			0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53, 0xde,
		];
		const idat = [
			0x00, 0x00, 0x00, 0x0c, 0x49, 0x44, 0x41, 0x54,
			0x08, 0xd7, 0x63, 0xf8, 0xcf, 0xc0, 0x00, 0x00,
			0x00, 0x02, 0x00, 0x01, 0xe2, 0x21, 0xbc, 0x33,
		];
		const iend = [
			0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4e, 0x44,
			0xae, 0x42, 0x60, 0x82,
		];
		const buffer = Buffer.from([...pngSignature, ...ihdr, ...idat, ...iend]);

		// The file input is hidden (class="hidden"), but Playwright can still set files on it
		const fileInput = page.locator('input[type="file"]');
		await fileInput.setInputFiles({
			name: 'test-receipt.png',
			mimeType: 'image/png',
			buffer,
		});

		// After selecting a file, a preview image should appear
		await expect(page.locator('img[alt="レシートプレビュー"]')).toBeVisible({ timeout: 5000 });

		// The upload button should be visible
		await expect(page.getByRole('button', { name: /アップロード/ })).toBeVisible();

		// The retake button should also be visible
		await expect(page.getByRole('button', { name: /撮り直し/ })).toBeVisible();
	});
});
