<script setup lang="ts">
import { X } from '@lucide/vue'

import BaseButton from '@/components/common/BaseButton.vue'
import SearchBox from '@/components/common/SearchBox.vue'

interface Props {
  searchValue?: string
  searchPlaceholder?: string
  hasActiveFilters?: boolean
  // Defaults to true so every existing usage (Projects, Documents,
  // Tasks, etc.) is completely unaffected -- only pages that explicitly
  // opt out lose the search box.
  showSearch?: boolean
}

withDefaults(defineProps<Props>(), {
  searchValue: '',
  searchPlaceholder: 'Search',
  hasActiveFilters: false,
  showSearch: true,
})

const emit = defineEmits<{
  'update:searchValue': [value: string]
  search: [value: string]
  clear: []
}>()
</script>

<template>
  <div class="flex flex-col gap-3 rounded-xl border border-border-light bg-bg-card p-4 shadow-soft lg:flex-row lg:items-center lg:justify-between">
    <div class="flex flex-1 flex-col gap-3 sm:flex-row sm:items-center">
      <div v-if="showSearch" class="sm:w-72">
        <SearchBox
          :model-value="searchValue"
          :placeholder="searchPlaceholder"
          @update:model-value="emit('update:searchValue', $event)"
          @search="emit('search', $event)"
        />
      </div>
      <div class="flex flex-wrap items-center gap-3">
        <slot name="filters" />
      </div>
      <BaseButton v-if="hasActiveFilters" variant="ghost" size="sm" :icon="X" @click="emit('clear')"> Clear filters </BaseButton>
    </div>
    <div v-if="$slots.actions" class="flex shrink-0 items-center gap-2">
      <slot name="actions" />
    </div>
  </div>
</template>
