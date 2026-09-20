<script setup lang="ts" generic="T">
import { computed, watch } from 'vue'

import TablePagination from '@/components/common/TablePagination.vue'
import { usePagination } from '@/composables/usePagination'
import { DEFAULT_PAGE_SIZE } from '@/utils/paginationHelpers'

// Pages any list of results the way SmartTable pages a table rows --
// same composable, same pager, same 5/10/25/50 sizes -- for the lists
// that are not tables: the dashboard widgets, card grids, log entries,
// notifications and so on. The caller owns the markup for one page
// (the default slot receives just that page's items); this owns the
// slicing and the pager. Client-side: for a list a server already pages
// (clientStore, documentStore, ...) drive TablePagination from the
// store's own page/total instead.
const props = withDefaults(defineProps<{ items: T[]; pageSize?: number; pageSizeOptions?: number[]; stacked?: boolean; pagerClass?: string; pagerInset?: 'table' | 'card' | 'none' }>(), {
  pageSize: DEFAULT_PAGE_SIZE,
  pageSizeOptions: () => [5, 10, 25, 50],
  stacked: false,
  pagerClass: undefined,
  // Lists live inside padded containers unless told otherwise.
  pagerInset: 'none',
})

defineSlots<{
  default(props: { items: T[]; startIndex: number }): unknown
}>()

const { currentPage, pageSize, totalItems, totalPages, startIndex, endIndex, goToPage, setPageSize } = usePagination(
  () => props.items.length,
  props.pageSize,
)

const pageItems = computed(() => props.items.slice(startIndex.value, endIndex.value))

// The list can shrink under the reader (a task completed, a filter
// changed) -- never leave them on a page that no longer exists.
watch(totalPages, (pages) => {
  if (currentPage.value > pages) goToPage(pages)
})

// No pager for a list that fits on the smallest page size -- it would
// only add a "Showing 1-3 of 3" line to a handful of rows.
const showPagination = computed(() => totalItems.value > Math.min(...props.pageSizeOptions))
</script>

<template>
  <slot :items="pageItems" :start-index="startIndex" />
  <TablePagination
    v-if="showPagination"
    :current-page="currentPage"
    :total-pages="totalPages"
    :total-items="totalItems"
    :start-index="startIndex"
    :end-index="endIndex"
    :page-size="pageSize"
    :page-size-options="pageSizeOptions"
    :stacked="stacked"
    :inset="pagerInset"
    :class="pagerClass"
    @page-change="goToPage"
    @page-size-change="setPageSize"
  />
</template>
