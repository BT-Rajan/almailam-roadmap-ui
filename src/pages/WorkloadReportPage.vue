<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import ReportHeader from '@/components/reports/ReportHeader.vue'
import ReportSection from '@/components/reports/ReportSection.vue'
import ReportMetricCard from '@/components/reports/ReportMetricCard.vue'
import BarChart from '@/components/reports/BarChart.vue'
import ProgressChart from '@/components/reports/ProgressChart.vue'
import Card from '@/components/common/Card.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import { DEFAULT_CHART_COLOR, STATUS_CHART_COLORS } from '@/constants/chartColors'
import { reportService } from '@/services/reportService'
import type { ChartDataPoint, TeamWorkload, TeamWorkloadMember } from '@/types/Report'

const router = useRouter()
const { t } = useI18n()

// Matches report_service.TASKS_AT_FULL_CAPACITY on the backend -- the
// number of open tasks treated as "fully loaded" for allocation-percent
// purposes, since no real capacity/hours field exists anywhere in the
// schema. Kept in sync manually; if the backend constant changes, update
// this too (see that constant's own comment for why it exists at all).
const TASKS_AT_FULL_CAPACITY = 8

const reportDate = new Date().toLocaleDateString('en-US', {
  year: 'numeric',
  month: 'long',
  day: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
})

const isLoading = ref(false)
const loadError = ref('')
const workload = ref<TeamWorkload | null>(null)

async function load(): Promise<void> {
  isLoading.value = true
  loadError.value = ''
  try {
    workload.value = await reportService.getTeamWorkload()
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : t('report.workloadPage.loadFailed')
    workload.value = null
  } finally {
    isLoading.value = false
  }
}

onMounted(load)

const members = computed<TeamWorkloadMember[]>(() => workload.value?.members ?? [])

const teamMetrics = computed(() => [
  {
    label: t('report.workloadPage.totalTeamMembers'),
    value: workload.value?.totalMembers ?? 0,
    color: 'primary',
  },
  {
    label: t('report.workloadPage.averageUtilization'),
    value: `${workload.value?.averageUtilization ?? 0}%`,
    color: 'info',
  },
  {
    label: t('report.workloadPage.overallocatedStaff'),
    value: workload.value?.overallocatedCount ?? 0,
    unit: t('report.workloadPage.personsUnit'),
    color: 'warning',
  },
  {
    label: t('report.workloadPage.capacityAvailable'),
    value: `${workload.value?.capacityAvailable ?? 0}%`,
    color: 'neutral',
  },
])

function allocationColor(allocationPercent: number): string {
  if (allocationPercent > 100) return STATUS_CHART_COLORS.danger
  if (allocationPercent >= 90) return STATUS_CHART_COLORS.warning
  return STATUS_CHART_COLORS.success
}

const activeTasksChart = computed<ChartDataPoint[]>(() =>
  members.value.map((member) => ({ label: member.name, value: member.activeTasks, color: DEFAULT_CHART_COLOR })),
)

const allocationChart = computed<ChartDataPoint[]>(() =>
  members.value.map((member) => ({ label: member.name, value: member.allocationPercent, color: allocationColor(member.allocationPercent) })),
)

const overallocatedMembers = computed(() => members.value.filter((member) => member.overallocated))
const overdueMembers = computed(() => members.value.filter((member) => member.overdueTasks > 0))

function namesList(list: TeamWorkloadMember[]): string {
  return list.map((member) => member.name).join(', ')
}

// See ProjectReportPage.vue's identical handler for why this uses
// window.print() rather than a separate backend-rendered PDF.
const handleExport = () => {
  window.print()
}

const goBack = () => {
  router.back()
}

function getRowColor(member: TeamWorkloadMember): string {
  if (member.overallocated) return 'bg-danger-50 border-danger-200'
  if (member.allocationPercent >= 90) return 'bg-warning-50 border-warning-200'
  return 'bg-bg-secondary'
}
</script>

