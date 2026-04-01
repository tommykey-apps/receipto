<script lang="ts">
	import { formatCurrency } from '$lib/utils';

	interface Props {
		amount: number;
		size?: 'sm' | 'md' | 'lg' | 'xl' | 'hero';
		class?: string;
		animate?: boolean;
	}

	let { amount, size = 'md', class: className = '', animate = false }: Props = $props();

	const sizeClasses = {
		sm: 'text-lg',
		md: 'text-2xl',
		lg: 'text-fluid-xl',
		xl: 'text-fluid-2xl',
		hero: 'text-fluid-3xl'
	};
</script>

<span
	class="amount {sizeClasses[size]} {animate ? 'animate-count-up' : ''} {className}"
>
	{formatCurrency(amount)}
</span>
