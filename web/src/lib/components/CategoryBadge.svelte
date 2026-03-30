<script lang="ts">
	interface Props {
		icon?: string;
		name?: string;
		size?: 'sm' | 'md';
	}

	let { icon = '📦', name = '', size = 'md' }: Props = $props();

	const sizeClasses = {
		sm: 'h-8 w-8 text-sm',
		md: 'h-10 w-10 text-lg'
	};
</script>

<div
	class="flex items-center justify-center rounded-lg bg-primary/10 {sizeClasses[size]}"
	title={name}
>
	{icon}
</div>
