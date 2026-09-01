<script setup lang="ts">
import { computed } from 'vue'

import Card from '@/components/common/Card.vue'
import Stepper from '@/components/common/Stepper.vue'
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
// stepper is now the only place Quotation/Contract/Design/Supervision/
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

const steps = computed(() => visibleStages.value.map((stage) => ({ label: getWorkflowStageLabel(stage) })))

// Rank = position in the full, unfiltered WORKFLOW_STAGES sequence, not
// in visibleStages -- Design/Supervision can drop in or out of
// visibleStages as a project's selected activities change (see
// compute_stage_flags), which would otherwise shift every later
// step's render-array position and desync it from currentStepRank,
// making already-completed steps render as if nothing were done (see
// Stepper.vue's stepRanks prop).
const stepRanks = computed(() => visibleStages.value.map((stage) => WORKFLOW_STAGES.indexOf(stage)))

const currentStepRank = computed(() => WORKFLOW_STAGES.indexOf(props.currentStage))

// Every visible stage has a destination now (see STAGE_TABS above), so
// every step is navigable regardless of its complete/current/upcoming
// status.
const isStepNavigable = (): boolean => true

function handleSelect(index: number): void {
  const stage = visibleStages.value[index]
  if (stage) emit('navigate-tab', STAGE_TABS[stage])
}
</script>

<template>
  <Card>
    <template #header>
      <h3 class="text-sm font-semibold text-text-primary">Workflow Progress</h3>
    </template>
    <div class="overflow-x-auto pb-1">
      <div class="min-w-[720px]">
        <Stepper
          :steps="steps"
          :current-step="currentStepRank"
          :step-ranks="stepRanks"
          clickable
          :is-step-navigable="isStepNavigable"
          @select="handleSelect"
        />
      </div>
    </div>
  </Card>
</template>
