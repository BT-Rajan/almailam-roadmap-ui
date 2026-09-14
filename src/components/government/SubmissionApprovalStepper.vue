<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import StatusBadge from '@/components/common/StatusBadge.vue'
import Stepper from '@/components/common/Stepper.vue'
import type { ResponseOutcome, SubmissionStage } from '@/types/Submission'
import { SUBMISSION_STAGES, getSubmissionOutcomeVariant } from '@/utils/submissionHelpers'

interface Props {
  stage: SubmissionStage
  responseOutcome?: ResponseOutcome | null
}

const props = defineProps<Props>()
const { t } = useI18n()

const STAGE_LABEL_KEYS: Record<SubmissionStage, string> = {
  Prepare: 'government.submissionStage.prepare',
  Apply: 'government.submissionStage.apply',
  Track: 'government.submissionStage.track',
  Update: 'government.submissionStage.update',
  Close: 'government.submissionStage.close',
}

const OUTCOME_LABEL_KEYS: Record<ResponseOutcome, string> = {
  Approved: 'government.responseOutcome.approved',
  Rejected: 'government.responseOutcome.rejected',
  'No Response': 'government.responseOutcome.noResponse',
  Withdrawn: 'government.responseOutcome.withdrawn',
}

const steps = computed(() => SUBMISSION_STAGES.map((stage) => ({ label: t(STAGE_LABEL_KEYS[stage]) })))

const currentStepIndex = computed(() => {
  const index = SUBMISSION_STAGES.indexOf(props.stage)
  return index === -1 ? 0 : index
})

const outcomeLabel = computed(() => (props.responseOutcome ? t(OUTCOME_LABEL_KEYS[props.responseOutcome]) : undefined))
</script>

<template>
  <div class="flex flex-col gap-3">
    <Stepper :steps="steps" :current-step="currentStepIndex" />
    <div v-if="stage === 'Close' && outcomeLabel" class="flex items-center gap-2">
      <StatusBadge :label="t('government.workspacePage.outcomeBadge', { outcome: outcomeLabel })" :variant="getSubmissionOutcomeVariant(responseOutcome)" />
    </div>
  </div>
</template>
