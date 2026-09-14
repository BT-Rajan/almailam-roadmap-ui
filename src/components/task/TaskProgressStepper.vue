<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import type { StepStatus } from '@/utils/stepperStyle'
import type { TaskStatus } from '@/types/Task'

// Read-only progress indicator for a single task, shown inside
// TaskDetails.vue. Deliberately not interactive (no click-to-jump) --
// unlike WorkflowProgress.vue's stage segments, a task's status is
// already changed via the Status dropdown right below it, so a second,
// clickable control here would just be a second way to do the same
// thing and could let someone skip the dropdown's own validation path.
//
// Only three steps are ever shown (Pending / In Progress / Completed).
// 'Preset' is a real TaskStatus (see Task.ts) but it isn't a visual
// stage of its own here -- it's "not yet reviewed", which TaskDetails
// already surfaces separately via its own warning banner -- so a
// Preset task's rank collapses to the same as Pending's.
const props = defineProps<{
  status: TaskStatus
}>()

const { t } = useI18n()

const STEPS: { status: TaskStatus; labelKey: string }[] = [
  { status: 'Pending', labelKey: 'task.status.pending' },
  { status: 'In Progress', labelKey: 'task.status.inProgress' },
  { status: 'Completed', labelKey: 'task.status.completed' },
]

const currentRank = computed(() => {
  if (props.status === 'Preset') return 0
  const rank = STEPS.findIndex((step) => step.status === props.status)
  return rank === -1 ? 0 : rank
})

function stepStatus(rank: number): StepStatus {
  if (rank < currentRank.value) return 'complete'
  if (rank === currentRank.value) return 'current'
  return 'upcoming'
}

// Same three-color convention as stepBarClasses/stepLabelClasses in
// stepperStyle.ts (complete = green, current = info, upcoming = neutral
// border), but without that helper's cursor-pointer/hover affordances,
// since these segments aren't clickable.
function segmentClasses(status: StepStatus): string[] {
  return [
    'h-1.5 w-full rounded-full transition-colors duration-fast',
    status === 'complete' ? 'bg-success-500' : '',
    status === 'current' ? 'bg-info-500' : '',
    status === 'upcoming' ? 'bg-border-default' : '',
  ]
}

function labelClasses(status: StepStatus): string[] {
  return ['truncate text-xs text-center', status === 'current' ? 'font-semibold text-info-600' : 'text-text-muted']
}
</script>

<template>
  <div>
    <p class="mb-2 text-sm font-medium text-text-primary">
      {{ t('task.progress.stepLabel', { current: currentRank + 1, total: STEPS.length, label: t(STEPS[currentRank].labelKey) }) }}
    </p>
    <div class="flex items-stretch gap-2" role="group" :aria-label="t('task.progress.label')">
      <div v-for="(step, rank) in STEPS" :key="step.status" class="flex flex-1 flex-col items-stretch gap-1">
        <span :class="segmentClasses(stepStatus(rank))" :aria-current="stepStatus(rank) === 'current' ? 'step' : undefined" />
        <span :class="labelClasses(stepStatus(rank))">{{ t(step.labelKey) }}</span>
      </div>
    </div>
  </div>
</template>
