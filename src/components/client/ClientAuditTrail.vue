<script setup lang="ts">
import { History } from '@lucide/vue'

import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import type { ClientAuditEvent } from '@/types/Client'
import { formatDateTime } from '@/utils/dateFormatter'

defineProps<{
  events: ClientAuditEvent[]
}>()
</script>

<template>
  <Card>
    <template #header>
      <h3 class="text-sm font-semibold text-neutral-800">Activity</h3>
    </template>

    <EmptyState
      v-if="events.length === 0"
      :icon="History"
      title="No activity recorded"
      description="Changes to this client profile will be recorded here for audit purposes."
    />

    <ol v-else class="flex flex-col gap-4">
      <li v-for="event in events" :key="event.id" class="flex gap-3">
        <span class="mt-1 h-2 w-2 shrink-0 rounded-full bg-primary-500" />
        <div class="flex flex-col gap-0.5">
          <p class="text-sm font-medium text-neutral-800">{{ event.action }}</p>
          <p class="text-xs text-neutral-500">{{ event.user }} · {{ formatDateTime(event.timestamp) }}</p>
          <p v-if="event.reason" class="text-xs text-neutral-500">{{ event.reason }}</p>
        </div>
      </li>
    </ol>
  </Card>
</template>
