<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import Card from '@/components/common/Card.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import type { Task } from '@/types/Dashboard'
import type { BadgeVariant } from '@/types/Ui'

interface Props {
  tasks: Task[]
  title?: string
  maxItems?: number
}

const props = withDefaults(defineProps<Props>(), {
  title: undefined,
  maxItems: 4,
})

const { t } = useI18n()

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
    .slice(0, props.maxItems)
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

const isOverdue = (dueDate: string) => new Date(dueDate) < new Date()

const formatDate = (date: string) => new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
</script>

<template>
  <Card>
    <template #header>
      <h3 class="font-medium text-text-primary">{{ title ?? t('dashboard.pendingTasks') }}</h3>
    </template>

    <div v-if="displayedTasks.length === 0" class="py-8 text-center text-text-muted">
      <p class="text-sm">{{ t('dashboard.noPendingTasks') }}</p>
    </div>
    <div v-else class="space-y-2">
      <div
        v-for="task in displayedTasks"
        :key="task.id"
        class="p-3 rounded-lg border border-border-light hover:bg-bg-hover transition-colors cursor-pointer"
        @click="$emit('task-click', task.id)"
      >
        <div class="flex items-start gap-3">
          <div class="flex-1 min-w-0">
            <div class="flex items-start gap-2">
              <p class="text-sm font-medium text-text-primary flex-1">{{ task.title }}</p>
              <StatusBadge :label="priorityLabel(task.priority)" :variant="priorityColor(task.priority)" class="flex-shrink-0" />
            </div>
            <p class="text-xs text-text-muted mt-1">{{ task.project }}</p>
          </div>
        </div>
        <div class="flex items-center justify-between mt-2">
          <span class="text-xs text-text-muted">{{ task.assignee }}</span>
          <span :class="['text-xs font-medium', isOverdue(task.dueDate) ? 'text-danger-500' : 'text-text-muted']">
            {{ formatDate(task.dueDate) }}
          </span>
        </div>
      </div>
    </div>
  </Card>
</template>
