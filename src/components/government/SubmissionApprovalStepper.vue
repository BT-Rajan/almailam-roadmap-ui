<script setup lang="ts">
import { computed } from 'vue'

import StatusBadge from '@/components/common/StatusBadge.vue'
import Stepper from '@/components/common/Stepper.vue'
import type { SubmissionStatus } from '@/types/Submission'
import { SUBMISSION_STAGES, getSubmissionStatusVariant } from '@/utils/submissionHelpers'

interface Props {
  status: SubmissionStatus
}

const props = defineProps<Props>()

const steps = SUBMISSION_STAGES.map((stage) => ({ label: stage }))

const currentStepIndex = computed(() => {
  const index = SUBMISSION_STAGES.indexOf(props.status as (typeof SUBMISSION_STAGES)[number])
  return index === -1 ? 0 : index
})
</script>

<template>
  <div>
    <Stepper v-if="status !== 'Rejected'" :steps="steps" :current-step="currentStepIndex" />
    <div v-else class="flex items-center gap-2">
      <StatusBadge label="Rejected" :variant="getSubmissionStatusVariant('Rejected')" />
      <p class="text-sm text-neutral-500">This submission was rejected by the authority.</p>
    </div>
  </div>
</template>