<template>
  <div class="max-w-6xl mx-auto space-y-8 pb-12">
    <div class="flex items-center justify-between">
      <BaseButton variant="ghost" size="sm" @click="goBack"> ← {{ t('report.back') }} </BaseButton>
    </div>

    <ReportHeader :title="t('report.workloadPage.pageTitle')" :subtitle="t('report.workloadPage.pageSubtitle')" :generated-date="reportDate" @download="handleExport" />

    <ErrorState v-if="loadError" :description="loadError" @retry="load" />

    <SkeletonLoader v-else-if="isLoading" :rows="6" />

    <EmptyState
      v-else-if="members.length === 0"
      :title="t('report.workloadPage.noDataTitle')"
      :description="t('report.workloadPage.noDataDescription')"
    />

    <template v-else>
      <!-- Team Overview Metrics -->
      <ReportSection :title="t('report.workloadPage.teamOverviewTitle')" :description="t('report.workloadPage.teamOverviewDescription')">
        <ReportMetricCard v-for="(metric, index) in teamMetrics" :key="index" :label="metric.label" :value="metric.value" :unit="metric.unit" :color="metric.color" />
      </ReportSection>

      <!-- Overall Team Health -->
      <ReportSection :title="t('report.workloadPage.teamCapacityStatusTitle')" fullWidth>
        <div class="grid grid-cols-1 tablet:grid-cols-2 gap-8 justify-items-center">
          <ProgressChart :value="workload?.averageUtilization ?? 0" :label="t('report.workloadPage.averageUtilization')" :color="DEFAULT_CHART_COLOR" size="md" />
          <ProgressChart :value="workload?.capacityAvailable ?? 0" :label="t('report.workloadPage.capacityAvailable')" :color="STATUS_CHART_COLORS.success" size="md" />
        </div>
      </ReportSection>

      <!-- Active Tasks by Team Member -->
      <ReportSection :title="t('report.workloadPage.activeTasksChartTitle')" :description="t('report.workloadPage.activeTasksChartDescription')" fullWidth>
        <Card>
          <BarChart :data="activeTasksChart" :height="350" />
        </Card>
      </ReportSection>

      <!-- Allocation by Team Member -->
      <ReportSection
        :title="t('report.workloadPage.allocationChartTitle')"
        :description="t('report.workloadPage.allocationChartDescription', { capacity: TASKS_AT_FULL_CAPACITY })"
        fullWidth
      >
        <Card>
          <BarChart :data="allocationChart" :height="350" />
        </Card>
      </ReportSection>

      <!-- Individual Team Member Details -->
      <ReportSection :title="t('report.workloadPage.teamMemberDetailsTitle')" fullWidth>
        <div class="space-y-3">
          <div
            v-for="member in members"
            :key="member.userId"
            :class="['p-4 rounded-lg border transition-all', getRowColor(member)]"
          >
            <div class="grid grid-cols-1 tablet:grid-cols-3 gap-4">
              <div>
                <p class="text-sm font-semibold text-text-primary">{{ member.name }}</p>
                <p class="text-xs text-text-secondary mt-1">{{ member.role }}</p>
              </div>
              <div>
                <p class="text-xs text-text-secondary uppercase font-medium mb-2">{{ t('report.workloadPage.allocation') }}</p>
                <div class="space-y-1">
                  <div class="h-2 bg-border-default rounded-full overflow-hidden">
                    <div :style="{ width: `${Math.min(member.allocationPercent, 120)}%`, backgroundColor: allocationColor(member.allocationPercent) }" class="h-full rounded-full transition-all" />
                  </div>
                  <div class="flex items-center justify-between text-xs">
                    <span :class="member.allocationPercent > 100 ? 'text-danger-600 font-semibold' : 'text-text-secondary'">
                      {{ member.allocationPercent }}%
                    </span>
                    <span v-if="member.overallocated" class="text-danger-600 font-medium">⚠ {{ t('report.workloadPage.overallocatedBadge') }}</span>
                  </div>
                </div>
              </div>
              <div class="flex items-center gap-4">
                <div>
                  <p class="text-xs text-text-secondary uppercase font-medium">{{ t('report.workloadPage.projects') }}</p>
                  <p class="text-lg font-bold text-text-primary mt-1">{{ member.activeProjects }}</p>
                </div>
                <div>
                  <p class="text-xs text-text-secondary uppercase font-medium">{{ t('report.workloadPage.activeTasks') }}</p>
                  <p class="text-lg font-bold text-text-primary mt-1">{{ member.activeTasks }}</p>
                </div>
                <div>
                  <p class="text-xs text-text-secondary uppercase font-medium">{{ t('report.workloadPage.overdueTasks') }}</p>
                  <p :class="['text-lg font-bold mt-1', member.overdueTasks > 0 ? 'text-danger-600' : 'text-text-primary']">{{ member.overdueTasks }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </ReportSection>

      <!-- Recommendations -->
      <ReportSection :title="t('report.workloadPage.recommendationsTitle')" fullWidth>
        <div class="space-y-3">
          <Card v-if="overallocatedMembers.length === 0" class="bg-success-50 border border-success-200">
            <div class="space-y-2">
              <h3 class="font-semibold text-success-900">✓ {{ t('report.workloadPage.noOverallocationTitle') }}</h3>
              <p class="text-sm text-success-800">{{ t('report.workloadPage.noOverallocationText', { capacity: TASKS_AT_FULL_CAPACITY }) }}</p>
            </div>
          </Card>
          <Card v-else class="bg-danger-50 border border-danger-200">
            <div class="space-y-2">
              <h3 class="font-semibold text-danger-900">⚠ {{ t('report.workloadPage.overallocatedWarningTitle') }}</h3>
              <p class="text-sm text-danger-800">{{ t('report.workloadPage.overallocatedWarningText', { names: namesList(overallocatedMembers), capacity: TASKS_AT_FULL_CAPACITY }) }}</p>
            </div>
          </Card>
          <Card v-if="overdueMembers.length > 0" class="bg-warning-50 border border-warning-200">
            <div class="space-y-2">
              <h3 class="font-semibold text-warning-900">⚠ {{ t('report.workloadPage.overdueWarningTitle') }}</h3>
              <p class="text-sm text-warning-800">{{ t('report.workloadPage.overdueWarningText', { names: namesList(overdueMembers) }) }}</p>
            </div>
          </Card>
        </div>
      </ReportSection>

      <!-- Report Footer -->
      <div class="border-t border-border-light pt-6 text-center text-xs text-text-muted">
        <p>{{ t('report.workloadPage.footerTitle') }}</p>
        <p class="mt-1">{{ t('report.workloadPage.footerGenerated', { date: reportDate }) }}</p>
        <p class="mt-1">{{ t('report.workloadPage.footerBasedOn') }}</p>
      </div>
    </template>
  </div>
</template>

<style scoped>
@media print {
  :deep(.print\:hidden) {
    display: none;
  }

  :deep(button) {
    display: none;
  }

  :deep(.max-w-6xl) {
    max-width: 100%;
  }
}
</style>
