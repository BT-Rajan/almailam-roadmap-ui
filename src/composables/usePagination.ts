import { computed, ref } from 'vue'

import { DEFAULT_PAGE_SET_SIZE, DEFAULT_PAGE_SIZE, getPageSet } from '@/utils/paginationHelpers'

export function usePagination(getTotalItems: () => number, initialPageSize = DEFAULT_PAGE_SIZE, setSize = DEFAULT_PAGE_SET_SIZE) {
  const currentPage = ref(1)
  const pageSize = ref(initialPageSize)

  const totalItems = computed(() => getTotalItems())
  const totalPages = computed(() => Math.max(1, Math.ceil(totalItems.value / pageSize.value)))
  const startIndex = computed(() => (currentPage.value - 1) * pageSize.value)
  const endIndex = computed(() => Math.min(startIndex.value + pageSize.value, totalItems.value))

  // Which page-number buttons to show right now, grouped into sets of
  // `setSize` (see utils/paginationHelpers.ts) -- e.g. pages 1-5, then
  // 6-10 once the reader pages past 5, rather than one button per page
  // however many pages there are.
  const pageSet = computed(() => getPageSet(currentPage.value, totalPages.value, setSize))

  function goToPage(page: number): void {
    currentPage.value = Math.min(Math.max(page, 1), totalPages.value)
  }

  function goToNextSet(): void {
    goToPage(pageSet.value.nextSetPage)
  }

  function goToPreviousSet(): void {
    goToPage(pageSet.value.previousSetPage)
  }

  function setPageSize(size: number): void {
    pageSize.value = size
    currentPage.value = 1
  }

  function resetPage(): void {
    currentPage.value = 1
  }

  return {
    currentPage,
    pageSize,
    totalItems,
    totalPages,
    startIndex,
    endIndex,
    pageSet,
    goToPage,
    goToNextSet,
    goToPreviousSet,
    setPageSize,
    resetPage,
  }
}
