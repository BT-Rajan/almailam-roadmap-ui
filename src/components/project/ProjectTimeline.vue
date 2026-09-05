<script setup lang="ts">
import { Pencil } from '@lucide/vue'
import { useI18n } from 'vue-i18n'

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

// Completed = green, in-progress = blue (info -- the closest theme-aware
// token to "blue"), upcoming = grey. Matches Stepper.vue's own status
// coloring so the whole app uses one consistent status color language.
const DOT_STATUS_CLASSES: Record<TimelineEventStatus, string> = {
  completed: 'border-success-500 bg-success-500 text-white',
  'in-progress': 'border-info-500 bg-bg-card text-info-600',
  upcoming: 'border-border-default bg-bg-card text-text-muted',
}

const { t } = useI18n()
</script>

<template>
  <Card>
    <EmptyState
      v-if="events.length === 0"
      :title="t('project.timeline.emptyTitle')"
      :description="t('project.timeline.emptyDescription')"
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
            <p class="text-sm font-medium text-text-primary">{{ event.title }}</p>
            <StatusBadge
              :label="getTimelineStatusLabel(event.status)"
              :variant="getTimelineStatusVariant(event.status)"
              size="sm"
            />
            <IconButton
              v-if="editable"
              :icon="Pencil"
              :label="t('project.timeline.editUpdate', { title: event.title })"
              size="sm"
              class="opacity-0 transition-opacity duration-fast no-print group-hover:opacity-100 group-focus-within:opacity-100"
              @click="$emit('edit', event)"
            />
          </div>
          <p v-if="event.description" class="mt-0.5 text-sm text-text-muted">{{ event.description }}</p>
          <div class="mt-1 flex items-center gap-2 text-xs text-text-muted">
            <span>{{ formatDate(event.date) }}</span>
            <span v-if="event.user">&bull; {{ event.user }}</span>
          </div>
        </div>
      </li>
    </ol>
  </Card>
</template>
