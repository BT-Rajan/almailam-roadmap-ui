<script setup lang="ts">
import { ChevronLeft, ChevronRight } from '@lucide/vue'
import { computed } from 'vue'

import IconButton from '@/components/common/IconButton.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import type { SelectOption } from '@/types/Ui'

interface Props {
  currentPage: number
  totalPages: number
  totalItems: number
  startIndex: number
  endIndex: number
  pageSize: number
  pageSizeOptions?: number[]
}

const props = withDefaults(defineProps<Props>(), {
  pageSizeOptions: () => [10, 25, 50],
})

const emit = defineEmits<{
  'page-change': [page: number]
  'page-size-change': [size: number]
}>()

const rangeLabel = computed(() => {
  if (props.totalItems === 0) return 'Showing 0 results'
  return `Showing ${props.startIndex + 1}\u2013${props.endIndex} of ${props.totalItems}`
})

const pageSizeOptionList = computed<SelectOption[]>(() =>
  props.pageSizeOptions.map((size) => ({ label: `${size} / page`, value: String(size) })),
)

const isFirstPage = computed(() => props.currentPage <= 1)
const isLastPage = computed(() => props.currentPage >= props.totalPages)

function handlePageSizeChange(value: string): void {
  emit('page-size-change', Number(value))
}
</script>

<template>
  <div class="flex flex-col gap-3 border-t border-border-light px-4 py-3 tablet:flex-row tablet:items-center tablet:justify-between">
    <p class="text-sm text-neutral-500">{{ rangeLabel }}</p>
    <div class="flex items-center gap-3">
      <div class="w-32">
        <SelectBox
          :model-value="String(pageSize)"
          :options="pageSizeOptionList"
          @update:model-value="handlePageSizeChange"
        />
      </div>
      <div class="flex items-center gap-1">
        <IconButton
          :icon="ChevronLeft"
          label="Previous page"
          size="sm"
          :disabled="isFirstPage"
          @click="emit('page-change', currentPage - 1)"
        />
        <span class="px-2 text-sm text-neutral-600">{{ currentPage }} / {{ totalPages }}</span>
        <IconButton
          :icon="ChevronRight"
          label="Next page"
          size="sm"
          :disabled="isLastPage"
          @click="emit('page-change', currentPage + 1)"
        />
      </div>
    </div>
  </div>
</template>
