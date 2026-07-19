<script setup lang="ts">
import { computed } from 'vue'
import type { Task } from '@/types/Dashboard'
import Card from '@/components/common/Card.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'

interface Props {
  tasks: Task[]
  title?: string
  maxItems?: number
}

const props = withDefaults(defineProps<Props>(), {
  title: 'Pending Tasks',
  maxItems: 4,
})

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

const priorityColor = (priority: string) => {
  const colors: Record<string, any> = {
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
      <h3 class="font-medium text-neutral-900">{{ title }}</h3>
    </template>

    <div v-if="displayedTasks.length === 0" class="py-8 text-center text-neutral-500">
      <p class="text-sm">No pending tasks</p>
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
              <p class="text-sm font-medium text-neutral-900 flex-1">{{ task.title }}</p>
              <StatusBadge :label="task.priority" :variant="priorityColor(task.priority)" class="flex-shrink-0" />
            </div>
            <p class="text-xs text-neutral-500 mt-1">{{ task.project }}</p>
          </div>
        </div>
        <div class="flex items-center justify-between mt-2">
          <span class="text-xs text-neutral-500">{{ task.assignee }}</span>
          <span :class="['text-xs font-medium', isOverdue(task.dueDate) ? 'text-danger-500' : 'text-neutral-400']">
            {{ formatDate(task.dueDate) }}
          </span>
        </div>
      </div>
    </div>
  </Card>
</template>
