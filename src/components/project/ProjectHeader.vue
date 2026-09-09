<script setup lang="ts">
import { Building2, Calendar, Layers, Pencil, Trash2, User } from '@lucide/vue'
import { useI18n } from 'vue-i18n'

import IconButton from '@/components/common/IconButton.vue'
import { formatDate } from '@/utils/dateFormatter'
import type { Client } from '@/types/Client'
import type { Project } from '@/types/Project'

interface Props {
  project: Project
  client?: Client
}

defineProps<Props>()

defineEmits<{
  edit: []
  'change-stage': []
  'change-status': []
  'add-service': []
  delete: []
}>()

const { t } = useI18n()
</script>

<template>
  <!-- Single row: id + name + the four meta facts + actions all share one
       line now instead of stacking id/name, then meta, then a separate
       badges/actions row underneath. Status and priority badges, and the
       Add Service button, are hidden for now (not removed -- see the
       commented-out block below) at the request of the person maintaining
       this screen; @change-stage/@change-status/@add-service stay declared
       since PaymentPlanPanel.vue and others still rely on the same events
       existing on this component's contract. -->
  <div class="flex flex-wrap items-center gap-x-5 gap-y-2 p-4">
    <div class="flex flex-wrap items-baseline gap-x-2">
      <p class="text-xs font-medium uppercase tracking-wide text-text-muted">{{ project.projectNo }}</p>
      <h1 class="text-base font-semibold text-text-primary">{{ project.projectName }}</h1>
    </div>

    <span class="inline-flex items-center gap-1.5 text-sm text-text-muted">
      <Building2 class="h-4 w-4 text-text-muted" />
      {{ client?.companyName ?? t('project.unassigned') }}
    </span>
    <span class="inline-flex items-center gap-1.5 text-sm text-text-muted">
      <User class="h-4 w-4 text-text-muted" />
      {{ project.engineer }}
    </span>
    <span class="inline-flex items-center gap-1.5 text-sm text-text-muted">
      <Layers class="h-4 w-4 text-text-muted" />
      {{ project.service }}
    </span>
    <span class="inline-flex items-center gap-1.5 text-sm text-text-muted">
      <Calendar class="h-4 w-4 text-text-muted" />
      {{ formatDate(project.startDate) }}&ndash;{{ formatDate(project.targetDate) }}
    </span>

    <div class="ml-auto flex shrink-0 items-center gap-2">
      <!-- Status badge (Active/On Hold/...), priority badge (Medium
           Priority/...), and the Add Service button are hidden for now.
           Change Stage / Change Status buttons were already hidden
           earlier for the same reason they're commented rather than
           deleted: this is currently the only UI path that calls
           projectStore.setStage/setStatus (see ProjectWorkspacePage.vue's
           @change-stage/@change-status handlers and
           ProjectTransitionDialog) and the only caller of @add-service
           (openAddServiceDialog) -- hiding these buttons means projects
           can no longer be advanced through stages, moved to On Hold /
           Cancelled, or have a service added from this screen. Uncomment
           to restore any of them. -->
      <!-- <StatusBadge :label="statusLabel" :variant="getProjectStatusVariant(project.status)" showDot /> -->
      <!-- <StatusBadge :label="priorityBadgeLabel" :variant="getProjectPriorityVariant(project.priority)" /> -->
      <!-- <BaseButton variant="secondary" size="sm" :icon="Workflow" class="no-print" @click="$emit('change-stage')">{{ t('project.header.stage') }}</BaseButton> -->
      <!-- <BaseButton v-if="project.status !== 'Completed'" variant="secondary" size="sm" :icon="RefreshCw" class="no-print" @click="$emit('change-status')">{{ t('project.header.status') }}</BaseButton> -->
      <!-- <BaseButton variant="secondary" size="sm" :icon="Plus" class="no-print" @click="$emit('add-service')">{{ t('project.header.addService') }}</BaseButton> -->
      <IconButton :icon="Pencil" :label="t('project.header.editProject')" size="sm" class="no-print" @click="$emit('edit')" />
      <IconButton :icon="Trash2" :label="t('project.header.deleteProject')" size="sm" class="no-print" @click="$emit('delete')" />
    </div>
  </div>
</template>
