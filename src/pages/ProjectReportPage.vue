<script setup lang="ts">
import { useRouter } from 'vue-router'
import ReportHeader from '@/components/reports/ReportHeader.vue'
import ReportSection from '@/components/reports/ReportSection.vue'
import ReportMetricCard from '@/components/reports/ReportMetricCard.vue'
import BarChart from '@/components/reports/BarChart.vue'
import ProgressChart from '@/components/reports/ProgressChart.vue'
import Card from '@/components/common/Card.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import type { ChartDataPoint } from '@/types/Report'
import type { BadgeVariant } from '@/types/Ui'

const router = useRouter()

// Project Data - sourced from the Marina Bay Hotel Renovation project (PRJ-2026-003)
const project = {
  name: 'Marina Bay Hotel Renovation',
  client: 'Marina Bay Hospitality Group',
  projectId: 'PRJ-2026-003',
  status: 'active',
  startDate: '2026-03-10',
  endDate: '2026-10-05',
  progress: 42,
  budget: {
    allocated: 720000,
    spent: 302400,
    currency: 'KWD',
  },
  team: {
    assigned: 4,
    utilization: 90,
  },
  riskScore: 3,
}

const reportDate = new Date().toLocaleDateString('en-US', {
  year: 'numeric',
  month: 'long',
  day: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
})

// Project Overview Metrics
const projectMetrics = [
  {
    label: 'Overall Progress',
    value: `${project.progress}%`,
    change: { direction: 'up' as const, percentage: 12 },
    color: 'primary',
  },
  {
    label: 'Budget Utilization',
    value: '42%',
    change: { direction: 'down' as const, percentage: 3 },
    color: 'info',
  },
  {
    label: 'Team Utilization',
    value: `${project.team.utilization}%`,
    change: { direction: 'up' as const, percentage: 8 },
    color: 'success',
  },
  {
    label: 'Risk Level',
    value: 'Medium',
    color: 'warning',
  },
]

// Task Completion Status
const taskStatus: ChartDataPoint[] = [
  { label: 'Completed', value: 42, color: '#10B981' },
  { label: 'In Progress', value: 28, color: '#3B82F6' },
  { label: 'Pending', value: 15, color: '#F59E0B' },
  { label: 'Blocked', value: 5, color: '#EF4444' },
]

// Deliverables by Category
const deliverables: ChartDataPoint[] = [
  { label: 'Design & Planning', value: 18, color: '#8B5CF6' },
  { label: 'Structural Works', value: 12, color: '#06B6D4' },
  { label: 'MEP Systems', value: 10, color: '#EC4899' },
  { label: 'Finishing & QA', value: 8, color: '#14B8A6' },
]

// Timeline Status
const timelineData = [
  { phase: 'Phase 1', completedDays: 85, totalDays: 90, status: 'Completed' },
  { phase: 'Phase 2', completedDays: 45, totalDays: 60, status: 'In Progress' },
  { phase: 'Phase 3', completedDays: 0, totalDays: 40, status: 'Pending' },
]

const statusVariant = (status: string) => {
  const variants: Record<string, BadgeVariant> = {
    active: 'info',
    completed: 'success',
    'on-hold': 'warning',
    blocked: 'danger',
  }
  return variants[status] || 'neutral'
}

