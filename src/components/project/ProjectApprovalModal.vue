<script setup lang="ts">
import { CheckCircle2, Circle, RotateCcw } from '@lucide/vue'
import { watch } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import { useProjectApprovalStore } from '@/stores/projectApprovalStore'
import { useToastStore } from '@/stores/toastStore'

const props = defineProps<{
  modelValue: boolean
  projectId: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const store = useProjectApprovalStore()
const toastStore = useToastStore()

function loadData(): void {
  store.loadSteps(props.projectId)
}

// Loads fresh every time the modal opens rather than once on mount --
// this is a dialog that can be opened and closed repeatedly across a
// session, not a page that loads once.
watch(
  () => props.modelValue,
  (isOpen) => {
    if (isOpen) loadData()
  },
)

async function handleComplete(stepId: string): Promise<void> {
  await store.completeStep(props.projectId, stepId)
  if (store.mutationError) toastStore.show('error', 'Could not complete step', store.mutationError)
}

async function handleUncomplete(stepId: string): Promise<void> {
  await store.uncompleteStep(props.projectId, stepId)
  if (store.mutationError) toastStore.show('error', 'Could not undo step', store.mutationError)
}
</script>

<template>
  <BaseDialog :model-value="modelValue" title="Approval Process" size="md" @update:model-value="emit('update:modelValue', $event)">
    <p class="mb-4 text-xs text-text-muted">
      A separate, new tracker for the project approval sequence -- independent of the project's own Stage and Status above.
      Steps are completed in order; undoing is only possible for the most recently completed step.
    </p>

    <ErrorState v-if="store.error" :description="store.error" @retry="loadData" />

    <SkeletonLoader v-else-if="store.isLoading" :rows="5" />

    <ol v-else class="flex flex-col gap-2">
      <li
        v-for="step in store.steps"
        :key="step.id"
        class="flex items-center gap-3 rounded-lg border p-3"
        :class="step.status === 'Completed' ? 'border-success-200 bg-success-50' : 'border-border-light bg-bg-card'"
      >
        <CheckCircle2 v-if="step.status === 'Completed'" class="h-5 w-5 shrink-0 text-success-600" />
        <Circle v-else class="h-5 w-5 shrink-0 text-text-muted" />

        <div class="min-w-0 flex-1">
          <p class="text-sm font-medium text-text-primary">{{ step.name }}</p>
          <p v-if="step.status === 'Completed' && step.completedByName" class="text-xs text-text-muted">
            Completed by {{ step.completedByName }}
          </p>
        </div>

        <BaseButton v-if="step.id === store.nextActionableStepId" size="sm" @click="handleComplete(step.id)">
          Mark Complete
        </BaseButton>
        <BaseButton
          v-else-if="step.id === store.lastCompletedStepId"
          size="sm"
          variant="ghost"
          :icon="RotateCcw"
          @click="handleUncomplete(step.id)"
        >
          Undo
        </BaseButton>
      </li>
    </ol>

    <template #footer>
      <BaseButton variant="secondary" @click="emit('update:modelValue', false)">Close</BaseButton>
    </template>
  </BaseDialog>
</template>
