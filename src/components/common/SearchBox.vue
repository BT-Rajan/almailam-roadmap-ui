<script setup lang="ts">
import { Search, X } from '@lucide/vue'
import { onBeforeUnmount } from 'vue'
import { useI18n } from 'vue-i18n'

interface Props {
  modelValue: string
  placeholder?: string
  debounceMs?: number
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: undefined,
  debounceMs: 300,
})

const { t } = useI18n()

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
    <Search class="pointer-events-none absolute start-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
    <input
      type="text"
      :value="modelValue"
      :placeholder="placeholder ?? t('common.search')"
      class="h-10 w-full rounded-lg border border-border-default bg-bg-card py-2 ps-10 pe-9 text-sm text-text-primary placeholder:text-text-muted transition-colors duration-fast focus:border-accent-500 focus:outline-none focus:ring-2 focus:ring-accent-500/30"
      @input="handleInput"
    />
    <button
      v-if="modelValue"
      type="button"
      :aria-label="t('common.clearSearch')"
      class="absolute end-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-secondary"
      @click="clearSearch"
    >
      <X class="h-4 w-4" />
    </button>
  </div>
</template>
