<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BarChart from '@/components/reports/BarChart.vue'
import Card from '@/components/common/Card.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import ReportMetricCard from '@/components/reports/ReportMetricCard.vue'
import SmartTable from '@/components/common/SmartTable.vue'
import { STATUS_CHART_COLORS } from '@/constants/chartColors'
import { reportService } from '@/services/reportService'
import type { ChartDataPoint, EmployeePerformance } from '@/types/Report'
import type { SmartTableColumn } from '@/types/Table'

const { t } = useI18n()

function currentMonthValue(): string {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
}

const monthValue = ref(currentMonthValue())

const rows = ref<EmployeePerformance[]>([])
const isLoading = ref(false)
const loadError = ref('')

async function load(): Promise<void> {
  const [year, month] = monthValue.value.split('-').map(Number)
  if (!year || !month) return
  isLoading.value = true
  loadError.value = ''
  try {
    rows.value = await reportService.getEmployeePerformance(year, month)
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : t('report.employeePerformancePage.loadFailed')
    rows.value = []
  } finally {
    isLoading.value = false
  }
}

onMounted(load)
watch(monthValue, load)

type PerformanceRow = EmployeePerformance & Record<string, unknown>
const tableRows = computed<PerformanceRow[]>(() => rows.value.map((row) => ({ ...row })))

const columns = computed<SmartTableColumn<PerformanceRow>[]>(() => [
  { key: 'employeeName', label: t('report.employeePerformancePage.columnEmployee'), sortable: true },
  { key: 'assigned', label: t('report.employeePerformancePage.columnAssigned'), align: 'right', sortable: true },
  { key: 'completed', label: t('report.employeePerformancePage.columnCompleted'), align: 'right', sortable: true },
  { key: 'completionRate', label: t('report.employeePerformancePage.columnRate'), align: 'right', sortable: true },
])

function rateColor(rate: number): string {
  if (rate >= 80) return STATUS_CHART_COLORS.success
  if (rate >= 50) return STATUS_CHART_COLORS.warning
  return STATUS_CHART_COLORS.danger
}

const rateChart = computed<ChartDataPoint[]>(() =>
  rows.value.map((row) => ({ label: row.employeeName, value: row.completionRate, color: rateColor(row.completionRate) })),
)

const totalAssigned = computed(() => rows.value.reduce((sum, row) => sum + row.assigned, 0))
const totalCompleted = computed(() => rows.value.reduce((sum, row) => sum + row.completed, 0))
const overallRate = computed(() => (totalAssigned.value > 0 ? Math.round((totalCompleted.value * 100) / totalAssigned.value) : 0))
</script>

<template>
  <div class="flex flex-col gap-6 p-6 laptop:p-8">
    <PageHeader :title="t('report.employeePerformancePage.pageTitle')" :subtitle="t('report.employeePerformancePage.pageSubtitle')" />

    <Card>
      <div class="flex flex-col gap-1.5 sm:w-56">
        <label class="text-sm font-medium text-text-secondary">{{ t('report.employeePerformancePage.month') }}</label>
        <input
          v-model="monthValue"
          type="month"
          class="h-10 w-full rounded-lg border border-border-default bg-bg-card px-3 text-sm text-text-primary transition-colors duration-fast focus:border-accent-500 focus:outline-none focus:ring-2 focus:ring-accent-500/30"
        />
      </div>
    </Card>

    <ErrorState v-if="loadError" :description="loadError" @retry="load" />

    <template v-else>
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <ReportMetricCard :label="t('report.employeePerformancePage.metricAssigned')" :value="totalAssigned" color="primary" />
        <ReportMetricCard :label="t('report.employeePerformancePage.metricCompleted')" :value="totalCompleted" color="success" />
        <ReportMetricCard :label="t('report.employeePerformancePage.metricRate')" :value="overallRate" unit="%" color="info" />
      </div>

      <Card v-if="rateChart.length > 0">
        <template #header><h3 class="text-sm font-semibold text-text-primary">{{ t('report.employeePerformancePage.chartTitle') }}</h3></template>
        <BarChart :data="rateChart" :height="320" />
      </Card>

      <SmartTable
        :columns="columns"
        :rows="tableRows"
        row-key="userId"
        :loading="isLoading"
        :searchable="true"
        :search-placeholder="t('report.employeePerformancePage.searchEmployee')"
        :empty-title="t('report.employeePerformancePage.noData')"
      >
        <template #cell-completionRate="{ value }">{{ value }}%</template>
      </SmartTable>
    </template>
  </div>
</template>
