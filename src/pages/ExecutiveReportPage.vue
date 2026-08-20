<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import ReportHeader from '@/components/reports/ReportHeader.vue'
import ReportSection from '@/components/reports/ReportSection.vue'
import ReportMetricCard from '@/components/reports/ReportMetricCard.vue'
import BarChart from '@/components/reports/BarChart.vue'
import LineChart from '@/components/reports/LineChart.vue'
import Card from '@/components/common/Card.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import { reportService } from '@/services/reportService'
import { useToastStore } from '@/stores/toastStore'
import type { ChartDataPoint, LineChartData, ReportMetric } from '@/types/Report'

const router = useRouter()
const toastStore = useToastStore()

const reportDate = new Date().toLocaleDateString('en-US', {
  year: 'numeric',
  month: 'long',
  day: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
})

const isLoading = ref(true)
const error = ref<string | undefined>(undefined)
const keyMetrics = ref<ReportMetric[]>([])
const projectsByStatus = ref<ChartDataPoint[]>([])
const paymentsReceivedTrend = ref<LineChartData[]>([])
const contractsByStatus = ref<ChartDataPoint[]>([])

async function loadReport(): Promise<void> {
  isLoading.value = true
  error.value = undefined
  try {
    ;[keyMetrics.value, projectsByStatus.value, paymentsReceivedTrend.value, contractsByStatus.value] =
      await Promise.all([
        reportService.getSummary(),
        reportService.getProjectsByStatus(),
        reportService.getPaymentsReceivedByMonth(6),
        reportService.getContractsByStatus(),
      ])
  } catch {
    error.value = 'Unable to load the executive report. Please try again.'
  } finally {
    isLoading.value = false
  }
}

onMounted(loadReport)

const handleExport = () => {
  toastStore.show('info', 'Export not available yet', 'PDF export for this report is coming soon.')
}

const goBack = () => {
  router.back()
}
</script>

<template>
  <div class="max-w-6xl mx-auto space-y-8 pb-12">
    <div class="flex items-center justify-between">
      <BaseButton variant="ghost" size="sm" @click="goBack"> ← Back </BaseButton>
    </div>

    <ReportHeader title="Executive Summary Report" subtitle="Current Performance Overview" :generated-date="reportDate" @download="handleExport" />

    <ErrorState v-if="error" :description="error" @retry="loadReport" />

    <template v-else-if="isLoading">
      <div class="rounded-xl border border-border-light bg-bg-card p-5">
        <SkeletonLoader :rows="6" />
      </div>
    </template>

    <template v-else>
      <!-- Key Metrics Overview -->
      <ReportSection title="Key Performance Indicators" description="High-level metrics for the current period">
        <ReportMetricCard v-for="(metric, index) in keyMetrics" :key="index" :label="metric.label" :value="metric.value" :unit="metric.unit" :change="metric.change" :color="metric.color" />
      </ReportSection>

      <!-- Projects Status Distribution -->
      <ReportSection title="Project Status Distribution" description="Breakdown of projects by current status" fullWidth>
        <Card>
          <BarChart :data="projectsByStatus" :height="350" />
        </Card>
      </ReportSection>

      <!-- Payments Received Trend -->
      <ReportSection title="Payments Received Trend" description="Payments received over the past 6 months" fullWidth>
        <Card>
          <LineChart :data="paymentsReceivedTrend" :height="350" />
        </Card>
      </ReportSection>

      <!-- Contract Pipeline -->
      <ReportSection title="Contract Pipeline" description="Distribution of contracts by current status" fullWidth>
        <Card>
          <BarChart :data="contractsByStatus" :height="350" />
        </Card>
      </ReportSection>
    </template>

    <!-- Report Footer -->
    <div class="border-t border-border-light pt-6 text-center text-xs text-text-muted">
      <p>This report was automatically generated on {{ reportDate }}</p>
      <p class="mt-1">For questions or detailed analysis, contact the project management office.</p>
    </div>
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
