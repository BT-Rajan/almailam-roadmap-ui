<script setup lang="ts">
import { Building2, UserCheck, UserCog, UserX } from '@lucide/vue'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import StatisticsCard from '@/components/dashboard/StatisticsCard.vue'
import RecentClientsWidget from '@/components/dashboard/RecentClientsWidget.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import { useDashboardData } from '@/composables/useDashboardData'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { dashboardService } from '@/services/dashboardService'
import type { StatisticItem, RecentClient } from '@/types/Dashboard'

const router = useRouter()
const { t } = useI18n()

// Counts and the newest clients come ready-made from the server -- this
// tab no longer downloads every client to count them in the browser.
const { data, error, isStale, reload } = useDashboardData('clients', dashboardService.getClients)

// One consistent tile (StatisticsCard) for every figure here, same as
// DashboardFinancialsTab.vue's own.
const statistics = computed<StatisticItem[]>(() => [
  { id: 'total', label: t('dashboard.totalClients'), value: data.value?.total ?? 0, icon: Building2, color: 'primary' },
  { id: 'active', label: t('dashboard.activeClients'), value: data.value?.active ?? 0, icon: UserCheck, color: 'success' },
  { id: 'onboarding', label: t('dashboard.pendingOnboarding'), value: data.value?.onboarding ?? 0, icon: UserCog, color: 'warning' },
  { id: 'inactive', label: t('dashboard.inactiveClients'), value: data.value?.inactive ?? 0, icon: UserX, color: 'info' },
])

// Most recently added clients (newest first).
const recentClients = computed<RecentClient[]>(() => data.value?.recentClients ?? [])

function handleKpiClick(): void {
  router.push({ name: ROUTE_NAMES.CLIENTS })
}

function handleClientClick(clientId: string): void {
  router.push({ name: ROUTE_NAMES.CLIENT_WORKSPACE, params: { clientId } })
}
</script>

<template>
  <ErrorState v-if="error" :description="error" @retry="reload" />
  <div v-else class="space-y-6">
    <p v-if="isStale" class="flex flex-wrap items-center gap-2 text-xs text-text-muted" role="status">
      {{ t('dashboard.staleNotice') }}
      <button type="button" class="font-medium text-primary-600 hover:text-primary-700" @click="reload">{{ t('dashboard.retry') }}</button>
    </p>
    <div class="grid grid-cols-1 tablet:grid-cols-2 laptop:grid-cols-4 gap-4">
      <StatisticsCard v-for="stat in statistics" :key="stat.id" :statistic="stat" @click="handleKpiClick" />
    </div>

    <RecentClientsWidget :clients="recentClients" @client-click="handleClientClick" />
  </div>
</template>
