<script setup lang="ts">
interface Props {
  orientation?: 'horizontal' | 'vertical'
  label?: string
}

withDefaults(defineProps<Props>(), {
  orientation: 'horizontal',
  label: undefined,
})
</script>

<template>
  <div v-if="orientation === 'vertical'" class="h-full w-px bg-border-default" role="separator" />
  <div v-else-if="label" class="flex items-center gap-3" role="separator">
    <span class="h-px flex-1 bg-border-default" />
    <span class="text-xs font-medium uppercase tracking-wide text-neutral-400">{{ label }}</span>
    <span class="h-px flex-1 bg-border-default" />
  </div>
  <div v-else class="h-px w-full bg-border-default" role="separator" />
</template>
