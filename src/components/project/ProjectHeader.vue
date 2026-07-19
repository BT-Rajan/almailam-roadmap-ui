<script setup lang="ts">
import { Building2, User } from '@lucide/vue'

import ProgressBar from '@/components/common/ProgressBar.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { getProjectPriorityVariant, getProjectStatusVariant } from '@/utils/projectHelpers'
import type { Client } from '@/types/Client'
import type { Project } from '@/types/Project'

interface Props {
  project: Project
  client?: Client
}

withDefaults(defineProps<Props>(), {
  client: undefined,
})
</script>

<template>
  <div class="flex flex-col gap-4 rounded-xl border border-border-light bg-bg-card p-5 shadow-soft">
    <div class="flex flex-col gap-3 tablet:flex-row tablet:items-start tablet:justify-between">
      <div class="flex flex-col gap-1.5">
        <p class="text-xs font-medium uppercase tracking-wide text-neutral-400">{{ project.projectNo }}</p>
        <h1 class="text-xl font-semibold text-neutral-800">{{ project.projectName }}</h1>
        <div class="flex flex-wrap items-center gap-4 text-sm text-neutral-500">
          <span v-if="client" class="inline-flex items-center gap-1.5">
            <Building2 class="h-4 w-4 text-neutral-400" />
            {{ client.companyName }}
          </span>
          <span class="inline-flex items-center gap-1.5">
            <User class="h-4 w-4 text-neutral-400" />
            {{ project.engineer }}
          </span>
        </div>
      </div>

      <div class="flex shrink-0 items-center gap-2">
        <StatusBadge :label="project.currentStage" variant="info" />
        <StatusBadge :label="project.status" :variant="getProjectStatusVariant(project.status)" />
        <StatusBadge :label="`${project.priority} Priority`" :variant="getProjectPriorityVariant(project.priority)" />
      </div>
    </div>

    <div class="flex items-center gap-3">
      <span class="w-24 shrink-0 text-xs font-medium text-neutral-500">Progress</span>
      <div class="max-w-md flex-1">
        <ProgressBar :value="project.progress" show-label />
      </div>
    </div>
  </div>
</template>
