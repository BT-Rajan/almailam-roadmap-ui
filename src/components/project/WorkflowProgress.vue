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

// Several of these 9 stages are also project tabs below -- rather than
// leave the stepper as a second, disconnected way of saying "Quotation"
// or "Contract", clicking a stage that has a matching tab jumps there
// directly. Stages with no tab of their own (Enquiry, Review,
// Correction, Approval, Completed) stay purely informational.
const STAGE_TABS: Partial<Record<WorkflowStage, ProjectWorkspaceTabKey>> = {
  Quotation: 'quotation',
  Contract: 'contract',
  Design: 'design',
  'Government Submission': 'government',
}

const steps = WORKFLOW_STAGES.map((stage) => ({ label: stage }))

const currentStepIndex = computed(() => {
  const index = WORKFLOW_STAGES.indexOf(props.currentStage)
  return index === -1 ? 0 : index
})

function isStepNavigable(index: number): boolean {
  return WORKFLOW_STAGES[index] in STAGE_TABS
}

function handleSelect(index: number): void {
  const tab = STAGE_TABS[WORKFLOW_STAGES[index]]
  if (tab) emit('navigate-tab', tab)
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
