<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
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
const { t } = useI18n()

const reportDate = new Date().toLocaleDateString('en-US', {
  year: 'numeric',
  month: 'long',
  day: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
})

// Overall Team Metrics
const teamMetrics = computed(() => [
  {
    label: t('report.workloadPage.totalTeamMembers'),
    value: 3,
    change: { direction: 'up' as const, percentage: 0 },
    color: 'primary',
  },
  {
    label: t('report.workloadPage.averageUtilization'),
    value: '82%',
    change: { direction: 'up' as const, percentage: 4 },
    color: 'info',
  },
  {
    label: t('report.workloadPage.overallocatedStaff'),
    value: 0,
    unit: t('report.workloadPage.personsUnit'),
    change: { direction: 'down' as const, percentage: 0 },
    color: 'warning',
  },
  {
    label: t('report.workloadPage.capacityAvailable'),
    value: '18%',
    change: { direction: 'up' as const, percentage: 6 },
    color: 'neutral',
  },
])

// Workload by Discipline
const workloadByDept = computed<ChartDataPoint[]>(() => [
  { label: t('report.workloadPage.disciplineStructural'), value: 2, color: '#8B5CF6' },
  { label: t('report.workloadPage.disciplineMep'), value: 2, color: '#06B6D4' },
  { label: t('report.workloadPage.disciplineFireSafety'), value: 1, color: '#F59E0B' },
])

// Team Member Allocation
const teamMembers = computed(() => [
  {
    name: 'Layla Haddad',
    role: t('report.workloadPage.roleStructuralEngineer'),
    department: t('report.workloadPage.disciplineStructural'),
    allocation: 90,
    capacity: 100,
    projects: 2,
    overallocated: false,
  },
  {
    name: 'Ahmed Rashid',
    role: t('report.workloadPage.roleMepEngineer'),
    department: t('report.workloadPage.disciplineMep'),
    allocation: 88,
    capacity: 100,
    projects: 2,
    overallocated: false,
  },
  {
    name: 'Mohammed Iqbal',
    role: t('report.workloadPage.roleFireSafetyEngineer'),
    department: t('report.workloadPage.disciplineFireSafety'),
    allocation: 68,
    capacity: 100,
    projects: 1,
    overallocated: false,
  },
])

// Discipline Utilization
const deptUtilization = computed<ChartDataPoint[]>(() => [
  { label: t('report.workloadPage.disciplineStructural'), value: 90, color: '#8B5CF6' },
  { label: t('report.workloadPage.disciplineMep'), value: 88, color: '#06B6D4' },
  { label: t('report.workloadPage.disciplineFireSafety'), value: 68, color: '#F59E0B' },
])

const handleExport = () => {
  console.log('Export would trigger here - PDF generation needs html2pdf library')
}

const goBack = () => {
  router.back()
}