const handleExport = () => {
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

    <ReportHeader :title="project.name" :subtitle="`Client: ${project.client} | ID: ${project.projectId}`" :generated-date="reportDate" @download="handleExport" />

    <!-- Project Status Summary -->
    <Card>
      <div class="grid grid-cols-1 tablet:grid-cols-4 gap-4">
        <div>
          <p class="text-xs text-neutral-600 uppercase font-medium">Status</p>
          <div class="mt-2">
            <StatusBadge :label="project.status" :variant="statusVariant(project.status)" />
          </div>
        </div>
        <div>
          <p class="text-xs text-neutral-600 uppercase font-medium">Duration</p>
          <p class="text-sm font-medium text-neutral-900 mt-2">Mar 10 - Oct 5, 2026</p>
        </div>
        <div>
          <p class="text-xs text-neutral-600 uppercase font-medium">Team Size</p>
          <p class="text-sm font-medium text-neutral-900 mt-2">{{ project.team.assigned }} Members</p>
        </div>
        <div>
          <p class="text-xs text-neutral-600 uppercase font-medium">Budget Allocated</p>
          <p class="text-sm font-medium text-neutral-900 mt-2">KD {{ project.budget.allocated.toLocaleString() }}</p>
        </div>
      </div>
    </Card>

    <!-- Key Performance Metrics -->
    <ReportSection title="Key Performance Indicators" description="Project health and progress metrics">
      <ReportMetricCard v-for="(metric, index) in projectMetrics" :key="index" :label="metric.label" :value="metric.value" :change="metric.change" :color="metric.color" />
    </ReportSection>

    <!-- Progress Visualization -->
    <ReportSection title="Project Progress" fullWidth>
      <div class="grid grid-cols-1 tablet:grid-cols-3 gap-8 justify-items-center">
        <ProgressChart :value="project.progress" label="Overall Completion" color="#3B82F6" size="md" />
        <ProgressChart :value="Math.round(project.budget.spent / (project.budget.allocated / 100))" label="Budget Spent" color="#F59E0B" size="md" />
        <ProgressChart :value="project.team.utilization" label="Team Utilization" color="#10B981" size="md" />
      </div>
    </ReportSection>

    <!-- Task Status -->
    <ReportSection title="Task Status Breakdown" description="Distribution of tasks by current status" fullWidth>
      <Card>
        <BarChart :data="taskStatus" :height="350" />
      </Card>
    </ReportSection>

    <!-- Deliverables -->
    <ReportSection title="Deliverables by Category" description="Work items distribution across project components" fullWidth>
      <Card>
        <BarChart :data="deliverables" :height="350" />
      </Card>
    </ReportSection>

    <!-- Timeline Phases -->
    <ReportSection title="Project Phases Timeline" fullWidth>
      <div class="space-y-4">
        <div v-for="phase in timelineData" :key="phase.phase" class="space-y-2">
          <div class="flex items-center justify-between">
            <span class="text-sm font-medium text-neutral-900">{{ phase.phase }}</span>
            <span class="text-xs text-neutral-500">{{ phase.completedDays }}/{{ phase.totalDays }} days</span>
          </div>
          <div class="relative h-2 bg-neutral-200 rounded-full overflow-hidden">
            <div class="absolute inset-y-0 left-0 bg-primary-500 rounded-full transition-all" :style="{ width: `${(phase.completedDays / phase.totalDays) * 100}%` }" />
          </div>
          <div class="flex justify-between text-xs text-neutral-500">
            <span>Progress: {{ Math.round((phase.completedDays / phase.totalDays) * 100) }}%</span>
            <span>{{ phase.status }}</span>
          </div>
        </div>
      </div>
    </ReportSection>

    <!-- Risk Assessment -->
    <ReportSection title="Risk Assessment" fullWidth>
      <Card class="bg-warning-50 border border-warning-200">
        <div class="space-y-3">
          <div class="flex items-start gap-3">
            <span class="text-lg">⚠</span>
            <div class="flex-1">
              <h3 class="font-semibold text-warning-900">Potential Schedule Slip</h3>
              <p class="text-sm text-warning-800 mt-1">Phase 2 running 5 days behind. Recommend resource reallocation to maintain Q4 delivery.</p>
            </div>
          </div>
          <div class="flex items-start gap-3">
            <span class="text-lg">⚠</span>
            <div class="flex-1">
              <h3 class="font-semibold text-warning-900">Budget Contingency Low</h3>
              <p class="text-sm text-warning-800 mt-1">42% of budget spent with 58% of work remaining. Monitor Phase 3 expenditure closely.</p>
            </div>
          </div>
        </div>
      </Card>
    </ReportSection>

    <!-- Budget Analysis -->
    <ReportSection title="Budget Analysis" fullWidth>
      <Card>
        <div class="space-y-4">
          <div class="space-y-2">
            <div class="flex items-center justify-between text-sm">
              <span class="text-neutral-600">Budget Allocated</span>
              <span class="font-medium">KD {{ project.budget.allocated.toLocaleString() }}</span>
            </div>
            <div class="flex items-center justify-between text-sm">
              <span class="text-neutral-600">Amount Spent</span>
              <span class="font-medium text-danger-600">KD {{ project.budget.spent.toLocaleString() }}</span>
            </div>
            <div class="flex items-center justify-between text-sm">
              <span class="text-neutral-600">Remaining</span>
              <span class="font-medium text-success-600">KD {{ (project.budget.allocated - project.budget.spent).toLocaleString() }}</span>
            </div>
          </div>
          <div class="h-2 bg-neutral-200 rounded-full overflow-hidden">
            <div class="h-full bg-danger-500 rounded-full" :style="{ width: `${(project.budget.spent / project.budget.allocated) * 100}%` }" />
          </div>
        </div>
      </Card>
    </ReportSection>

    <!-- Report Footer -->
    <div class="border-t border-border-light pt-6 text-center text-xs text-neutral-500">
      <p>Project Report for {{ project.name }}</p>
      <p class="mt-1">Generated on {{ reportDate }}</p>
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
