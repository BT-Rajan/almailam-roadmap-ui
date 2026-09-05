<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import StatusBadge from '@/components/common/StatusBadge.vue'
import { getTaskStatusVariant } from '@/utils/taskHelpers'
import type { TaskStatus } from '@/types/Task'

const props = defineProps<{
  status: TaskStatus
}>()

const { t } = useI18n()

const STATUS_LABEL_KEYS: Record<TaskStatus, string> = {
  Pending: 'task.status.pending',
  'In Progress': 'task.status.inProgress',
  Completed: 'task.status.completed',
}
const statusLabel = computed(() => t(STATUS_LABEL_KEYS[props.status]))
</script>

<template>
  <StatusBadge :label="statusLabel" :variant="getTaskStatusVariant(status)" size="sm" show-dot />
</template>
