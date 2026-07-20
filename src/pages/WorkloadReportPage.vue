<script setup lang="ts">
import { useRouter } from 'vue-router'
import ReportHeader from '@/components/reports/ReportHeader.vue'
import ReportSection from '@/components/reports/ReportSection.vue'
import ReportMetricCard from '@/components/reports/ReportMetricCard.vue'
import BarChart from '@/components/reports/BarChart.vue'
import ProgressChart from '@/components/reports/ProgressChart.vue'
import Card from '@/components/common/Card.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import type { ChartDataPoint } from '@/types/Report'

const router = useRouter()

const reportDate = new Date().toLocaleDateString('en-US', {
  year: 'numeric',
  month: 'long',
  day: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
})

// Overall Team Metrics
const teamMetrics = [
  {
    label: 'Total Team Members',
    value: 3,
    change: { direction: 'up' as const, percentage: 0 },
    color: 'primary',
  },
  {
    label: 'Average Utilization',
    value: '82%',
    change: { direction: 'up' as const, percentage: 4 },
    color: 'info',
  },
  {
    label: 'Overallocated Staff',
    value: 0,
    unit: 'persons',
    change: { direction: 'down' as const, percentage: 0 },
    color: 'warning',
  },
  {
    label: 'Capacity Available',
    value: '18%',
    change: { direction: 'up' as const, percentage: 6 },
    color: 'neutral',
  },
]

// Workload by Discipline
const workloadByDept: ChartDataPoint[] = [
  { label: 'Structural Engineering', value: 2, color: '#8B5CF6' },
  { label: 'MEP Engineering', value: 2, color: '#06B6D4' },
  { label: 'Fire & Safety', value: 1, color: '#F59E0B' },
]

// Team Member Allocation
const teamMembers = [
  { name: 'Layla Haddad', role: 'Structural Engineer', department: 'Structural Engineering', allocation: 90, capacity: 100, projects: 2, overallocated: false },
  { name: 'Ahmed Rashid', role: 'MEP Engineer', department: 'MEP Engineering', allocation: 88, capacity: 100, projects: 2, overallocated: false },
  { name: 'Mohammed Iqbal', role: 'Fire & Safety Engineer', department: 'Fire & Safety', allocation: 68, capacity: 100, projects: 1, overallocated: false },
]

// Discipline Utilization
const deptUtilization: ChartDataPoint[] = [
  { label: 'Structural Engineering', value: 90, color: '#8B5CF6' },
  { label: 'MEP Engineering', value: 88, color: '#06B6D4' },
  { label: 'Fire & Safety', value: 68, color: '#F59E0B' },
]

const handleExport = () => {
  console.log('Export would trigger here - PDF generation needs html2pdf library')
}

const goBack = () => {
  router.back()
}

const getRowColor = (member: (typeof teamMembers)[number]) => {
  if (member.overallocated) return 'bg-danger-50 border-danger-200'
  if (member.allocation >= 90) return 'bg-warning-50 border-warning-200'
  return 'bg-neutral-50'
}

const getAllocationColor = (allocation: number) => {
  if (allocation > 100) return '#EF4444'
  if (allocation >= 90) return '#F59E0B'
  return '#10B981'
}
</script>

