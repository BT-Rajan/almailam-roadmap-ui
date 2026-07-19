<script setup lang="ts">
import { useRouter } from 'vue-router'
import ReportHeader from '@/components/reports/ReportHeader.vue'
import ReportSection from '@/components/reports/ReportSection.vue'
import ReportMetricCard from '@/components/reports/ReportMetricCard.vue'
import BarChart from '@/components/reports/BarChart.vue'
import LineChart from '@/components/reports/LineChart.vue'
import ProgressChart from '@/components/reports/ProgressChart.vue'
import Card from '@/components/common/Card.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import type { ChartDataPoint, LineChartData } from '@/types/Report'

const router = useRouter()

const reportDate = new Date().toLocaleDateString('en-US', {
  year: 'numeric',
  month: 'long',
  day: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
})

// Key Metrics
const keyMetrics = [
  {
    label: 'Total Projects',
    value: 24,
    unit: 'active',
    change: { direction: 'up' as const, percentage: 15 },
    color: 'primary',
  },
  {
    label: 'Project Completion Rate',
    value: '87%',
    change: { direction: 'up' as const, percentage: 8 },
    color: 'success',
  },
  {
    label: 'Team Utilization',
    value: '92%',
    change: { direction: 'down' as const, percentage: 2 },
    color: 'info',
  },
  {
    label: 'Budget Variance',
    value: '+5%',
    change: { direction: 'down' as const, percentage: 12 },
    color: 'warning',
  },
]

// Projects by Status
const projectsByStatus: ChartDataPoint[] = [
  { label: 'Active', value: 18, color: '#3B82F6' },
  { label: 'Pending', value: 4, color: '#F59E0B' },
  { label: 'On Hold', value: 2, color: '#EF4444' },
]

// Monthly Delivery Trend
const deliveryTrend: LineChartData[] = [
  { x: 'Jan', value: 12 },
  { x: 'Feb', value: 15 },
  { x: 'Mar', value: 14 },
  { x: 'Apr', value: 18 },
  { x: 'May', value: 22 },
  { x: 'Jun', value: 20 },
]

// Resource Allocation
const resourceAllocation: ChartDataPoint[] = [
  { label: 'Development', value: 45, color: '#8B5CF6' },
  { label: 'QA', value: 25, color: '#06B6D4' },
  { label: 'Design', value: 15, color: '#EC4899' },
  { label: 'Management', value: 15, color: '#14B8A6' },
]

const handleExport = () => {
  const element = document.documentElement
  const opt = {
    margin: 10,
    filename: `executive-report-${new Date().toISOString().split('T')[0]}.pdf`,
    image: { type: 'jpeg', quality: 0.98 },
    html2canvas: { scale: 2 },
    jsPDF: { orientation: 'portrait', unit: 'mm', format: 'a4' },
  }
  console.log('Export would trigger here - PDF generation needs html2pdf library')
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

    <ReportHeader title="Executive Summary Report" subtitle="Q2 2024 Performance Overview" :generated-date="reportDate" @download="handleExport" />

    <!-- Key Metrics Overview -->
    <ReportSection title="Key Performance Indicators" description="High-level metrics for the current period">
      <ReportMetricCard v-for="(metric, index) in keyMetrics" :key="index" :label="metric.label" :value="metric.value" :unit="metric.unit" :change="metric.change" :color="metric.color" />
    </ReportSection>

    <!-- Progress Overview -->
    <ReportSection title="Overall Health Metrics" fullWidth>
      <div class="grid grid-cols-1 tablet:grid-cols-3 gap-8 justify-items-center">
        <ProgressChart :value="87" label="Project Completion" color="#10B981" size="md" />
        <ProgressChart :value="92" label="Team Utilization" color="#3B82F6" size="md" />
        <ProgressChart :value="78" label="Budget Tracking" color="#F59E0B" size="md" />
      </div>
    </ReportSection>

    <!-- Projects Status Distribution -->
    <ReportSection title="Project Status Distribution" description="Breakdown of projects by current status" fullWidth>
      <Card>
        <BarChart :data="projectsByStatus" :height="350" />
      </Card>
    </ReportSection>

    <!-- Delivery Trend -->
    <ReportSection title="Delivery Trend Analysis" description="Monthly completed deliverables over the past 6 months" fullWidth>
      <Card>
        <LineChart :data="deliveryTrend" :height="350" />
      </Card>
    </ReportSection>

    <!-- Resource Allocation -->
    <ReportSection title="Resource Allocation" description="Distribution of team resources across functional areas" fullWidth>
      <Card>
        <BarChart :data="resourceAllocation" :height="350" />
      </Card>
    </ReportSection>

    <!-- Summary Insights -->
    <ReportSection title="Key Insights & Recommendations" fullWidth>
      <div class="space-y-3">
        <Card class="bg-success-50 border border-success-200">
          <div class="space-y-2">
            <h3 class="font-semibold text-success-900">✓ Strong Performance</h3>
            <p class="text-sm text-success-800">87% project completion rate demonstrates consistent delivery capability and effective project management.</p>
          </div>
        </Card>
        <Card class="bg-warning-50 border border-warning-200">
          <div class="space-y-2">
            <h3 class="font-semibold text-warning-900">⚠ Resource Optimization Needed</h3>
            <p class="text-sm text-warning-800">Team utilization at 92% with 4 pending projects. Consider capacity planning for next quarter.</p>
          </div>
        </Card>
        <Card class="bg-info-50 border border-info-200">
          <div class="space-y-2">
            <h3 class="font-semibold text-info-900">ℹ Budget Status</h3>
            <p class="text-sm text-info-800">5% positive variance indicates efficient cost management. Current spending aligns with projections.</p>
          </div>
        </Card>
      </div>
    </ReportSection>

    <!-- Report Footer -->
    <div class="border-t border-border-light pt-6 text-center text-xs text-neutral-500">
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
