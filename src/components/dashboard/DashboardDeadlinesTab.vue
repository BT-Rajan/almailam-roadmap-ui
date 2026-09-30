<script setup lang="ts">
import { Clock, FileWarning } from '@lucide/vue'
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import StatisticsCard from '@/components/dashboard/StatisticsCard.vue'
import UpcomingDeadlinesWidget from '@/components/dashboard/UpcomingDeadlinesWidget.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import { useDashboardData } from '@/composables/useDashboardData'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { dashboardService, type DashboardContractRow } from '@/services/dashboardService'
import type { Deadline, StatisticItem } from '@/types/Dashboard'
import type { TaskPriority } from '@/types/Task'

const router = useRouter()
const { t } = useI18n()
const contractRenewalsWidget = ref<InstanceType<typeof UpcomingDeadlinesWidget> | null>(null)

// Overdue count, the next two weeks' task deadlines and the contract
// renewal callouts all come from one server request, computed against the
// server's Kuwait-local "today" -- this tab no longer downloads every
// task, project and contract.
//
// Contract rules (unchanged, now server-side): only Signed/Active
// contracts count down; "expiring soon" = expires within 7 days; "not
// renewed" = already past expiry while its project isn't Completed -- a
// callout for staff to act on, not an automatic status change.
const { data, error, reload } = useDashboardData(dashboardService.getDeadlines)

const statistics = computed<StatisticItem[]>(() => [
  { id: 'overdue', label: t('dashboard.overdueTasks'), value: data.value?.overdueTasks ?? 0, icon: Clock, color: 'danger' },
  {
    id: 'contracts-expiring-soon',
    label: t('dashboard.contractsExpiringSoon'),
    value: data.value?.contractsExpiringSoon.length ?? 0,
    icon: FileWarning,
    color: 'warning',
  },
  {
    id: 'contracts-not-renewed',
    label: t('dashboard.contractsNotRenewed'),
    value: data.value?.contractsNotRenewed.length ?? 0,
    icon: FileWarning,
    color: 'danger',
  },
])

const PRIORITY: Record<TaskPriority, Deadline['priority']> = { High: 'high', Medium: 'medium', Low: 'low' }

const upcomingDeadlines = computed<Deadline[]>(() =>
  (data.value?.upcomingDeadlines ?? []).map((task) => ({
    id: task.id,
    title: task.title,
    project: task.project,
    dueDate: task.dueDate,
    priority: PRIORITY[task.priority],
    type: 'review' as const,
  })),
)

// Both buckets in one widget, already-lapsed first -- a lapsed contract is
// always more urgent than one still counting down.
const contractRenewalItems = computed<Deadline[]>(() =>
  [...(data.value?.contractsNotRenewed ?? []), ...(data.value?.contractsExpiringSoon ?? [])].map((contract: DashboardContractRow) => ({
    id: contract.projectId,
    title: contract.contractNo,
    project: contract.project,
    dueDate: contract.expiryDate,
    priority: 'high' as const,
    type: 'contract-expiry' as const,
  })),
)

function handleStatisticClick(statisticId: string): void {
  if (statisticId === 'contracts-expiring-soon' || statisticId === 'contracts-not-renewed') {
    ;(contractRenewalsWidget.value?.$el as HTMLElement | undefined)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    return
  }
  router.push({ name: ROUTE_NAMES.TASKS })
}

function handleDeadlineClick(): void {
  router.push({ name: ROUTE_NAMES.TASKS })
}

function handleContractRenewalClick(projectId: string): void {
  router.push({ name: ROUTE_NAMES.PROJECT_WORKSPACE, params: { projectId }, query: { tab: 'contract' } })
}
</script>

<template>
  <ErrorState v-if="error" :description="error" @retry="reload" />
  <div v-else class="space-y-6">
    <div class="grid grid-cols-1 tablet:grid-cols-3 gap-4">
      <StatisticsCard v-for="stat in statistics" :key="stat.id" :statistic="stat" @click="handleStatisticClick(stat.id)" />
    </div>

    <UpcomingDeadlinesWidget
      :title="t('dashboard.upcomingDeadlines')"
      :deadlines="upcomingDeadlines"
      :page-size="10"
      @deadline-click="handleDeadlineClick"
    />

    <UpcomingDeadlinesWidget
      ref="contractRenewalsWidget"
      :title="t('dashboard.contractRenewals')"
      :deadlines="contractRenewalItems"
      :page-size="10"
      :empty-text="t('dashboard.noContractRenewals')"
      @deadline-click="handleContractRenewalClick"
    />
  </div>
</template>
