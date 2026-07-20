<script setup lang="ts">
import StatusBadge from '@/components/common/StatusBadge.vue'
import { getTaskStatusVariant } from '@/utils/taskHelpers'
import type { TaskStatus } from '@/types/Task'

defineProps<{
  status: TaskStatus
}>()
</script>

<template>
  <StatusBadge :label="status" :variant="getTaskStatusVariant(status)" size="sm" show-dot />
</template>
