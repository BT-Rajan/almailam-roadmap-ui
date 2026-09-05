<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import StatusBadge from '@/components/common/StatusBadge.vue'
import Stepper from '@/components/common/Stepper.vue'
import type { SubmissionStatus } from '@/types/Submission'
import { SUBMISSION_STAGES, getSubmissionStatusVariant } from '@/utils/submissionHelpers'

interface Props {
  status: SubmissionStatus
}

const props = defineProps<Props>()
const { t } = useI18n()

const STAGE_LABEL_KEYS: Record<string, string> = {
  Draft: 'government.submissionStatus.draft',
  Submitted: 'government.submissionStatus.submitted',
  'Under Review': 'government.submissionStatus.underReview',
  'Comments Received': 'government.submissionStatus.commentsReceived',
  Approved: 'government.submissionStatus.approved',
}

const steps = computed(() => SUBMISSION_STAGES.map((stage) => ({ label: t(STAGE_LABEL_KEYS[stage]) })))

const currentStepIndex = computed(() => {
  const index = SUBMISSION_STAGES.indexOf(props.status as (typeof SUBMISSION_STAGES)[number])
  return index === -1 ? 0 : index
})
</script>

<template>
  <div>
    <Stepper v-if="status !== 'Rejected'" :steps="steps" :current-step="currentStepIndex" />
    <div v-else class="flex items-center gap-2">
      <StatusBadge :label="t('government.submissionStatus.rejected')" :variant="getSubmissionStatusVariant('Rejected')" />
      <p class="text-sm text-text-muted">{{ t('government.approvalStepper.rejectedNotice') }}</p>
    </div>
  </div>
</template>
