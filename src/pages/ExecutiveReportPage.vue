<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
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
const { t } = useI18n()
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
      <BaseButton variant="ghost" size="sm" @click="goBack"> ← {{ t('report.back') }} </BaseButton>
    </div>

    <ReportHeader :title="t('report.executivePage.pageTitle')" :subtitle="t('report.executivePage.pageSubtitle')" :generated-date="reportDate" @download="handleExport" />

    <ErrorState v-if="error" :description="error" @retry="loadReport" />

    <template v-else-if="isLoading">
      <div class="rounded-xl border border-border-light bg-bg-card p-5">
        <SkeletonLoader :rows="6" />
      </div>
    </template>

    <template v-else>
      <!-- Key Metrics Overview -->
      <ReportSection :title="t('report.executivePage.kpiTitle')" :description="t('report.executivePage.kpiDescription')">
        <ReportMetricCard v-for="(metric, index) in keyMetrics" :key="index" :label="metric.label" :value="metric.value" :unit="metric.unit" :change="metric.change" :color="metric.color" />
      </ReportSection>

      <!-- Projects Status Distribution -->
      <ReportSection :title="t('report.executivePage.projectStatusTitle')" :description="t('report.executivePage.projectStatusDescription')" fullWidth>
        <Card>
          <BarChart :data="projectsByStatus" :height="350" />
        </Card>
      </ReportSection>

      <!-- Payments Received Trend -->
      <ReportSection :title="t('report.executivePage.paymentsTrendTitle')" :description="t('report.executivePage.paymentsTrendDescription')" fullWidth>
        <Card>
          <LineChart :data="paymentsReceivedTrend" :height="350" />
        </Card>
      </ReportSection>

      <!-- Contract Pipeline -->
      <ReportSection :title="t('report.executivePage.contractPipelineTitle')" :description="t('report.executivePage.contractPipelineDescription')" fullWidth>
        <Card>
          <BarChart :data="contractsByStatus" :height="350" />
        </Card>
      </ReportSection>
    </template>

    <!-- Report Footer -->
    <div class="border-t border-border-light pt-6 text-center text-xs text-text-muted">
      <p>{{ t('report.executivePage.footerGenerated', { date: reportDate }) }}</p>
      <p class="mt-1">{{ t('report.executivePage.footerContact') }}</p>
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
