import { onMounted, ref, type Ref } from 'vue'

import { useAuthStore } from '@/stores/authStore'
import { readDashboardCache, writeDashboardCache } from '@/utils/dashboardCache'
import { describeStoreError } from '@/utils/storeError'

// Loads one dashboard tab's server-computed figures (see
// dashboardService.ts). The figures from this user's last visit show
// immediately (utils/dashboardCache.ts) while fresh ones load in the
// background; they're then replaced and saved for next time. An error
// replaces the tab only when there's nothing to show -- if the refresh
// fails over saved figures, those stay up with a note (see isStale).
export function useDashboardData<T>(tab: string, load: () => Promise<T>): {
  data: Ref<T | undefined>
  isLoading: Ref<boolean>
  error: Ref<string | undefined>
  // Showing saved figures whose refresh failed.
  isStale: Ref<boolean>
  reload: () => Promise<void>
} {
  const authStore = useAuthStore()
  const userId = () => authStore.user?.id
  const cached = readDashboardCache<T>(tab, userId())

  const data = ref<T | undefined>(cached?.data) as Ref<T | undefined>
  const isLoading = ref(false)
  const error = ref<string>()
  const isStale = ref(false)

  async function reload(): Promise<void> {
    isLoading.value = true
    error.value = undefined
    try {
      const fresh = await load()
      data.value = fresh
      isStale.value = false
      writeDashboardCache(tab, userId(), fresh)
    } catch (caught) {
      const message = describeStoreError('Unable to load the dashboard. Please try again.', caught)
      if (data.value === undefined) error.value = message
      else isStale.value = true
    } finally {
      isLoading.value = false
    }
  }

  onMounted(reload)
  return { data, isLoading, error, isStale, reload }
}
