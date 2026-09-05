<script setup lang="ts">
import { Building2, CalendarClock, UserRound } from '@lucide/vue'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import Card from '@/components/common/Card.vue'
import ProgressBar from '@/components/common/ProgressBar.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import type { Client } from '@/types/Client'
import type { Project } from '@/types/Project'
import { formatDate } from '@/utils/dateFormatter'
import { getProjectPriorityVariant, getProjectStatusVariant, getWorkflowStageLabel } from '@/utils/projectHelpers'

const props = defineProps<{
  project: Project
  client?: Client
}>()

const emit = defineEmits<{
  open: [projectId: string]
}>()

const { t } = useI18n()

const clientName = computed(() => props.client?.companyName ?? t('project.unknownClient'))

function open(): void {
  emit('open', props.project.id)
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
const stageLabel = computed(() => t(STAGE_LABEL_KEYS[props.project.currentStage] ?? getWorkflowStageLabel(props.project.currentStage)))

const STATUS_LABEL_KEYS: Record<string, string> = {
  Active: 'project.status.active',
  'On Hold': 'project.status.onHold',
  Cancelled: 'project.status.cancelled',
}
const statusLabel = computed(() => t(STATUS_LABEL_KEYS[props.project.status] ?? props.project.status))

const PRIORITY_BADGE_LABEL_KEYS: Record<string, string> = {
  High: 'project.priorityBadge.high',
  Medium: 'project.priorityBadge.medium',
  Low: 'project.priorityBadge.low',
}
const priorityBadgeLabel = computed(() => t(PRIORITY_BADGE_LABEL_KEYS[props.project.priority] ?? props.project.priority))

function handleKeydown(event: KeyboardEvent): void {
  // See ClientCard.vue's identical fix: the whole card acts as one big
  // button, so Enter and Space both activate it -- a mouse-only @click
  // here would otherwise make every project in the grid unreachable to
  // keyboard and screen-reader users entirely.
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault()
    open()
  }
}
</script>

<template>
  <Card
    hoverable
    class="cursor-pointer focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-500"
    role="button"
    tabindex="0"
    :aria-label="t('project.card.openProject', { name: project.projectName })"
    @click="open"
    @keydown="handleKeydown"
  >
    <div class="flex flex-col gap-4">
      <div class="flex items-start justify-between gap-3">
        <div class="flex flex-col gap-1">
          <p class="text-xs font-medium uppercase tracking-wide text-text-muted">{{ project.projectNo }}</p>
          <h3 class="text-base font-semibold leading-snug text-text-primary">{{ project.projectName }}</h3>
        </div>
        <StatusBadge :label="statusLabel" :variant="getProjectStatusVariant(project.status)" show-dot />
      </div>

      <div class="flex items-center gap-2 text-sm text-text-muted">
        <Building2 class="h-4 w-4 shrink-0 text-text-muted" />
        <span class="truncate">{{ clientName }}</span>
      </div>

      <div class="flex flex-wrap items-center gap-2">
        <StatusBadge :label="stageLabel" variant="info" />
        <StatusBadge :label="priorityBadgeLabel" :variant="getProjectPriorityVariant(project.priority)" />
      </div>

      <ProgressBar :value="project.progress" show-label />

      <div class="flex items-center justify-between border-t border-border-light pt-3 text-xs text-text-muted">
        <div class="flex items-center gap-1.5">
          <UserRound class="h-3.5 w-3.5" />
          <span>{{ project.engineer }}</span>
        </div>
        <div class="flex items-center gap-1.5">
          <CalendarClock class="h-3.5 w-3.5" />
          <span>{{ formatDate(project.targetDate) }}</span>
        </div>
      </div>
    </div>
  </Card>
</template>
