<script setup lang="ts">
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from '@lucide/vue'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import IconButton from '@/components/common/IconButton.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import { useLocale } from '@/composables/useLocale'
import { getPageSet } from '@/utils/paginationHelpers'
import type { SelectOption } from '@/types/Ui'

interface Props {
  currentPage: number
  totalPages: number
  totalItems: number
  startIndex: number
  endIndex: number
  pageSize: number
  pageSizeOptions?: number[]
  // How many page-number buttons show at once before stepping to the
  // next set -- see utils/paginationHelpers.ts. Every consumer (this
  // component is shared by SmartTable and every server-paginated list
  // page) gets the same 5-per-set behaviour unless it opts out.
  setSize?: number
}

const props = withDefaults(defineProps<Props>(), {
  pageSizeOptions: () => [5, 10, 25, 50],
  setSize: 5,
})

const emit = defineEmits<{
  'page-change': [page: number]
  'page-size-change': [size: number]
}>()

const { t } = useI18n()
const { isRtl } = useLocale()

// Previous/next chevrons point the way the reader moves, which reverses
// with reading direction rather than staying physically fixed.
const previousPageIcon = computed(() => (isRtl.value ? ChevronRight : ChevronLeft))
const nextPageIcon = computed(() => (isRtl.value ? ChevronLeft : ChevronRight))
const previousSetIcon = computed(() => (isRtl.value ? ChevronsRight : ChevronsLeft))
const nextSetIcon = computed(() => (isRtl.value ? ChevronsLeft : ChevronsRight))

const rangeLabel = computed(() => {
  if (props.totalItems === 0) return t('common.showingZeroResults')
  return t('common.showingRange', { start: props.startIndex + 1, end: props.endIndex, total: props.totalItems })
})

const pageSizeOptionList = computed<SelectOption[]>(() =>
  props.pageSizeOptions.map((size) => ({ label: t('common.perPage', { size }), value: String(size) })),
)

const isFirstPage = computed(() => props.currentPage <= 1)
const isLastPage = computed(() => props.currentPage >= props.totalPages)

// The current set of page-number buttons (e.g. [6, 7, 8, 9, 10]) plus
// whether/where a whole-set jump would go -- pure function of the
// currentPage/totalPages props, so it stays correct for both
// client-side (SmartTable/usePagination) and server-side (a store's
// own page/total) pagination without this component needing to know
// which one it's driving.
const pageSet = computed(() => getPageSet(props.currentPage, props.totalPages, props.setSize))

function handlePageSizeChange(value: string): void {
  emit('page-size-change', Number(value))
}
</script>

<template>
  <div class="flex flex-col gap-3 border-t border-border-light px-4 py-3 tablet:flex-row tablet:items-center tablet:justify-between">
    <p class="text-sm text-text-muted">{{ rangeLabel }}</p>
    <div class="flex items-center gap-3">
      <div class="w-32">
        <SelectBox
          :model-value="String(pageSize)"
          :options="pageSizeOptionList"
          @update:model-value="handlePageSizeChange"
        />
      </div>
      <nav class="flex items-center gap-0.5" :aria-label="t('common.pagination')">
        <IconButton
          v-if="pageSet.hasPreviousSet"
          :icon="previousSetIcon"
          :label="t('common.previousPageSet')"
          size="sm"
          @click="emit('page-change', pageSet.previousSetPage)"
        />
        <IconButton
          :icon="previousPageIcon"
          :label="t('common.previousPage')"
          size="sm"
          :disabled="isFirstPage"
          @click="emit('page-change', currentPage - 1)"
        />
        <button
          v-for="page in pageSet.pages"
          :key="page"
          type="button"
          class="flex h-8 min-w-8 items-center justify-center rounded-lg px-2 text-sm font-medium transition-colors duration-fast"
          :class="
            page === currentPage
              ? 'bg-accent-500 text-neutral-0'
              : 'text-text-secondary hover:bg-bg-hover hover:text-text-primary'
          "
          :aria-current="page === currentPage ? 'page' : undefined"
          :aria-label="t('common.goToPage', { page })"
          @click="emit('page-change', page)"
        >
          {{ page }}
        </button>
        <IconButton
          :icon="nextPageIcon"
          :label="t('common.nextPage')"
          size="sm"
          :disabled="isLastPage"
          @click="emit('page-change', currentPage + 1)"
        />
        <IconButton
          v-if="pageSet.hasNextSet"
          :icon="nextSetIcon"
          :label="t('common.nextPageSet')"
          size="sm"
          @click="emit('page-change', pageSet.nextSetPage)"
        />
      </nav>
    </div>
  </div>
</template>
