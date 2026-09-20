<script setup lang="ts">
import { CalendarClock } from '@lucide/vue'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import Card from '@/components/common/Card.vue'
import PaginatedList from '@/components/common/PaginatedList.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import WorkflowProgress from '@/components/project/WorkflowProgress.vue'
import type { Project, ProjectWorkspaceTabKey } from '@/types/Project'
import { formatDate } from '@/utils/dateFormatter'
import { getProjectStatusVariant, getWorkflowStageLabel, getWorkflowStageLabelKey } from '@/utils/projectHelpers'

// The client workspace's Overview: where each of this client's projects
// stands. One card per project -- its own workflow stepper (the same one
// the project's pages show, so "Design" or "Handover" reads identically
// here), plus the plain-words stage. Clicking a stage opens the project
// at that stage. Everything else about the client (profile, contacts,
// identification, documents) has its own tab and is deliberately not
// repeated here.
const props = defineProps<{
  projects: Project[]
}>()

const emit = defineEmits<{
  open: [projectId: string, tab?: ProjectWorkspaceTabKey]
}>()

const { t } = useI18n()

// Newest project first.
const sortedProjects = computed(() => [...props.projects].sort((a, b) => b.projectNo.localeCompare(a.projectNo)))

const STATUS_LABEL_KEYS: Record<string, string> = {
  Active: 'project.status.active',
  'On Hold': 'project.status.onHold',
  Cancelled: 'project.status.cancelled',
  Completed: 'project.status.completed',
}

function statusLabel(project: Project): string {
  return t(STATUS_LABEL_KEYS[project.status] ?? project.status)
}

function stageLabel(project: Project): string {
  return t(getWorkflowStageLabelKey(project.currentStage) ?? getWorkflowStageLabel(project.currentStage))
}
</script>

<template>
  <PaginatedList :items="sortedProjects" :page-size="5">
    <template #default="{ items }">
      <div class="flex flex-col gap-4">
        <Card v-for="project in items" :key="project.id">
          <div class="flex flex-col gap-4">
            <div class="flex flex-wrap items-start justify-between gap-3">
              <div class="flex min-w-0 flex-col gap-1">
                <p class="text-xs font-medium uppercase tracking-wide text-text-muted">{{ project.projectNo }} &middot; {{ project.service }}</p>
                <h3 class="text-base font-semibold leading-snug text-text-primary">{{ project.projectName }}</h3>
              </div>
              <div class="flex shrink-0 items-center gap-2">
                <StatusBadge :label="statusLabel(project)" :variant="getProjectStatusVariant(project.status)" show-dot />
                <BaseButton size="sm" variant="secondary" class="no-print" @click="emit('open', project.id)">
                  {{ t('client.projectStages.openProject') }}
                </BaseButton>
              </div>
            </div>

            <div class="flex flex-wrap items-center justify-between gap-2 text-sm">
              <p class="text-text-secondary">
                {{ t('client.projectStages.currentlyAt') }}
                <span class="font-semibold text-text-primary">{{ stageLabel(project) }}</span>
              </p>
              <p class="inline-flex items-center gap-1.5 text-xs text-text-muted">
                <CalendarClock class="h-3.5 w-3.5" />
                {{ t('client.projectStages.target', { date: formatDate(project.targetDate) }) }}
              </p>
            </div>

            <WorkflowProgress
              :current-stage="project.currentStage"
              :project-status="project.status"
              :includes-design="project.includesDesign"
              :includes-government-submission="project.includesGovernmentSubmission"
              :includes-supervision="project.includesSupervision"
              :selected-activities="project.selectedActivities"
              :selected-permits="project.selectedPermits"
              :selected-supervision-activities="project.selectedSupervisionActivities"
              @navigate-tab="(tab: ProjectWorkspaceTabKey) => emit('open', project.id, tab)"
            />
          </div>
        </Card>
      </div>
    </template>
  </PaginatedList>
</template>
