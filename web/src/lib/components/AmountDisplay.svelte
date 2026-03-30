<script lang="ts">
	import { formatCurrency } from '$lib/utils';

	interface Props {
		amount: number;
		size?: 'sm' | 'md' | 'lg' | 'xl';
		class?: string;
	}

	let { amount, size = 'md', class: className = '' }: Props = $props();

	const sizeClasses = {
		sm: 'text-lg',
		md: 'text-2xl',
		lg: 'text-3xl',
		xl: 'text-4xl'
	};
</script>

<span
	class="font-semibold tabular-nums tracking-tight {sizeClasses[size]} {className}"
	style="font-feature-settings: 'tnum' 1"
>
	{formatCurrency(amount)}
</span>
