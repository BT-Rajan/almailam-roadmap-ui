<script setup lang="ts">
import { Building2, Calendar, Layers, Pencil, Plus, Trash2, User } from '@lucide/vue'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import IconButton from '@/components/common/IconButton.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { getProjectPriorityVariant, getProjectStatusVariant } from '@/utils/projectHelpers'
import { formatDate } from '@/utils/dateFormatter'
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

const STATUS_LABEL_KEYS: Record<string, string> = {
  Active: 'project.status.active',
  'On Hold': 'project.status.onHold',
  Cancelled: 'project.status.cancelled',
  Completed: 'project.status.completed',
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
          <span class="inline-flex items-center gap-1.5">
            <Building2 class="h-4 w-4 text-text-muted" />
            {{ client?.companyName ?? t('project.unassigned') }}
          </span>
          <span class="inline-flex items-center gap-1.5">
            <User class="h-4 w-4 text-text-muted" />
            {{ project.engineer }}
          </span>
          <span class="inline-flex items-center gap-1.5">
            <Layers class="h-4 w-4 text-text-muted" />
            {{ project.service }}
          </span>
          <span class="inline-flex items-center gap-1.5">
            <Calendar class="h-4 w-4 text-text-muted" />
            {{ formatDate(project.startDate) }}&ndash;{{ formatDate(project.targetDate) }}
          </span>
        </div>
      </div>

      <div class="flex shrink-0 flex-wrap items-center gap-2">
        <!-- The current stage used to be repeated here as its own badge,
             on top of the same fact shown by the "current" circle in
             WorkflowProgress.vue immediately below this header, and again
             as that circle's own step label. Dropped as a pure duplicate --
             stage is now shown in exactly one place. -->
        <StatusBadge :label="statusLabel" :variant="getProjectStatusVariant(project.status)" showDot />
        <StatusBadge :label="priorityBadgeLabel" :variant="getProjectPriorityVariant(project.priority)" />
        <!-- Change Stage / Change Status buttons hidden deliberately, not removed --
             this is currently the only UI path that calls projectStore.setStage /
             setStatus (see ProjectWorkspacePage.vue's @change-stage / @change-status
             handlers and ProjectTransitionDialog), so hiding them means projects can
             no longer be advanced through stages or moved to On Hold / Cancelled
             from this screen. Uncomment to restore. -->
        <!-- <BaseButton variant="secondary" size="sm" :icon="Workflow" class="no-print" @click="$emit('change-stage')">{{ t('project.header.stage') }}</BaseButton> -->
        <!-- <BaseButton v-if="project.status !== 'Completed'" variant="secondary" size="sm" :icon="RefreshCw" class="no-print" @click="$emit('change-status')">{{ t('project.header.status') }}</BaseButton> -->
        <BaseButton variant="secondary" size="sm" :icon="Plus" class="no-print" @click="$emit('add-service')">{{ t('project.header.addService') }}</BaseButton>
        <IconButton :icon="Pencil" :label="t('project.header.editProject')" size="sm" class="no-print" @click="$emit('edit')" />
        <IconButton :icon="Trash2" :label="t('project.header.deleteProject')" size="sm" class="no-print" @click="$emit('delete')" />
      </div>
    </div>
  </div>
</template>
