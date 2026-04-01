<script lang="ts">
	interface Props {
		icon?: string;
		name?: string;
		size?: 'sm' | 'md';
	}

	let { icon = '📦', name = '', size = 'md' }: Props = $props();

	const sizeClasses = {
		sm: 'h-8 w-8 text-sm rounded-lg',
		md: 'h-10 w-10 text-lg rounded-xl'
	};
</script>

<div
	class="flex items-center justify-center bg-primary/8 {sizeClasses[size]}"
	title={name}
>
	{icon}
</div>