const getRowColor = (member: (typeof teamMembers.value)[number]) => {
  if (member.overallocated) return 'bg-danger-50 border-danger-200'
  if (member.allocation >= 90) return 'bg-warning-50 border-warning-200'
  return 'bg-bg-secondary'
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
      <BaseButton variant="ghost" size="sm" @click="goBack"> ← {{ t('report.back') }} </BaseButton>
    </div>

    <ReportHeader :title="t('report.workloadPage.pageTitle')" :subtitle="t('report.workloadPage.pageSubtitle')" :generated-date="reportDate" @download="handleExport" />

    <!-- Team Overview Metrics -->
    <ReportSection :title="t('report.workloadPage.teamOverviewTitle')" :description="t('report.workloadPage.teamOverviewDescription')">
      <ReportMetricCard v-for="(metric, index) in teamMetrics" :key="index" :label="metric.label" :value="metric.value" :unit="metric.unit" :change="metric.change" :color="metric.color" />
    </ReportSection>

    <!-- Overall Team Health -->
    <ReportSection :title="t('report.workloadPage.teamCapacityStatusTitle')" fullWidth>
      <div class="grid grid-cols-1 tablet:grid-cols-2 gap-8 justify-items-center">
        <ProgressChart :value="82" :label="t('report.workloadPage.averageUtilization')" color="#3B82F6" size="md" />
        <ProgressChart :value="18" :label="t('report.workloadPage.capacityAvailable')" color="#10B981" size="md" />
      </div>
    </ReportSection>

    <!-- Workload by Discipline -->
    <ReportSection :title="t('report.workloadPage.workloadByDisciplineTitle')" :description="t('report.workloadPage.workloadByDisciplineDescription')" fullWidth>
      <Card>
        <BarChart :data="workloadByDept" :height="350" />
      </Card>
    </ReportSection>

    <!-- Discipline Utilization -->
    <ReportSection :title="t('report.workloadPage.disciplineUtilizationTitle')" :description="t('report.workloadPage.disciplineUtilizationDescription')" fullWidth>
      <Card>
        <BarChart :data="deptUtilization" :height="350" />
      </Card>
    </ReportSection>

    <!-- Individual Team Member Details -->
    <ReportSection :title="t('report.workloadPage.teamMemberDetailsTitle')" fullWidth>
      <div class="space-y-3">
        <div
          v-for="member in teamMembers"
          :key="member.name"
          :class="['p-4 rounded-lg border transition-all', getRowColor(member)]"
        >
          <div class="grid grid-cols-1 tablet:grid-cols-3 gap-4">
            <div>
              <p class="text-sm font-semibold text-text-primary">{{ member.name }}</p>
              <p class="text-xs text-text-secondary mt-1">{{ member.role }}</p>
              <p class="text-xs text-text-muted mt-0.5">{{ member.department }}</p>
            </div>
            <div>
              <p class="text-xs text-text-secondary uppercase font-medium mb-2">{{ t('report.workloadPage.allocation') }}</p>
              <div class="space-y-1">
                <div class="h-2 bg-border-default rounded-full overflow-hidden">
                  <div :style="{ width: `${Math.min(member.allocation, 120)}%`, backgroundColor: getAllocationColor(member.allocation) }" class="h-full rounded-full transition-all" />
                </div>
                <div class="flex items-center justify-between text-xs">
                  <span :class="member.allocation > 100 ? 'text-danger-600 font-semibold' : 'text-text-secondary'">
                    {{ member.allocation }}%
                  </span>
                  <span v-if="member.overallocated" class="text-danger-600 font-medium">⚠ {{ t('report.workloadPage.overallocatedBadge') }}</span>
                </div>
              </div>
            </div>
            <div class="flex items-center gap-4">
              <div>
                <p class="text-xs text-text-secondary uppercase font-medium">{{ t('report.workloadPage.projects') }}</p>
                <p class="text-lg font-bold text-text-primary mt-1">{{ member.projects }}</p>
              </div>
              <div>
                <p class="text-xs text-text-secondary uppercase font-medium">{{ t('report.workloadPage.capacity') }}</p>
                <p class="text-lg font-bold text-text-primary mt-1">{{ member.capacity }}{{ t('report.workloadPage.hoursUnit') }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </ReportSection>

    <!-- Recommendations -->
    <ReportSection :title="t('report.workloadPage.recommendationsTitle')" fullWidth>
      <div class="space-y-3">
        <Card class="bg-info-50 border border-info-200">
          <div class="space-y-2">
            <h3 class="font-semibold text-info-900">ℹ {{ t('report.workloadPage.balancedWorkloadTitle') }}</h3>
            <p class="text-sm text-info-800">{{ t('report.workloadPage.balancedWorkloadText') }}</p>
          </div>
        </Card>
        <Card class="bg-success-50 border border-success-200">
          <div class="space-y-2">
            <h3 class="font-semibold text-success-900">✓ {{ t('report.workloadPage.hiringOpportunityTitle') }}</h3>
            <p class="text-sm text-success-800">{{ t('report.workloadPage.hiringOpportunityText') }}</p>
          </div>
        </Card>
        <Card class="bg-warning-50 border border-warning-200">
          <div class="space-y-2">
            <h3 class="font-semibold text-warning-900">⚠ {{ t('report.workloadPage.watchListTitle') }}</h3>
            <p class="text-sm text-warning-800">{{ t('report.workloadPage.watchListText') }}</p>
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
