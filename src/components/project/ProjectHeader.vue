<script setup lang="ts">
import { Building2, Pencil, Plus, RefreshCw, Trash2, User, Workflow } from '@lucide/vue'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import IconButton from '@/components/common/IconButton.vue'
import ProgressBar from '@/components/common/ProgressBar.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { getProjectPriorityVariant, getProjectStatusVariant, getWorkflowStageLabel } from '@/utils/projectHelpers'
import type { Client } from '@/types/Client'
import type { Project } from '@/types/Project'

interface Props {
  project: Project
  client?: Client
}

const props = withDefaults(defineProps<Props>(), {
  client: undefined,
})

defineEmits<{
  edit: []
  'change-stage': []
  'change-status': []
  'add-service': []
  delete: []
}>()

const { t } = useI18n()

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
</script>

<template>
  <div class="flex flex-col gap-4 rounded-xl border border-border-light bg-bg-card p-5 shadow-soft">
    <div class="flex flex-col gap-3 tablet:flex-row tablet:items-start tablet:justify-between">
      <div class="flex flex-col gap-1.5">
        <p class="text-xs font-medium uppercase tracking-wide text-text-muted">{{ project.projectNo }}</p>
        <h1 class="text-xl font-semibold text-text-primary">{{ project.projectName }}</h1>
        <div class="flex flex-wrap items-center gap-4 text-sm text-text-muted">
          <span v-if="client" class="inline-flex items-center gap-1.5">
            <Building2 class="h-4 w-4 text-text-muted" />
            {{ client.companyName }}
          </span>
          <span class="inline-flex items-center gap-1.5">
            <User class="h-4 w-4 text-text-muted" />
            {{ project.engineer }}
          </span>
        </div>
      </div>

      <div class="flex shrink-0 flex-wrap items-center gap-2">
        <StatusBadge :label="stageLabel" variant="info" />
        <StatusBadge :label="statusLabel" :variant="getProjectStatusVariant(project.status)" />
        <StatusBadge :label="priorityBadgeLabel" :variant="getProjectPriorityVariant(project.priority)" />
        <BaseButton variant="secondary" size="sm" :icon="Workflow" class="no-print" @click="$emit('change-stage')">{{ t('project.header.stage') }}</BaseButton>
        <BaseButton variant="secondary" size="sm" :icon="RefreshCw" class="no-print" @click="$emit('change-status')">{{ t('project.header.status') }}</BaseButton>
        <BaseButton variant="secondary" size="sm" :icon="Plus" class="no-print" @click="$emit('add-service')">{{ t('project.header.addService') }}</BaseButton>
        <IconButton :icon="Pencil" :label="t('project.header.editProject')" size="sm" class="no-print" @click="$emit('edit')" />
        <IconButton :icon="Trash2" :label="t('project.header.deleteProject')" size="sm" class="no-print" @click="$emit('delete')" />
      </div>
    </div>

    <div class="flex items-center gap-3">
      <span class="w-24 shrink-0 text-xs font-medium text-text-muted">{{ t('project.header.progress') }}</span>
      <div class="max-w-md flex-1">
        <ProgressBar :value="project.progress" show-label />
      </div>
    </div>
  </div>
</template>
