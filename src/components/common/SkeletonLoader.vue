<script setup lang="ts">
interface Props {
  variant?: 'text' | 'block' | 'circle'
  rows?: number
  width?: string
  height?: string
}

withDefaults(defineProps<Props>(), {
  variant: 'text',
  rows: 1,
  width: '100%',
  height: undefined,
})
</script>

<template>
  <div v-if="variant === 'text'" class="flex flex-col gap-2">
    <span
      v-for="row in rows"
      :key="row"
      class="block h-3.5 animate-pulse rounded bg-bg-secondary"
      :style="{ width: row === rows && rows > 1 ? '70%' : width }"
    />
  </div>
  <span
    v-else-if="variant === 'circle'"
    class="block animate-pulse rounded-full bg-bg-secondary"
    :style="{ width: width === '100%' ? '2.5rem' : width, height: height ?? width }"
  />
  <span
    v-else
    class="block animate-pulse rounded-lg bg-bg-secondary"
    :style="{ width, height: height ?? '6rem' }"
  />
</template>
