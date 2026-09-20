<script setup lang="ts">
import { ChevronLeft, ChevronRight } from '@lucide/vue'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import PaginatedList from '@/components/common/PaginatedList.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { useLocale } from '@/composables/useLocale'
import { useServerTimeStore } from '@/stores/serverTimeStore'
import type { Task } from '@/types/Dashboard'
import type { BadgeVariant } from '@/types/Ui'
import { formatShortDate } from '@/utils/dateFormatter'

interface Props {
  tasks: Task[]
  title?: string
  pageSize?: number
}

const props = withDefaults(defineProps<Props>(), {
  title: undefined,
  pageSize: 5,
})

const serverTimeStore = useServerTimeStore()

const { t } = useI18n()
const { isRtl } = useLocale()
// Purely decorative "this row is tappable" cue -- points the way the
// reader moves, same convention as SupervisionStatusReportsTab.vue's
// own month-nav chevrons.
const chevronIcon = computed(() => (isRtl.value ? ChevronLeft : ChevronRight))

const PRIORITY_LABEL_KEYS: Record<string, string> = {
  urgent: 'dashboard.priority.urgent',
  high: 'dashboard.priority.high',
  medium: 'dashboard.priority.medium',
  low: 'dashboard.priority.low',
}

function priorityLabel(priority: string): string {
  const key = PRIORITY_LABEL_KEYS[priority]
  return key ? t(key) : priority
}

defineEmits<{
  'task-click': [taskId: string]
}>()


const displayedTasks = computed(() => 
  props.tasks
    .filter(t => t.status !== 'done')
    .sort((a, b) => {
      const priorityOrder = { urgent: 0, high: 1, medium: 2, low: 3 }
      return priorityOrder[a.priority] - priorityOrder[b.priority]
    })
)

const priorityColor = (priority: string): BadgeVariant => {
  const colors: Record<string, BadgeVariant> = {
    urgent: 'danger',
    high: 'warning',
    medium: 'info',
    low: 'neutral',
  }
  return colors[priority] || 'neutral'
}

// Server's Kuwait-local "today" (see serverTimeStore.ts), not the
// browser's own clock -- falls back to it only for the brief window
// before the app's first server-time fetch resolves.
const isOverdue = (dueDate: string) => new Date(dueDate).getTime() < (serverTimeStore.todayTimestamp ?? new Date().setHours(0, 0, 0, 0))

const formatDate = formatShortDate
</script>

<template>
  <Card :padded="false">
    <template #header>
      <h3 class="text-sm font-semibold text-text-primary">{{ title ?? t('dashboard.pendingTasks') }}</h3>
    </template>

    <EmptyState v-if="displayedTasks.length === 0" :title="t('dashboard.noPendingTasks')" :bordered="false" />
    <PaginatedList v-else :items="displayedTasks" :page-size="pageSize">
      <template #default="{ items }">
        <ul class="divide-y divide-border-light">
          <li
            v-for="task in items"
            :key="task.id"
            class="flex cursor-pointer items-center gap-3 px-5 py-3.5 transition-colors hover:bg-bg-hover"
            @click="$emit('task-click', task.id)"
          >
            <div class="min-w-0 flex-1">
              <div class="flex items-start gap-2">
                <p class="flex-1 text-sm font-medium text-text-primary">{{ task.title }}</p>
                <StatusBadge :label="priorityLabel(task.priority)" :variant="priorityColor(task.priority)" class="shrink-0" />
              </div>
              <p class="mt-0.5 truncate text-xs text-text-muted">{{ task.project }}</p>
              <div class="mt-1.5 flex items-center justify-between">
                <span class="text-xs text-text-muted">{{ task.assignee }}</span>
                <span :class="['text-xs font-medium', isOverdue(task.dueDate) ? 'text-danger-500' : 'text-text-muted']">
                  {{ formatDate(task.dueDate) }}
                </span>
              </div>
            </div>
            <component :is="chevronIcon" class="h-4 w-4 shrink-0 text-text-muted" />
          </li>
        </ul>
      </template>
    </PaginatedList>
  </Card>
</template>
