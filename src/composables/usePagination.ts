import { computed, ref } from 'vue'

const DEFAULT_PAGE_SIZE = 10

export function usePagination(getTotalItems: () => number, initialPageSize = DEFAULT_PAGE_SIZE) {
  const currentPage = ref(1)
  const pageSize = ref(initialPageSize)

  const totalItems = computed(() => getTotalItems())
  const totalPages = computed(() => Math.max(1, Math.ceil(totalItems.value / pageSize.value)))
  const startIndex = computed(() => (currentPage.value - 1) * pageSize.value)
  const endIndex = computed(() => Math.min(startIndex.value + pageSize.value, totalItems.value))

  function goToPage(page: number): void {
    currentPage.value = Math.min(Math.max(page, 1), totalPages.value)
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
    goToPage,
    setPageSize,
    resetPage,
  }
}