<template>
  <div class="max-w-6xl mx-auto space-y-8 pb-12">
    <div class="flex items-center justify-between">
      <BaseButton variant="ghost" size="sm" @click="goBack"> ← Back </BaseButton>
    </div>

    <ReportHeader title="Team Workload Summary" subtitle="Current capacity and allocation analysis" :generated-date="reportDate" @download="handleExport" />

    <!-- Team Overview Metrics -->
    <ReportSection title="Team Overview" description="High-level team capacity and utilization metrics">
      <ReportMetricCard v-for="(metric, index) in teamMetrics" :key="index" :label="metric.label" :value="metric.value" :unit="metric.unit" :change="metric.change" :color="metric.color" />
    </ReportSection>

    <!-- Overall Team Health -->
    <ReportSection title="Team Capacity Status" fullWidth>
      <div class="grid grid-cols-1 tablet:grid-cols-2 gap-8 justify-items-center">
        <ProgressChart :value="82" label="Average Utilization" color="#3B82F6" size="md" />
        <ProgressChart :value="18" label="Capacity Available" color="#10B981" size="md" />
      </div>
    </ReportSection>

    <!-- Workload by Discipline -->
    <ReportSection title="Workload by Discipline" description="Active project count by engineering discipline" fullWidth>
      <Card>
        <BarChart :data="workloadByDept" :height="350" />
      </Card>
    </ReportSection>

    <!-- Discipline Utilization -->
    <ReportSection title="Discipline Utilization Rates" description="Allocation percentage by engineering discipline" fullWidth>
      <Card>
        <BarChart :data="deptUtilization" :height="350" />
      </Card>
    </ReportSection>

    <!-- Individual Team Member Details -->
    <ReportSection title="Team Member Allocation Details" fullWidth>
      <div class="space-y-3">
        <div
          v-for="member in teamMembers"
          :key="member.name"
          :class="['p-4 rounded-lg border transition-all', getRowColor(member)]"
        >
          <div class="grid grid-cols-1 tablet:grid-cols-3 gap-4">
            <div>
              <p class="text-sm font-semibold text-neutral-900">{{ member.name }}</p>
              <p class="text-xs text-neutral-600 mt-1">{{ member.role }}</p>
              <p class="text-xs text-neutral-500 mt-0.5">{{ member.department }}</p>
            </div>
            <div>
              <p class="text-xs text-neutral-600 uppercase font-medium mb-2">Allocation</p>
              <div class="space-y-1">
                <div class="h-2 bg-neutral-200 rounded-full overflow-hidden">
                  <div :style="{ width: `${Math.min(member.allocation, 120)}%`, backgroundColor: getAllocationColor(member.allocation) }" class="h-full rounded-full transition-all" />
                </div>
                <div class="flex items-center justify-between text-xs">
                  <span :class="member.allocation > 100 ? 'text-danger-600 font-semibold' : 'text-neutral-600'">
                    {{ member.allocation }}%
                  </span>
                  <span v-if="member.overallocated" class="text-danger-600 font-medium">⚠ Overallocated</span>
                </div>
              </div>
            </div>
            <div class="flex items-center gap-4">
              <div>
                <p class="text-xs text-neutral-600 uppercase font-medium">Projects</p>
                <p class="text-lg font-bold text-neutral-900 mt-1">{{ member.projects }}</p>
              </div>
              <div>
                <p class="text-xs text-neutral-600 uppercase font-medium">Capacity</p>
                <p class="text-lg font-bold text-neutral-900 mt-1">{{ member.capacity }}h</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </ReportSection>

    <!-- Recommendations -->
    <ReportSection title="Recommendations" fullWidth>
      <div class="space-y-3">
        <Card class="bg-info-50 border border-info-200">
          <div class="space-y-2">
            <h3 class="font-semibold text-info-900">ℹ Balanced Workload</h3>
            <p class="text-sm text-info-800">No engineers are currently over their capacity threshold. Structural and MEP engineering carry the highest load at 88-90% utilization.</p>
          </div>
        </Card>
        <Card class="bg-success-50 border border-success-200">
          <div class="space-y-2">
            <h3 class="font-semibold text-success-900">✓ Hiring Opportunity</h3>
            <p class="text-sm text-success-800">Fire &amp; Safety has the lowest headcount at 68% utilization. An additional fire safety engineer would support the growing government submission workload.</p>
          </div>
        </Card>
        <Card class="bg-warning-50 border border-warning-200">
          <div class="space-y-2">
            <h3 class="font-semibold text-warning-900">⚠ Watch List</h3>
            <p class="text-sm text-warning-800">Layla Haddad and Ahmed Rashid are each carrying two active projects. Monitor upcoming enquiries before assigning further work to either engineer.</p>
          </div>
        </Card>
      </div>
    </ReportSection>

    <!-- Report Footer -->
    <div class="border-t border-border-light pt-6 text-center text-xs text-neutral-500">
      <p>Team Workload Report</p>
      <p class="mt-1">Generated on {{ reportDate }}</p>
      <p class="mt-1">Based on current project assignments and team capacity data</p>
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
