import { onMounted, ref, type Ref } from 'vue'

import { describeStoreError } from '@/utils/storeError'

// Loads one dashboard tab's server-computed figures (see
// dashboardService.ts) on mount, with an error message and retry.
export function useDashboardData<T>(load: () => Promise<T>): {
  data: Ref<T | undefined>
  isLoading: Ref<boolean>
  error: Ref<string | undefined>
  reload: () => Promise<void>
} {
  const data = ref<T>() as Ref<T | undefined>
  const isLoading = ref(false)
  const error = ref<string>()

  async function reload(): Promise<void> {
    isLoading.value = true
    error.value = undefined
    try {
      data.value = await load()
    } catch (caught) {
      error.value = describeStoreError('Unable to load the dashboard. Please try again.', caught)
    } finally {
      isLoading.value = false
    }
  }

  onMounted(reload)
  return { data, isLoading, error, reload }
}
