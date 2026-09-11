<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import { stepBarClasses, stepLabelClasses } from '@/utils/stepperStyle'

interface WizardStep {
  label: string
}

interface Props {
  steps: WizardStep[]
  currentStep: number
  // When true, steps already passed through (status "complete") become
  // clickable, emitting `select` to jump back to them directly instead
  // of only ever being reachable by repeatedly clicking "Back". Default
  // false preserves the existing purely-visual behaviour everywhere
  // else this component is used (workflow/stage progress displays,
  // where a step number isn't a valid thing to jump to).
  clickable?: boolean
  // Overrides which steps are navigable, independent of clickable/
  // status -- e.g. WorkflowProgress.vue uses this to make a step
  // clickable whenever it has a matching project tab to jump to,
  // regardless of whether that stage is complete, current, or still
  // upcoming (a "go to" link, not a wizard "go back"). When omitted,
  // navigability falls back to the clickable+complete rule above.
  isStepNavigable?: (index: number) => boolean
  // Rank each step actually belongs to, parallel to `steps`, when the
  // rendered list can be a subset of a larger canonical sequence (e.g.
  // WorkflowProgress.vue drops Design/Supervision steps that don't
  // apply to a given project). Status must be judged by a step's real
  // position in the full sequence, not by where it happens to land in
  // the shortened render array -- otherwise dropping an earlier step
  // shifts every later one's local index down, and currentStep (also a
  // rank, not a render position) stops lining up with any of them,
  // silently turning every already-completed step grey. Omit for the
  // common case where `steps` already covers a fixed, gap-free
  // sequence (every wizard) -- render position and rank are the same
  // thing there.
  stepRanks?: number[]
}

const props = withDefaults(defineProps<Props>(), { clickable: false, isStepNavigable: undefined, stepRanks: undefined })

const { t } = useI18n()

const emit = defineEmits<{
  select: [index: number]
}>()

function rankOf(index: number): number {
  return props.stepRanks?.[index] ?? index
}

function stepStatus(index: number): 'complete' | 'current' | 'upcoming' {
  const rank = rankOf(index)
  if (rank < props.currentStep) return 'complete'
  if (rank === props.currentStep) return 'current'
  return 'upcoming'
}

function isNavigable(index: number): boolean {
  if (props.isStepNavigable) return props.isStepNavigable(index)
  return props.clickable && stepStatus(index) === 'complete'
}

function handleStepClick(index: number): void {
  if (isNavigable(index)) emit('select', index)
}
</script>

<template>
  <!-- One rendering only: a colored bar above each label, no connector
       or numbered circle -- same treatment everywhere this component is
       used (client/project creation wizards, the project workspace's
       Workflow Progress bar, the customer portal's stage progress), so
       a project or client's stage progress reads identically no matter
       which screen shows it. Color rules live in
       src/utils/stepperStyle.ts, shared with WorkflowProgress.vue's own
       parallel-band ticks. -->
  <div class="flex items-stretch gap-2">
    <component
      :is="isNavigable(index) ? 'button' : 'div'"
      v-for="(step, index) in steps"
      :key="step.label"
      :type="isNavigable(index) ? 'button' : undefined"
      class="flex flex-1 flex-col items-stretch gap-1"
      :class="isNavigable(index) ? 'cursor-pointer' : ''"
      :aria-label="isNavigable(index) ? t('common.goToStep', { step: index + 1, label: step.label }) : undefined"
      :aria-current="stepStatus(index) === 'current' ? 'step' : undefined"
      @click="handleStepClick(index)"
    >
      <span :class="[...stepBarClasses(stepStatus(index)), 'w-full']" />
      <span :class="[...stepLabelClasses(stepStatus(index)), 'text-center']">{{ step.label }}</span>
    </component>
  </div>
</template>
