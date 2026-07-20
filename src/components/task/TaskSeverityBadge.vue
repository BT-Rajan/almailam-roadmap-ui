<script setup lang="ts">
import StatusBadge from '@/components/common/StatusBadge.vue'
import { getTaskSeverityVariant } from '@/utils/taskHelpers'
import type { TaskSeverity } from '@/types/Task'

defineProps<{
  severity: TaskSeverity
}>()
</script>

<template>
  <StatusBadge :label="severity" :variant="getTaskSeverityVariant(severity)" size="sm" />
</template>
