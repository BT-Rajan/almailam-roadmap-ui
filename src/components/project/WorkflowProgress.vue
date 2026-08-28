<script setup lang="ts">
import { computed } from 'vue'

import Card from '@/components/common/Card.vue'
import Stepper from '@/components/common/Stepper.vue'
import type { ProjectWorkspaceTabKey, WorkflowStage } from '@/types/Project'
import { WORKFLOW_STAGES, getWorkflowStageLabel } from '@/utils/projectHelpers'

interface Props {
  currentStage: WorkflowStage
  // The project's Additional Services engagement type (Project.typeCategoryName,
  // a plain name snapshot from the New Project wizard's type-activity picker --
  // see backend/app/models/project.py). When it's the "Supervision" category
  // (case-insensitive -- an admin could rename it), a 6th step is appended to
  // the stepper below. This is purely a display addition: Supervision was
  // never made a real WorkflowStage/current_stage value, so it has no
  // complete/current status of its own and no stage tab -- it always renders
  // "upcoming" and, when clicked, jumps to Overview, where the Additional
  // Services section lists the selected Supervision activities.
  typeCategoryName?: string | null
}

const props = defineProps<Props>()

const hasSupervisionStage = computed(() => props.typeCategoryName?.trim().toLowerCase() === 'supervision')

const emit = defineEmits<{
  'navigate-tab': [tab: ProjectWorkspaceTabKey]
}>()

// Every one of these 5 stages jumps to the tab that covers it -- this
// stepper is now the only place Quotation/Contract/Design/Government
// Submission are reachable from (their own tab buttons were removed as
// exact duplicates of these same 4 stage names). Requirement (formerly
// Enquiry) has its own dedicated tab now -- client/project details,
// scope of work, and its revision history/internal approval.
// Government Submission is the terminal stage -- there is no further
// stage past it.
const STAGE_TABS: Record<WorkflowStage, ProjectWorkspaceTabKey> = {
  Requirement: 'requirement',
  Quotation: 'quotation',
  Contract: 'contract',
  Design: 'design',
  'Government Submission': 'government',
}

const steps = computed(() => {
  const base = WORKFLOW_STAGES.map((stage) => ({ label: getWorkflowStageLabel(stage) }))
  return hasSupervisionStage.value ? [...base, { label: 'Supervision' }] : base
})

const currentStepIndex = computed(() => {
  const index = WORKFLOW_STAGES.indexOf(props.currentStage)
  return index === -1 ? 0 : index
})

// Every stage has a destination now (see STAGE_TABS above), so every
// step is navigable regardless of its complete/current/upcoming status.
const isStepNavigable = (): boolean => true

function handleSelect(index: number): void {
  const stage = WORKFLOW_STAGES[index]
  // The extra Supervision step (index === WORKFLOW_STAGES.length) has no
  // WorkflowStage/STAGE_TABS entry of its own -- see typeCategoryName above.
  emit('navigate-tab', stage ? STAGE_TABS[stage] : 'overview')
}
</script>

<template>
  <Card>
    <template #header>
      <h3 class="text-sm font-semibold text-text-primary">Workflow Progress</h3>
    </template>
    <div class="overflow-x-auto pb-1">
      <div :class="hasSupervisionStage ? 'min-w-[840px]' : 'min-w-[720px]'">
        <Stepper
          :steps="steps"
          :current-step="currentStepIndex"
          clickable
          :is-step-navigable="isStepNavigable"
          @select="handleSelect"
        />
      </div>
    </div>
  </Card>
</template>
