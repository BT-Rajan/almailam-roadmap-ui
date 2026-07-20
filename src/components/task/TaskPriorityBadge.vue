<script setup lang="ts">
import StatusBadge from '@/components/common/StatusBadge.vue'
import { getTaskPriorityVariant } from '@/utils/taskHelpers'
import type { TaskPriority } from '@/types/Task'

defineProps<{
  priority: TaskPriority
}>()
</script>

<template>
  <StatusBadge :label="priority" :variant="getTaskPriorityVariant(priority)" size="sm" />
</template>
