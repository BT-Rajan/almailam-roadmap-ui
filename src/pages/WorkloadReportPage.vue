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
    value: 42,
    change: { direction: 'up' as const, percentage: 5 },
    color: 'primary',
  },
  {
    label: 'Average Utilization',
    value: '86%',
    change: { direction: 'up' as const, percentage: 8 },
    color: 'info',
  },
  {
    label: 'Overallocated Staff',
    value: 5,
    unit: 'persons',
    change: { direction: 'down' as const, percentage: 2 },
    color: 'warning',
  },
  {
    label: 'Capacity Available',
    value: '14%',
    change: { direction: 'down' as const, percentage: 8 },
    color: 'neutral',
  },
]

// Workload by Department
const workloadByDept: ChartDataPoint[] = [
  { label: 'Development', value: 18, color: '#8B5CF6' },
  { label: 'QA & Testing', value: 8, color: '#06B6D4' },
  { label: 'Design', value: 6, color: '#EC4899' },
  { label: 'PM & Leadership', value: 4, color: '#14B8A6' },
  { label: 'Infrastructure', value: 3, color: '#F59E0B' },
  { label: 'Documentation', value: 3, color: '#EF4444' },
]

// Team Member Allocation
const teamMembers = [
  { name: 'Rajesh Kumar', role: 'Senior Developer', department: 'Development', allocation: 95, capacity: 100, projects: 2 },
  { name: 'Priya Sharma', role: 'QA Lead', department: 'QA & Testing', allocation: 100, capacity: 100, projects: 3, overallocated: true },
  { name: 'Arjun Singh', role: 'Project Manager', department: 'PM & Leadership', allocation: 85, capacity: 100, projects: 4 },
  { name: 'Anjali Verma', role: 'UI/UX Designer', department: 'Design', allocation: 90, capacity: 100, projects: 3 },
  { name: 'Vikram Patel', role: 'DevOps Engineer', department: 'Infrastructure', allocation: 75, capacity: 100, projects: 2 },
  { name: 'Sneha Gupta', role: 'Backend Developer', department: 'Development', allocation: 105, capacity: 100, projects: 3, overallocated: true },
  { name: 'Aditya Nair', role: 'Frontend Developer', department: 'Development', allocation: 88, capacity: 100, projects: 2 },
  { name: 'Divya Reddy', role: 'QA Engineer', department: 'QA & Testing', allocation: 92, capacity: 100, projects: 2 },
]

// Department Utilization
const deptUtilization: ChartDataPoint[] = [
  { label: 'Development', value: 92, color: '#8B5CF6' },
  { label: 'QA & Testing', value: 96, color: '#06B6D4' },
  { label: 'Design', value: 85, color: '#EC4899' },
  { label: 'Infrastructure', value: 78, color: '#14B8A6' },
  { label: 'Leadership', value: 82, color: '#F59E0B' },
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
        <ProgressChart :value="86" label="Average Utilization" color="#3B82F6" size="md" />
        <ProgressChart :value="14" label="Capacity Available" color="#10B981" size="md" />
      </div>
    </ReportSection>

    <!-- Workload by Department -->
    <ReportSection title="Headcount by Department" description="Distribution of team members across departments" fullWidth>
      <Card>
        <BarChart :data="workloadByDept" :height="350" />
      </Card>
    </ReportSection>

    <!-- Department Utilization -->
    <ReportSection title="Department Utilization Rates" description="Allocation percentage by department" fullWidth>
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
            <h3 class="font-semibold text-info-900">ℹ Resource Rebalancing</h3>
            <p class="text-sm text-info-800">5 team members are over their capacity threshold. Consider redistributing tasks to underutilized team members or pausing non-critical projects.</p>
          </div>
        </Card>
        <Card class="bg-success-50 border border-success-200">
          <div class="space-y-2">
            <h3 class="font-semibold text-success-900">✓ Hiring Opportunity</h3>
            <p class="text-sm text-success-800">14% available capacity exists. One additional QA engineer would improve team balance and reduce overallocation risk.</p>
          </div>
        </Card>
        <Card class="bg-warning-50 border border-warning-200">
          <div class="space-y-2">
            <h3 class="font-semibold text-warning-900">⚠ Critical Priority</h3>
            <p class="text-sm text-warning-800">Priya Sharma and Sneha Gupta are working above capacity. Recommend immediate workload review and task reassignment.</p>
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
