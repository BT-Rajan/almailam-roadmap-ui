<script setup lang="ts">
import { CheckCircle2, Circle, CircleDot } from '@lucide/vue'
import { computed } from 'vue'

import Card from '@/components/common/Card.vue'
import ProgressBar from '@/components/common/ProgressBar.vue'
import type { ProjectWorkspaceTabKey, WorkflowStage } from '@/types/Project'
import { WORKFLOW_STAGES } from '@/utils/projectHelpers'

interface Props {
  currentStage: WorkflowStage
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'navigate-tab': [tab: ProjectWorkspaceTabKey]
}>()

// Every one of these 7 stages jumps to the tab that covers it -- this
// list is the only place Quotation/Contract/Design/Government
// Submission are reachable from (their own tab buttons were removed as
// exact duplicates of these same 4 stage names). Execution & Tracking
// (formerly Review; Approval was dropped entirely) lands on Process,
// since that's where the actual execution checklist and stage-gate
// documents live; Enquiry and Completed land on Overview, the
// project's general start/end-state summary.
const STAGE_TABS: Record<WorkflowStage, ProjectWorkspaceTabKey> = {
  Enquiry: 'overview',
  Quotation: 'quotation',
  Contract: 'contract',
  Design: 'design',
  'Government Submission': 'government',
  'Execution & Tracking': 'process',
  Completed: 'overview',
}

const currentStepIndex = computed(() => {
  const index = WORKFLOW_STAGES.indexOf(props.currentStage)
  return index === -1 ? 0 : index
})

// Same tri-state pattern as ClientOnboardingProgress's requirement
// checklist (done / not done), plus a "current" state in between since
// a project's stage -- unlike an onboarding requirement -- is always
// sitting at exactly one specific point in an ordered pipeline, not
// just satisfied-or-not. "Completed" is both the final stage AND a
// reached state, so it counts as done rather than "current".
function stageStatus(index: number): 'complete' | 'current' | 'upcoming' {
  if (index < currentStepIndex.value) return 'complete'
  if (index === currentStepIndex.value) return WORKFLOW_STAGES[index] === 'Completed' ? 'complete' : 'current'
  return 'upcoming'
}

// Mirrors ProgressBar's own >=100/>=50/else thresholds so the bar and
// the current-stage dot always agree on what "in progress" looks like.
const completionPercentage = computed(() => {
  const completeCount = WORKFLOW_STAGES.filter((_, index) => stageStatus(index) === 'complete').length
  return Math.round((completeCount / WORKFLOW_STAGES.length) * 100)
})

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
        <li v-for="(stage, index) in WORKFLOW_STAGES" :key="stage">
          <button
            type="button"
            class="group flex w-full items-center justify-between gap-3 py-2.5 text-left"
            :aria-label="`Go to ${stage}`"
            @click="handleSelect(stage)"
          >
            <span class="inline-flex items-center gap-2 text-sm text-text-secondary group-hover:text-accent-600">
              <CheckCircle2 v-if="stageStatus(index) === 'complete'" class="h-4 w-4 shrink-0 text-success-500" />
              <CircleDot v-else-if="stageStatus(index) === 'current'" class="h-4 w-4 shrink-0 text-primary-600" />
              <Circle v-else class="h-4 w-4 shrink-0 text-text-muted" />
              {{ stage }}
            </span>
            <span v-if="stageStatus(index) === 'current'" class="text-xs text-text-muted">Current</span>
          </button>
        </li>
      </ul>
    </div>
  </Card>
</template>
