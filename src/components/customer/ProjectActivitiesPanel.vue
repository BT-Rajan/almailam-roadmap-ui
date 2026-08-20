<script setup lang="ts">
import { ListChecks } from '@lucide/vue'

import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import type { ProjectActivityGroup } from '@/types/CustomerPortal'

defineProps<{
  activities: ProjectActivityGroup[]
}>()
</script>

<template>
  <Card>
    <template #header>
      <h2 class="text-xl font-semibold text-neutral-900">Scope of Work</h2>
    </template>

    <EmptyState
      v-if="activities.length === 0"
      :icon="ListChecks"
      title="No activities on file"
      description="The specific activities covered by this engagement will appear here once set up."
    />

    <div v-else class="flex flex-col gap-4">
      <div v-for="group in activities" :key="group.serviceName">
        <p class="text-sm font-semibold text-neutral-800">{{ group.serviceName }}</p>
        <ul class="mt-1.5 flex flex-col gap-1">
          <li v-for="activity in group.activities" :key="activity" class="flex items-center gap-2 text-sm text-neutral-600">
            <span class="h-1.5 w-1.5 shrink-0 rounded-full bg-primary-400" />
            {{ activity }}
          </li>
        </ul>
      </div>
    </div>
  </Card>
</template>
