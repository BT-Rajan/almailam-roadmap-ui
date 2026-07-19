<script setup lang="ts">
import { Building2, CalendarClock, UserRound } from '@lucide/vue'
import { computed } from 'vue'

import Card from '@/components/common/Card.vue'
import ProgressBar from '@/components/common/ProgressBar.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import type { Client } from '@/types/Client'
import type { Project } from '@/types/Project'
import { formatDate } from '@/utils/dateFormatter'
import { getProjectPriorityVariant, getProjectStatusVariant } from '@/utils/projectHelpers'

const props = defineProps<{
  project: Project
  client?: Client
}>()

defineEmits<{
  open: [projectId: string]
}>()

const clientName = computed(() => props.client?.companyName ?? 'Unknown Client')
</script>

<template>
  <Card
    hoverable
    class="cursor-pointer"
    @click="$emit('open', project.id)"
  >
    <div class="flex flex-col gap-4">
      <div class="flex items-start justify-between gap-3">
        <div class="flex flex-col gap-1">
          <p class="text-xs font-medium uppercase tracking-wide text-neutral-400">{{ project.projectNo }}</p>
          <h3 class="text-base font-semibold leading-snug text-neutral-800">{{ project.projectName }}</h3>
        </div>
        <StatusBadge :label="project.status" :variant="getProjectStatusVariant(project.status)" show-dot />
      </div>

      <div class="flex items-center gap-2 text-sm text-neutral-500">
        <Building2 class="h-4 w-4 shrink-0 text-neutral-400" />
        <span class="truncate">{{ clientName }}</span>
      </div>

      <div class="flex flex-wrap items-center gap-2">
        <StatusBadge :label="project.currentStage" variant="info" />
        <StatusBadge :label="`${project.priority} Priority`" :variant="getProjectPriorityVariant(project.priority)" />
      </div>

      <ProgressBar :value="project.progress" show-label />

      <div class="flex items-center justify-between border-t border-border-light pt-3 text-xs text-neutral-500">
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
