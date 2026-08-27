<script setup lang="ts">
import { computed } from 'vue'

import Card from '@/components/common/Card.vue'
import Stepper from '@/components/common/Stepper.vue'
import type { ProjectWorkspaceTabKey, WorkflowStage } from '@/types/Project'
import { WORKFLOW_STAGES, getWorkflowStageLabel } from '@/utils/projectHelpers'

interface Props {
  currentStage: WorkflowStage
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'navigate-tab': [tab: ProjectWorkspaceTabKey]
}>()

// Every one of these 7 stages jumps to the tab that covers it -- this
// stepper is now the only place Quotation/Contract/Design/Government
// Submission are reachable from (their own tab buttons were removed as
// exact duplicates of these same 4 stage names). Execution & Tracking
// (formerly Review; Approval was dropped entirely) lands on Process,
// since that's where the actual execution checklist and stage-gate
// documents live; Completed lands on Overview, the project's general
// end-state summary. Requirement (formerly Enquiry) has its own
// dedicated tab now -- client/project details, scope of work, and its
// revision history/internal approval -- deliberately decoupled from
// Overview's Completed-stage content rather than sharing it.
const STAGE_TABS: Record<WorkflowStage, ProjectWorkspaceTabKey> = {
  Requirement: 'requirement',
  Quotation: 'quotation',
  Contract: 'contract',
  Design: 'design',
  'Government Submission': 'government',
  'Execution & Tracking': 'process',
  // 'completed', not 'overview' directly -- lets the parent tell this
  // stepper click apart from every other route to the shared Overview
  // pane, so it can set stageContext to 'Completed' before landing on
  // Overview (see ProjectWorkspacePage.vue's STAGE_TAB_KEYS).
  Completed: 'completed',
}

const steps = WORKFLOW_STAGES.map((stage) => ({ label: getWorkflowStageLabel(stage) }))

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
