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
  includesGovernmentSubmission: boolean
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
  Handover: 'project.stage.handover',
}

function stageLabel(stage: WorkflowStage): string {
  return t(STAGE_LABEL_KEYS[stage] ?? getWorkflowStageLabel(stage))
}

// Design, Government Submission (Permits), and Supervision are three
// independent parallel tracks off Contract (see WorkflowStage) -- this
// simple linear Stepper can't draw the actual branching shape
// WorkflowProgress.vue does for staff, so it just filters each out when
// this project doesn't include that track, same as before, now
// extended to Government Submission too (previously shown
// unconditionally).
const visibleStages = computed<WorkflowStage[]>(() =>
  WORKFLOW_STAGES.filter((stage) => {
    if (stage === 'Design') return props.includesDesign
    if (stage === 'Government Submission') return props.includesGovernmentSubmission
    if (stage === 'Supervision') return props.includesSupervision
    return true
  }),
)

const steps = computed(() => visibleStages.value.map((stage) => ({ label: stageLabel(stage) })))

// Rank = position in a *banded* sequence, not the raw WORKFLOW_STAGES
// index -- Design/Government Submission/Supervision share one band
// (mirrors backend project_service._STAGE_PROGRESS_BAND) since they're
// parallel tracks with no real ordering among themselves (see
// WORKFLOW_STAGES's own comment). Using each one's distinct array
// index here instead would let currentStage sitting on any one of them
// read the *other* two as strictly before or after it -- e.g.
// currentStage = 'Design' while Government Submission has already
// finished would compare Government Submission's higher raw index as
// still "upcoming" (grey) even though it's actually done, and the
// reverse (a not-yet-started track misread as "complete") is exactly
// as possible. Banding them together makes every visible track in the
// parallel band read as the same status (all "current" while the
// project sits in the band, all "complete" once it reaches Handover)
// instead of an arbitrary subset flickering grey based on array order.
const STAGE_BAND: Record<WorkflowStage, number> = {
  Requirement: 0,
  Quotation: 1,
  'Payment Plan': 2,
  Contract: 3,
  Design: 4,
  'Government Submission': 4,
  Supervision: 4,
  Handover: 5,
}

const stepRanks = computed(() => visibleStages.value.map((stage) => STAGE_BAND[stage]))

const currentStepRank = computed(() => STAGE_BAND[props.currentStage])
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
