<script lang="ts">
	interface Props {
		placeholder?: string;
		class?: string;
	}

	let { placeholder = "", class: className = "" }: Props = $props();
</script>

<span data-slot="select-value" class={className}>
	{placeholder}
</span>
