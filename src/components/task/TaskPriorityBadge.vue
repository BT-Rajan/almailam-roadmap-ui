<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import StatusBadge from '@/components/common/StatusBadge.vue'
import { getTaskPriorityVariant } from '@/utils/taskHelpers'
import type { TaskPriority } from '@/types/Task'

const props = defineProps<{
  priority: TaskPriority
}>()

const { t } = useI18n()

const PRIORITY_LABEL_KEYS: Record<TaskPriority, string> = {
  High: 'task.priority.high',
  Medium: 'task.priority.medium',
  Low: 'task.priority.low',
}
const priorityLabel = computed(() => t(PRIORITY_LABEL_KEYS[props.priority]))
</script>

<template>
  <StatusBadge :label="priorityLabel" :variant="getTaskPriorityVariant(priority)" size="sm" />
</template>
