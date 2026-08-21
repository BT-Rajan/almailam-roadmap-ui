<script setup lang="ts">
import { computed } from 'vue'

import Card from '@/components/common/Card.vue'
import Stepper from '@/components/common/Stepper.vue'
import type { ProjectWorkspaceTabKey, WorkflowStage } from '@/types/Project'
import { WORKFLOW_STAGES } from '@/utils/projectHelpers'

interface Props {
  currentStage: WorkflowStage
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'navigate-tab': [tab: ProjectWorkspaceTabKey]
}>()

// Every one of these 9 stages jumps to the tab that covers it -- this
// stepper is now the only place Quotation/Contract/Design/Government
// Submission are reachable from (their own tab buttons were removed as
// exact duplicates of these same 4 stage names). Review, Correction,
// and Approval all land on Process, since that's where the actual
// approval/execution checklist -- and any corrections to it, via
// undo/waive -- lives; Enquiry and Completed land on Overview, the
// project's general start/end-state summary.
const STAGE_TABS: Record<WorkflowStage, ProjectWorkspaceTabKey> = {
  Enquiry: 'overview',
  Quotation: 'quotation',
  Contract: 'contract',
  Design: 'design',
  'Government Submission': 'government',
  Review: 'process',
  Correction: 'process',
  Approval: 'process',
  Completed: 'overview',
}

const steps = WORKFLOW_STAGES.map((stage) => ({ label: stage }))

const currentStepIndex = computed(() => {
  const index = WORKFLOW_STAGES.indexOf(props.currentStage)
  return index === -1 ? 0 : index
})

// Every stage has a destination now (see STAGE_TABS above), so every
// step is navigable regardless of its complete/current/upcoming status.
const isStepNavigable = (): boolean => true

function handleSelect(index: number): void {
  emit('navigate-tab', STAGE_TABS[WORKFLOW_STAGES[index]])
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
          :current-step="currentStepIndex"
          clickable
          :is-step-navigable="isStepNavigable"
          @select="handleSelect"
        />
      </div>
    </div>
  </Card>
</template>
