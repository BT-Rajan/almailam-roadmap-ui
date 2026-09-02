<script setup lang="ts">
import { CheckCircle2, Circle, CircleDot } from '@lucide/vue'
import { computed } from 'vue'

import Card from '@/components/common/Card.vue'
import ProgressBar from '@/components/common/ProgressBar.vue'
import type { ProjectWorkspaceTabKey, WorkflowStage } from '@/types/Project'
import { WORKFLOW_STAGES, getWorkflowStageLabel } from '@/utils/projectHelpers'

interface Props {
  currentStage: WorkflowStage
  // Design and/or Supervision only appear as steps when this project
  // actually includes that kind of work (see Project.includesDesign/
  // includesSupervision) -- every other stage is common to all projects.
  includesDesign: boolean
  includesSupervision: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'navigate-tab': [tab: ProjectWorkspaceTabKey]
}>()

// Every one of these stages jumps to the tab that covers it -- this
// list is the only place Quotation/Contract/Design/Supervision/
// Government Submission are reachable from (their own tab buttons were
// removed as exact duplicates of these same stage names). Requirement
// (formerly Enquiry) has its own dedicated tab now -- client/project
// details, scope of work, and its revision history/internal approval.
// Government Submission is the terminal stage -- there is no further
// stage past it.
const STAGE_TABS: Record<WorkflowStage, ProjectWorkspaceTabKey> = {
  Requirement: 'requirement',
  Quotation: 'quotation',
  Contract: 'contract',
  Design: 'design',
  Supervision: 'supervision',
  'Government Submission': 'government',
}

// Requirement/Quotation/Contract/Government Submission are common to
// every project; Design and Supervision only show up as steps when this
// project actually includes that kind of work.
const visibleStages = computed<WorkflowStage[]>(() =>
  WORKFLOW_STAGES.filter((stage) => {
    if (stage === 'Design') return props.includesDesign
    if (stage === 'Supervision') return props.includesSupervision
    return true
  }),
)

// Rank = position in the full, unfiltered WORKFLOW_STAGES sequence, not
// in visibleStages -- Design/Supervision can drop in or out of
// visibleStages as a project's selected activities change, which would
// otherwise misjudge an earlier stage's complete/current/upcoming
// status once a stage between it and currentStage is hidden.
const currentStepRank = computed(() => WORKFLOW_STAGES.indexOf(props.currentStage))

// Same tri-state pattern as ClientOnboardingProgress's requirement
// checklist (done / not done) -- same icons, same colors, same list
// layout -- plus a "current" state in between, since a project's stage,
// unlike an onboarding requirement, always sits at exactly one specific
// point in an ordered pipeline rather than just satisfied-or-not.
function stageStatus(stage: WorkflowStage): 'complete' | 'current' | 'upcoming' {
  const rank = WORKFLOW_STAGES.indexOf(stage)
  if (rank < currentStepRank.value) return 'complete'
  if (rank === currentStepRank.value) return 'current'
  return 'upcoming'
}

// Mirrors ClientOnboardingProgress's own completion percentage shape --
// share of the (visible) stages already reached.
const completionPercentage = computed(() => {
  const completeCount = visibleStages.value.filter((stage) => stageStatus(stage) === 'complete').length
  return Math.round((completeCount / visibleStages.value.length) * 100)
})

// Every visible stage has a destination (see STAGE_TABS above), so
// every row is clickable regardless of its complete/current/upcoming
// status -- same as before this was restyled.
function handleSelect(stage: WorkflowStage): void {
  emit('navigate-tab', STAGE_TABS[stage])
}
</script>

<template>
  <Card>
    <template #header>
      <h3 class="text-sm font-semibold text-text-primary">Workflow Progress</h3>
    </template>
    <div class="flex flex-col gap-4">
      <ProgressBar :value="completionPercentage" show-label />
      <ul class="flex flex-col divide-y divide-border-light">
        <li v-for="stage in visibleStages" :key="stage">
          <button
            type="button"
            class="group flex w-full items-center justify-between gap-3 py-2.5 text-left"
            :aria-label="`Go to ${getWorkflowStageLabel(stage)}`"
            @click="handleSelect(stage)"
          >
            <span class="inline-flex items-center gap-2 text-sm text-text-secondary group-hover:text-accent-600">
              <CheckCircle2
                v-if="stageStatus(stage) === 'complete'"
                class="h-4 w-4 shrink-0 text-success-500"
                aria-hidden="true"
              />
              <CircleDot v-else-if="stageStatus(stage) === 'current'" class="h-4 w-4 shrink-0 text-primary-600" aria-hidden="true" />
              <Circle v-else class="h-4 w-4 shrink-0 text-text-muted" aria-hidden="true" />
              {{ getWorkflowStageLabel(stage) }}
              <!-- Same reasoning as ClientOnboardingProgress.vue: the icon
                   alone only conveys status visually. -->
              <span class="sr-only">
                ({{ stageStatus(stage) === 'complete' ? 'Complete' : stageStatus(stage) === 'current' ? 'Current' : 'Upcoming' }})
              </span>
            </span>
            <span v-if="stageStatus(stage) === 'current'" class="text-xs text-text-muted">Current</span>
          </button>
        </li>
      </ul>
    </div>
  </Card>
</template>
