<script setup lang="ts">
import { Search, X } from '@lucide/vue'
import { onBeforeUnmount } from 'vue'

interface Props {
  modelValue: string
  placeholder?: string
  debounceMs?: number
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: 'Search',
  debounceMs: 300,
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
  search: [value: string]
}>()

let debounceTimer: ReturnType<typeof setTimeout> | undefined

const handleInput = (event: Event): void => {
  const value = (event.target as HTMLInputElement).value
  emit('update:modelValue', value)

  if (debounceTimer) {
    clearTimeout(debounceTimer)
  }
  debounceTimer = setTimeout(() => {
    emit('search', value)
  }, props.debounceMs)
}

const clearSearch = (): void => {
  emit('update:modelValue', '')
  emit('search', '')
}

onBeforeUnmount(() => {
  if (debounceTimer) {
    clearTimeout(debounceTimer)
  }
})
</script>

<template>
  <div class="relative">
    <Search class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-neutral-400" />
    <input
      type="text"
      :value="modelValue"
      :placeholder="placeholder"
      class="h-10 w-full rounded-lg border border-border-default bg-bg-card py-2 pl-10 pr-9 text-sm text-neutral-800 placeholder:text-neutral-400 transition-colors duration-fast focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/30"
      @input="handleInput"
    />
    <button
      v-if="modelValue"
      type="button"
      aria-label="Clear search"
      class="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-400 hover:text-neutral-600"
      @click="clearSearch"
    >
      <X class="h-4 w-4" />
    </button>
  </div>
</template>
