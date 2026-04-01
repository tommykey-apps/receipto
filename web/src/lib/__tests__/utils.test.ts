import { describe, it, expect, vi, afterEach } from 'vitest';
import { formatCurrency, formatDate, getCurrentMonth } from '../utils';

describe('formatCurrency', () => {
	it('formats a regular number with yen symbol and commas', () => {
		expect(formatCurrency(12345)).toBe('¥12,345');
	});

	it('formats zero', () => {
		expect(formatCurrency(0)).toBe('¥0');
	});

	it('formats a large number with commas', () => {
		expect(formatCurrency(1000000)).toBe('¥1,000,000');
	});
});

describe('formatDate', () => {
	it('formats an ISO datetime string to YYYY/MM/DD', () => {
		expect(formatDate('2026-04-01T12:00:00Z')).toBe('2026/04/01');
	});

	it('zero-pads single-digit month and day', () => {
		expect(formatDate('2026-01-05T00:00:00Z')).toBe('2026/01/05');
	});

	it('formats a date-only string to YYYY/MM/DD', () => {
		const result = formatDate('2026-12-25');
		expect(result).toMatch(/^\d{4}\/\d{2}\/\d{2}$/);
	});
});

describe('getCurrentMonth', () => {
	afterEach(() => {
		vi.useRealTimers();
	});

	it('returns a string matching YYYY-MM format', () => {
		const result = getCurrentMonth();
		expect(result).toMatch(/^\d{4}-\d{2}$/);
	});

	it('returns the correct month when time is faked', () => {
		vi.useFakeTimers();
		vi.setSystemTime(new Date('2026-04-15T00:00:00Z'));
		expect(getCurrentMonth()).toBe('2026-04');
	});
});
