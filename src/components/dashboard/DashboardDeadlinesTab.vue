<script setup lang="ts">
import { Clock, FileWarning } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import StatisticsCard from '@/components/dashboard/StatisticsCard.vue'
import UpcomingDeadlinesWidget from '@/components/dashboard/UpcomingDeadlinesWidget.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { contractService } from '@/services/contractService'
import { useProjectStore } from '@/stores/projectStore'
import { useTaskStore } from '@/stores/taskStore'
import type { Contract } from '@/types/Contract'
import type { Deadline, StatisticItem } from '@/types/Dashboard'

const router = useRouter()
const { t } = useI18n()
const projectStore = useProjectStore()
const taskStore = useTaskStore()
const contractRenewalsWidget = ref<InstanceType<typeof UpcomingDeadlinesWidget> | null>(null)

// Deadlines are derived from task due dates, and each task's project name
// needs projectStore -- guarded the same way as the other tabs.
onMounted(() => {
  if (taskStore.tasks.length === 0 && !taskStore.isLoading) void taskStore.loadTasks()
  if (projectStore.projects.length === 0 && !projectStore.isLoading) void projectStore.loadProjects()
})

function projectNameFor(projectId: string): string {
  return projectStore.projects.find((project) => project.id === projectId)?.projectName ?? 'Unknown Project'
}

const today = computed(() => new Date().setHours(0, 0, 0, 0))

// Contract renewals -- not from any per-project store (contractStore is
// scoped to whichever single project a workspace tab has open), fetched
// directly and held locally, same reasoning as taskStore/projectStore
// above but without a shared store to reuse.
const allContracts = ref<Contract[]>([])
const isLoadingContracts = ref(false)
onMounted(async () => {
  if (allContracts.value.length > 0 || isLoadingContracts.value) return
  isLoadingContracts.value = true
  try {
    allContracts.value = await contractService.getContracts()
  } finally {
    isLoadingContracts.value = false
  }
})

// Business policy: a contract can't expire before it's even signed --
// a Draft's expiryDate is provisional and not yet in force, and
// Expired/Terminated are already resolved. Only Signed/Active
// contracts are actually counted down against their expiry date.
const renewalEligibleContracts = computed(() => allContracts.value.filter((contract) => contract.status === 'Signed' || contract.status === 'Active'))

const daysUntil = (isoDate: string) => Math.ceil((new Date(isoDate).getTime() - today.value) / (1000 * 60 * 60 * 24))

const contractsExpiringSoon = computed(() => renewalEligibleContracts.value.filter((contract) => {
  const days = daysUntil(contract.expiryDate)
  return days >= 0 && days <= 7
}))

// "Not renewed" -- expiry date has already passed but nobody has moved
// the contract to Expired/Terminated *and* the project it belongs to
// isn't Completed, so the work is presumably still ongoing without a
// contract actually covering it. This is deliberately a dashboard
// callout for staff to act on rather than an automatic status change
// (no scheduled job flips these to Expired on its own).
const contractsNotRenewed = computed(() => renewalEligibleContracts.value.filter((contract) => {
  if (daysUntil(contract.expiryDate) >= 0) return false
  const project = projectStore.projects.find((p) => p.id === contract.projectId)
  return project ? project.status !== 'Completed' : false
}))

const statistics = computed<StatisticItem[]>(() => [
  {
    id: 'overdue',
    label: t('dashboard.overdueTasks'),
    value: taskStore.tasks.filter((task) => task.status !== 'Completed' && new Date(task.dueDate).getTime() < today.value).length,
    icon: Clock,
    color: 'danger',
  },
  {
    id: 'contracts-expiring-soon',
    label: t('dashboard.contractsExpiringSoon'),
    value: contractsExpiringSoon.value.length,
    icon: FileWarning,
    color: 'warning',
  },
  {
    id: 'contracts-not-renewed',
    label: t('dashboard.contractsNotRenewed'),
    value: contractsNotRenewed.value.length,
    icon: FileWarning,
    color: 'danger',
  },
])

// There is no separate "deadlines" concept in the backend -- this reuses
// real task due dates, same convention as the old dashboard, just with
// more room to show them now that it has a whole tab instead of a
// sidebar slot.
const upcomingDeadlines = computed<Deadline[]>(() => {
  const now = Date.now()
  const twoWeeksFromNow = now + 14 * 24 * 60 * 60 * 1000
  return taskStore.tasks
    .filter((task) => task.status !== 'Completed')
    .filter((task) => {
      const due = new Date(task.dueDate).getTime()
      return due >= now && due <= twoWeeksFromNow
    })
    .sort((a, b) => a.dueDate.localeCompare(b.dueDate))
    .slice(0, 15)
    .map((task) => ({
      id: task.id,
      title: task.title,
      project: projectNameFor(task.projectId),
      dueDate: task.dueDate,
      priority: task.priority === 'High' ? ('high' as const) : task.priority === 'Medium' ? ('medium' as const) : ('low' as const),
      type: 'review' as const,
    }))
})

// Both buckets in one widget, sorted oldest-expiry-first -- an already
// lapsed contract (negative days) is always more urgent than one still
// counting down, and the widget's own overdue/urgent/soon styling
// already reads correctly for both at once.
const contractRenewalItems = computed<Deadline[]>(() => [...contractsNotRenewed.value, ...contractsExpiringSoon.value].map((contract) => ({
  id: contract.projectId,
  title: contract.contractNo,
  project: projectNameFor(contract.projectId),
  dueDate: contract.expiryDate,
  priority: 'high' as const,
  type: 'contract-expiry' as const,
})))

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
  <div class="space-y-6">
    <div class="grid grid-cols-1 tablet:grid-cols-3 gap-4">
      <StatisticsCard v-for="stat in statistics" :key="stat.id" :statistic="stat" @click="handleStatisticClick(stat.id)" />
    </div>

    <UpcomingDeadlinesWidget
      :title="t('dashboard.upcomingDeadlines')"
      :deadlines="upcomingDeadlines"
      :max-items="15"
      @deadline-click="handleDeadlineClick"
    />

    <UpcomingDeadlinesWidget
      ref="contractRenewalsWidget"
      :title="t('dashboard.contractRenewals')"
      :deadlines="contractRenewalItems"
      :max-items="15"
      :empty-text="t('dashboard.noContractRenewals')"
      @deadline-click="handleContractRenewalClick"
    />
  </div>
</template>
