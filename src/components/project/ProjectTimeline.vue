<script setup lang="ts">
import { Pencil } from '@lucide/vue'

import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import IconButton from '@/components/common/IconButton.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import type { TimelineEvent, TimelineEventStatus } from '@/types/Timeline'
import { formatDate } from '@/utils/dateFormatter'
import { getTimelineEventIcon, getTimelineStatusLabel, getTimelineStatusVariant } from '@/utils/timelineHelpers'

interface Props {
  events: TimelineEvent[]
  editable?: boolean
}

withDefaults(defineProps<Props>(), {
  editable: false,
})

defineEmits<{
  edit: [event: TimelineEvent]
}>()

const DOT_STATUS_CLASSES: Record<TimelineEventStatus, string> = {
  completed: 'border-primary-500 bg-primary-500 text-white',
  'in-progress': 'border-warning-500 bg-bg-card text-warning-600',
  upcoming: 'border-border-default bg-bg-card text-neutral-400',
}
</script>

<template>
  <Card>
    <EmptyState
      v-if="events.length === 0"
      title="No timeline activity"
      description="Activity for this project will appear here as it happens."
    />
    <ol v-else class="flex flex-col">
      <li v-for="(event, index) in events" :key="event.id" class="group flex gap-4">
        <div class="flex flex-col items-center">
          <div
            class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border-2"
            :class="DOT_STATUS_CLASSES[event.status]"
          >
            <component :is="getTimelineEventIcon(event.type)" class="h-4 w-4" />
          </div>
          <div v-if="index < events.length - 1" class="my-1 w-0.5 flex-1 bg-border-default" />
        </div>
        <div class="flex-1 pb-6 last:pb-0">
          <div class="flex flex-wrap items-center gap-2">
            <p class="text-sm font-medium text-neutral-800">{{ event.title }}</p>
            <StatusBadge
              :label="getTimelineStatusLabel(event.status)"
              :variant="getTimelineStatusVariant(event.status)"
              size="sm"
            />
            <IconButton
              v-if="editable"
              :icon="Pencil"
              label="Edit this update"
              size="sm"
              class="opacity-0 transition-opacity duration-fast no-print group-hover:opacity-100"
              @click="$emit('edit', event)"
            />
          </div>
          <p v-if="event.description" class="mt-0.5 text-sm text-neutral-500">{{ event.description }}</p>
          <div class="mt-1 flex items-center gap-2 text-xs text-neutral-400">
            <span>{{ formatDate(event.date) }}</span>
            <span v-if="event.user">&bull; {{ event.user }}</span>
          </div>
        </div>
      </li>
    </ol>
  </Card>
</template>
