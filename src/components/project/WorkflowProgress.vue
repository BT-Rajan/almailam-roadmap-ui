<script setup lang="ts">
import { computed } from 'vue'

import Card from '@/components/common/Card.vue'
import Stepper from '@/components/common/Stepper.vue'
import type { WorkflowStage } from '@/types/Project'
import { WORKFLOW_STAGES } from '@/utils/projectHelpers'

interface Props {
  currentStage: WorkflowStage
}

const props = defineProps<Props>()

const steps = WORKFLOW_STAGES.map((stage) => ({ label: stage }))

const currentStepIndex = computed(() => {
  const index = WORKFLOW_STAGES.indexOf(props.currentStage)
  return index === -1 ? 0 : index
})
</script>

<template>
  <Card>
    <template #header>
      <h3 class="text-sm font-semibold text-neutral-800">Workflow Progress</h3>
    </template>
    <div class="overflow-x-auto pb-1">
      <div class="min-w-[720px]">
        <Stepper :steps="steps" :current-step="currentStepIndex" />
      </div>
    </div>
  </Card>
</template>
