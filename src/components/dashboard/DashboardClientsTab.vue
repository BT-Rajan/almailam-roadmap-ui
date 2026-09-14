<script setup lang="ts">
import { UserCheck, UserCog } from '@lucide/vue'
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import KPIWidget from '@/components/dashboard/KPIWidget.vue'
import StatisticsCard from '@/components/dashboard/StatisticsCard.vue'
import RecentClientsWidget from '@/components/dashboard/RecentClientsWidget.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useClientStore } from '@/stores/clientStore'
import type { KPI, StatisticItem, RecentClient } from '@/types/Dashboard'

const router = useRouter()
const { t } = useI18n()
const clientStore = useClientStore()

// Guarded exactly like DashboardProjectsTab.vue's onMounted -- skip the
// fetch if the store is already populated (e.g. the Clients page was
// visited earlier this session) or already mid-fetch (this tab was
// switched away from and back to before the first load resolved).
onMounted(() => {
  if (clientStore.clients.length === 0 && !clientStore.isLoading) void clientStore.loadClients()
})

// Onboarding still in progress -- anything short of 'Ready' (or already
// 'Rejected'/'Suspended', which also isn't "done") needs someone to act
// on it, which is exactly what this card is for.
const ONBOARDING_IN_PROGRESS = new Set(['Information Required', 'Documents Required', 'Pending Verification'])

const kpis = computed<KPI[]>(() => [
  { id: 'total', label: t('dashboard.totalClients'), value: clientStore.clients.length },
  { id: 'active', label: t('dashboard.activeClients'), value: clientStore.clients.filter((c) => c.status === 'Active').length },
])

const statistics = computed<StatisticItem[]>(() => [
  {
    id: 'onboarding',
    label: t('dashboard.pendingOnboarding'),
    value: clientStore.clients.filter((c) => ONBOARDING_IN_PROGRESS.has(c.onboardingState)).length,
    icon: UserCog,
    color: 'warning',
  },
  {
    id: 'inactive',
    label: t('dashboard.inactiveClients'),
    value: clientStore.clients.filter((c) => c.status === 'Inactive').length,
    icon: UserCheck,
    color: 'info',
  },
])

// Most recently onboarded clients -- real data, not a fixed list, so it
// changes as clients are added (same convention as recentProjects).
const recentClients = computed<RecentClient[]>(() =>
  clientStore.clients.map((client) => ({
    id: client.id,
    name: client.companyName,
    type: client.clientType,
    status: client.status,
    city: client.city,
    createdDate: client.createdDate,
  })),
)

function handleKpiClick(): void {
  router.push({ name: ROUTE_NAMES.CLIENTS })
}

function handleClientClick(clientId: string): void {
  router.push({ name: ROUTE_NAMES.CLIENT_WORKSPACE, params: { clientId } })
}
</script>

<template>
  <div class="space-y-6">
    <div class="grid grid-cols-1 tablet:grid-cols-2 laptop:grid-cols-4 gap-4">
      <KPIWidget v-for="kpi in kpis" :key="kpi.id" :kpi="kpi" @click="handleKpiClick" />
      <StatisticsCard v-for="stat in statistics" :key="stat.id" :statistic="stat" @click="handleKpiClick" />
    </div>

    <RecentClientsWidget :clients="recentClients" @client-click="handleClientClick" />
  </div>
</template>
