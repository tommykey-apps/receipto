import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
	return twMerge(clsx(inputs));
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type WithoutChild<T> = T extends { child?: any } ? Omit<T, 'child'> : T;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type WithoutChildren<T> = T extends { children?: any } ? Omit<T, 'children'> : T;
export type WithoutChildrenOrChild<T> = WithoutChildren<WithoutChild<T>>;
export type WithElementRef<T, U extends HTMLElement = HTMLElement> = T & { ref?: U | null };

export function formatCurrency(amount: number): string {
	return `¥${amount.toLocaleString('ja-JP')}`;
}

export function formatDate(date: string): string {
	const d = new Date(date);
	const y = d.getFullYear();
	const m = String(d.getMonth() + 1).padStart(2, '0');
	const day = String(d.getDate()).padStart(2, '0');
	return `${y}/${m}/${day}`;
}

const CATEGORY_ICONS: Record<string, string> = {
	food: '🍽️',
	transport: '🚃',
	daily: '🛍️',
	entertainment: '🎮',
	utility: '⚡',
	telecom: '📶',
	medical: '🏥',
	clothing: '👕',
	education: '📚',
	other: '🏷️'
};

export function categoryIcon(name: string): string {
	return CATEGORY_ICONS[name] ?? '📦';
}

export function getCurrentMonth(): string {
	const d = new Date();
	const y = d.getFullYear();
	const m = String(d.getMonth() + 1).padStart(2, '0');
	return `${y}-${m}`;
}
