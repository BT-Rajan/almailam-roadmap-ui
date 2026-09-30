<script setup lang="ts">
import { ListChecks } from '@lucide/vue'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import type { TaskProgress } from '@/utils/serviceTaskLinks'

// A service's name on the project Overview (Design activity / Permit /
// Supervision activity), as the button that opens its tasks in
// ServiceTasksDialog.vue, with a live done/total chip -- so the tasks
// behind a service are one click away instead of a trip to another page.
const props = defineProps<{
  name: string
  progress?: TaskProgress
}>()

defineEmits<{ open: [] }>()

const { t } = useI18n()

const chipClass = computed(() => {
  if (!props.progress || props.progress.total === 0) return 'bg-neutral-500/10 text-text-muted'
  if (props.progress.done === props.progress.total) return 'bg-success-500/15 text-success-700'
  return 'bg-primary-500/15 text-primary-600'
})
</script>

<template>
  <button
    type="button"
    class="group inline-flex min-w-0 items-center gap-2 rounded-md text-start"
    :aria-label="t('project.serviceTasks.openTasksFor', { service: name })"
    @click="$emit('open')"
  >
    <span class="truncate text-sm font-medium text-text-primary underline-offset-4 group-hover:text-primary-600 group-hover:underline">{{ name }}</span>
    <span class="inline-flex shrink-0 items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium no-print" :class="chipClass">
      <ListChecks class="h-3.5 w-3.5" />
      {{ progress && progress.total > 0 ? t('project.serviceTasks.tasksChip', { done: progress.done, total: progress.total }) : t('project.serviceTasks.noTasksChip') }}
    </span>
  </button>
</template>
