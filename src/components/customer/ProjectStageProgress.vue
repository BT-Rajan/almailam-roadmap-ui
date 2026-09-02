<script setup lang="ts">
import { computed } from 'vue'

import Card from '@/components/common/Card.vue'
import Stepper from '@/components/common/Stepper.vue'
import type { WorkflowStage } from '@/types/Project'
import { WORKFLOW_STAGES, getWorkflowStageLabel } from '@/utils/projectHelpers'

// Mirrors src/components/project/WorkflowProgress.vue -- same Card +
// Stepper structure, same WORKFLOW_STAGES/getWorkflowStageLabel source
// of truth, so the client portal's stage stepper renders visually
// identical to the one staff see (and to the stepper the project/client
// wizards use, since all three share the one Stepper.vue component).
// Read-only here: unlike WorkflowProgress.vue, a step never navigates
// anywhere -- a customer has no internal tab to jump to.
interface Props {
  currentStage: WorkflowStage
  includesDesign: boolean
  includesSupervision: boolean
}

const props = defineProps<Props>()

const visibleStages = computed<WorkflowStage[]>(() =>
  WORKFLOW_STAGES.filter((stage) => {
    if (stage === 'Design') return props.includesDesign
    if (stage === 'Supervision') return props.includesSupervision
    return true
  }),
)

const steps = computed(() => visibleStages.value.map((stage) => ({ label: getWorkflowStageLabel(stage) })))

// Rank = position in the full, unfiltered WORKFLOW_STAGES sequence --
// see WorkflowProgress.vue's identical stepRanks for why this can't
// just be the render-array index.
const stepRanks = computed(() => visibleStages.value.map((stage) => WORKFLOW_STAGES.indexOf(stage)))

const currentStepRank = computed(() => WORKFLOW_STAGES.indexOf(props.currentStage))
</script>

<template>
  <Card>
    <template #header>
      <h2 class="text-xl font-semibold text-text-primary">Project Progress</h2>
    </template>
    <div class="overflow-x-auto pb-1">
      <div class="min-w-[640px]">
        <Stepper :steps="steps" :current-step="currentStepRank" :step-ranks="stepRanks" />
      </div>
    </div>
  </Card>
</template>
