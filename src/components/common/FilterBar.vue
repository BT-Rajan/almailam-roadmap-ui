<script setup lang="ts">
import { X } from '@lucide/vue'

import BaseButton from '@/components/common/BaseButton.vue'
import SearchBox from '@/components/common/SearchBox.vue'

interface Props {
  searchValue: string
  searchPlaceholder?: string
  hasActiveFilters?: boolean
}

withDefaults(defineProps<Props>(), {
  searchPlaceholder: 'Search',
  hasActiveFilters: false,
})

const emit = defineEmits<{
  'update:searchValue': [value: string]
  clear: []
}>()
</script>

<template>
  <div class="flex flex-col gap-3 rounded-xl border border-border-light bg-bg-card p-4 shadow-soft lg:flex-row lg:items-center lg:justify-between">
    <div class="flex flex-1 flex-col gap-3 sm:flex-row sm:items-center">
      <div class="sm:w-72">
        <SearchBox
          :model-value="searchValue"
          :placeholder="searchPlaceholder"
          @update:model-value="emit('update:searchValue', $event)"
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
