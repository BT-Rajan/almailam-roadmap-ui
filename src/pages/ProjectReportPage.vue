<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import ReportHeader from '@/components/reports/ReportHeader.vue'
import ReportSection from '@/components/reports/ReportSection.vue'
import ReportMetricCard from '@/components/reports/ReportMetricCard.vue'
import ProgressChart from '@/components/reports/ProgressChart.vue'
import Card from '@/components/common/Card.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import { reportService } from '@/services/reportService'
import { useProjectStore } from '@/stores/projectStore'
import { useToastStore } from '@/stores/toastStore'
import type { Client } from '@/types/Client'
import type { Project } from '@/types/Project'
import type { ReportSection as ReportSectionData } from '@/types/Report'
import type { BadgeVariant } from '@/types/Ui'
import { formatDate } from '@/utils/dateFormatter'
import { getWorkflowStageLabel } from '@/utils/projectHelpers'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()
const toastStore = useToastStore()
const { t } = useI18n()

const reportDate = new Date().toLocaleDateString('en-US', {
  year: 'numeric',
  month: 'long',
  day: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
})

const isLoading = ref(true)
const error = ref<string | undefined>(undefined)
const project = ref<Project | undefined>(undefined)
const client = ref<Client | undefined>(undefined)
const sections = ref<ReportSectionData[]>([])

async function loadReport(): Promise<void> {
  isLoading.value = true
  error.value = undefined
  try {
    if (projectStore.projects.length === 0) {
      await projectStore.loadProjects()
    }
    const requestedId = route.params.projectId as string | undefined
    const resolved = requestedId
      ? projectStore.projects.find((item) => item.id === requestedId)
      : (projectStore.projects.find((item) => item.status === 'Active') ?? projectStore.projects[0])

    if (!resolved) {
      error.value = 'No project is available to report on yet.'
      return
    }

    project.value = resolved
    client.value = projectStore.getClientById(resolved.clientId)
    sections.value = await reportService.getProjectReport(resolved.id)
  } catch {
    error.value = 'Unable to load the project report. Please try again.'
  } finally {
    isLoading.value = false
  }
}

onMounted(loadReport)
watch(() => route.params.projectId, loadReport)

const statusVariant = (status: string) => {
  const variants: Record<string, BadgeVariant> = {
    Active: 'info',
    Completed: 'success',
    'On Hold': 'warning',
    Cancelled: 'danger',
  }
  return variants[status] || 'neutral'
}

const STATUS_LABEL_KEYS: Record<string, string> = {
  Active: 'project.status.active',
  'On Hold': 'project.status.onHold',
  Cancelled: 'project.status.cancelled',
}
function statusLabel(status: string): string {
  return t(STATUS_LABEL_KEYS[status] ?? status)
}

const STAGE_LABEL_KEYS: Record<string, string> = {
  Requirement: 'project.stage.requirement',
  Quotation: 'project.stage.quotation',
  'Payment Plan': 'project.stage.paymentPlan',
  Contract: 'project.stage.contract',
  Design: 'project.stage.design',
  Supervision: 'project.stage.supervision',
  'Government Submission': 'project.stage.governmentSubmission',
}
function stageLabel(stage: string): string {
  return t(STAGE_LABEL_KEYS[stage] ?? getWorkflowStageLabel(stage))
}

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
      <BaseButton variant="ghost" size="sm" @click="goBack"> ← {{ t('project.reportPage.back') }} </BaseButton>
    </div>

    <ErrorState v-if="error" :description="error" @retry="loadReport" />

    <template v-else-if="isLoading">
      <div class="rounded-xl border border-border-light bg-bg-card p-5">
        <SkeletonLoader :rows="6" />
      </div>
    </template>

    <template v-else-if="project">
      <ReportHeader
        :title="project.projectName"
        :subtitle="`Client: ${client?.companyName ?? 'Unassigned'} | ID: ${project.projectNo}`"
        :generated-date="reportDate"
        @download="handleExport"
      />

      <!-- Project Status Summary -->
      <Card>
        <div class="grid grid-cols-1 tablet:grid-cols-4 gap-4">
          <div>
            <p class="text-xs text-text-secondary uppercase font-medium">{{ t('project.reportPage.status') }}</p>
            <div class="mt-2">
              <StatusBadge :label="statusLabel(project.status)" :variant="statusVariant(project.status)" />
            </div>
          </div>
          <div>
            <p class="text-xs text-text-secondary uppercase font-medium">{{ t('project.reportPage.duration') }}</p>
            <p class="text-sm font-medium text-text-primary mt-2">
              {{ formatDate(project.startDate) }} – {{ formatDate(project.targetDate) }}
            </p>
          </div>
          <div>
            <p class="text-xs text-text-secondary uppercase font-medium">{{ t('project.reportPage.currentStage') }}</p>
            <p class="text-sm font-medium text-text-primary mt-2">{{ stageLabel(project.currentStage) }}</p>
          </div>
          <div>
            <p class="text-xs text-text-secondary uppercase font-medium">{{ t('project.reportPage.fieldEngineer') }}</p>
            <p class="text-sm font-medium text-text-primary mt-2">{{ project.engineer }}</p>
          </div>
        </div>
      </Card>

      <!-- Overall Progress -->
      <ReportSection :title="t('project.reportPage.overallProgress')" fullWidth>
        <div class="grid grid-cols-1 tablet:grid-cols-3 gap-8 justify-items-center">
          <ProgressChart :value="project.progress" :label="t('project.reportPage.overallCompletion')" color="#3B82F6" size="md" />
        </div>
      </ReportSection>

      <!-- Backend-provided sections: task/document/submission breakdowns and
           finance (when a financial agreement exists). "Project Overview" is
           skipped here since its fields are already in the status card above. -->
      <ReportSection
        v-for="section in sections.filter((s) => s.title !== 'Project Overview')"
        :key="section.title"
        :title="section.title"
        :description="section.description"
        fullWidth
      >
        <ReportMetricCard
          v-for="(metric, index) in section.metrics"
          :key="index"
          :label="metric.label"
          :value="metric.value"
          :unit="metric.unit"
          :change="metric.change"
          :color="metric.color"
        />
      </ReportSection>
    </template>

    <!-- Report Footer -->
    <div v-if="project" class="border-t border-border-light pt-6 text-center text-xs text-text-muted">
      <p>{{ t('project.reportPage.footerFor', { name: project.projectName }) }}</p>
      <p class="mt-1">{{ t('project.reportPage.generatedOn', { date: reportDate }) }}</p>
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
