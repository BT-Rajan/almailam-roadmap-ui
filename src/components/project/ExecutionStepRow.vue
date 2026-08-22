<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import TextArea from '@/components/common/TextArea.vue'
import ExecutionStepProgressControl from '@/components/project/ExecutionStepProgressControl.vue'
import type { ProjectExecutionStep } from '@/types/ExecutionStep'

const props = defineProps<{
  step: ProjectExecutionStep
  isSaving: boolean
}>()

const emit = defineEmits<{
  save: [percentage: number, remarks: string]
}>()

const percentageDraft = ref(props.step.completionPercentage)
const remarksDraft = ref(props.step.remarks ?? '')

// The step prop is replaced (not mutated) with the server's response
// after every save, so re-seed the draft from it whenever that
// happens -- picks up the saved values as the new baseline for the
// dirty check below.
watch(
  () => props.step,
  (step) => {
    percentageDraft.value = step.completionPercentage
    remarksDraft.value = step.remarks ?? ''
  },
)

const isDirty = computed(
  () => percentageDraft.value !== props.step.completionPercentage || remarksDraft.value !== (props.step.remarks ?? ''),
)

function handleSave(): void {
  emit('save', percentageDraft.value, remarksDraft.value)
}
</script>

<template>
  <li
    class="flex flex-col gap-3 rounded-lg border p-3"
    :class="
      percentageDraft === 100
        ? 'border-success-100 bg-success-50'
        : percentageDraft > 0
          ? 'border-info-100 bg-info-50'
          : 'border-border-light bg-bg-card'
    "
  >
    <div class="flex items-start justify-between gap-3">
      <div class="min-w-0 flex-1">
        <p class="text-sm font-medium text-text-primary">
          {{ step.name }}
          <span v-if="step.isOptional" class="ml-1 text-xs font-normal text-text-muted">(optional)</span>
        </p>
        <p class="text-xs text-text-muted">{{ step.weightPercentage }}% weight</p>
      </div>
      <BaseButton size="sm" :disabled="!isDirty" :loading="isSaving" @click="handleSave">Save</BaseButton>
    </div>

    <ExecutionStepProgressControl v-model="percentageDraft" :disabled="isSaving" />

    <TextArea v-model="remarksDraft" placeholder="Remarks (optional)" :rows="2" :disabled="isSaving" />
  </li>
</template>
