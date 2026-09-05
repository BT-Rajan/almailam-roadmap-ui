<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import Stepper from '@/components/common/Stepper.vue'
import type { WorkflowStage } from '@/types/Project'
import { WORKFLOW_STAGES, getWorkflowStageLabel } from '@/utils/projectHelpers'

// Mirrors src/components/project/WorkflowProgress.vue -- same box +
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
const { t } = useI18n()

const STAGE_LABEL_KEYS: Record<WorkflowStage, string> = {
  Requirement: 'project.stage.requirement',
  Quotation: 'project.stage.quotation',
  'Payment Plan': 'project.stage.paymentPlan',
  Contract: 'project.stage.contract',
  Design: 'project.stage.design',
  Supervision: 'project.stage.supervision',
  'Government Submission': 'project.stage.governmentSubmission',
}

function stageLabel(stage: WorkflowStage): string {
  return t(STAGE_LABEL_KEYS[stage] ?? getWorkflowStageLabel(stage))
}

const visibleStages = computed<WorkflowStage[]>(() =>
  WORKFLOW_STAGES.filter((stage) => {
    if (stage === 'Design') return props.includesDesign
    if (stage === 'Supervision') return props.includesSupervision
    return true
  }),
)

const steps = computed(() => visibleStages.value.map((stage) => ({ label: stageLabel(stage) })))

// Rank = position in the full, unfiltered WORKFLOW_STAGES sequence --
// see WorkflowProgress.vue's identical stepRanks for why this can't
// just be the render-array index.
const stepRanks = computed(() => visibleStages.value.map((stage) => WORKFLOW_STAGES.indexOf(stage)))

const currentStepRank = computed(() => WORKFLOW_STAGES.indexOf(props.currentStage))
</script>

<template>
  <!-- Same plain rounded-xl border box (no Card header divider, same p-6
       padding) the wizards and WorkflowProgress.vue wrap their own
       Stepper in -- so this looks like the exact same UI element on
       every screen it appears, staff and customer portal alike. -->
  <div class="rounded-xl border border-border-light bg-bg-card p-6">
    <h2 class="mb-6 text-sm font-semibold text-text-primary">{{ t('customer.projectProgress') }}</h2>
    <div class="overflow-x-auto pb-1">
      <div class="min-w-[640px]">
        <Stepper :steps="steps" :current-step="currentStepRank" :step-ranks="stepRanks" />
      </div>
    </div>
  </div>
</template>
