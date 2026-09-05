<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import StatusBadge from '@/components/common/StatusBadge.vue'
import { getTaskSeverityVariant } from '@/utils/taskHelpers'
import type { TaskSeverity } from '@/types/Task'

const props = defineProps<{
  severity: TaskSeverity
}>()

const { t } = useI18n()

const SEVERITY_LABEL_KEYS: Record<TaskSeverity, string> = {
  Critical: 'task.severity.critical',
  Major: 'task.severity.major',
  Minor: 'task.severity.minor',
}
const severityLabel = computed(() => t(SEVERITY_LABEL_KEYS[props.severity]))
</script>

<template>
  <StatusBadge :label="severityLabel" :variant="getTaskSeverityVariant(severity)" size="sm" />
</template>
