<script setup lang="ts">
import { computed, reactive, watch } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextArea from '@/components/common/TextArea.vue'
import {
  PROJECT_STAGE_ALLOWED_TRANSITIONS,
  PROJECT_STATUS_ALLOWED_TRANSITIONS,
  isStageReasonRequired,
  isStatusReasonRequired,
} from '@/constants/projectOptions'
import { getWorkflowStageLabel } from '@/utils/projectHelpers'

const props = withDefaults(
  defineProps<{
    modelValue: boolean
    kind: 'stage' | 'status'
    currentValue: string
    loading?: boolean
    // Only meaningful for kind="stage" -- whether this project's
    // workflow includes a Design/Supervision stage at all, so a project
    // that skips one isn't offered it as a stage to move into.
    includesDesign?: boolean
    includesSupervision?: boolean
  }>(),
  { includesDesign: true, includesSupervision: true },
)

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  confirm: [payload: { value: string; reason?: string }]
}>()

const title = computed(() => (props.kind === 'stage' ? 'Change Workflow Stage' : 'Change Project Status'))
const fieldLabel = computed(() => (props.kind === 'stage' ? 'New Stage' : 'New Status'))

const options = computed(() => {
  const table = props.kind === 'stage' ? PROJECT_STAGE_ALLOWED_TRANSITIONS : PROJECT_STATUS_ALLOWED_TRANSITIONS
  const targets = (table[props.currentValue] ?? []).filter((value) => {
    if (props.kind !== 'stage') return true
    if (value === 'Design') return props.includesDesign
    if (value === 'Supervision') return props.includesSupervision
    return true
  })
  return targets.map((value) => ({
    label: props.kind === 'stage' ? getWorkflowStageLabel(value) : value,
    value,
  }))
})

const form = reactive({ value: '', reason: '' })
const errors = reactive({ value: '', reason: '' })

const reasonRequired = computed(() => {
  if (!form.value) return false
  return props.kind === 'stage'
    ? isStageReasonRequired(props.currentValue, form.value)
    : isStatusReasonRequired(props.currentValue, form.value)
})

watch(
  () => props.modelValue,
  (open) => {
    if (!open) return
    form.value = options.value.length === 1 ? options.value[0].value : ''
    form.reason = ''
    errors.value = ''
    errors.reason = ''
  },
)

function closeDialog(): void {
  emit('update:modelValue', false)
}

function handleConfirm(): void {
  errors.value = form.value ? '' : 'Please select an option'
  errors.reason = reasonRequired.value && !form.reason.trim() ? 'A reason is required for this change' : ''
  if (errors.value || errors.reason) return

  emit('confirm', { value: form.value, reason: form.reason.trim() || undefined })
}
</script>

<template>
  <BaseDialog :model-value="modelValue" :title="title" @update:model-value="emit('update:modelValue', $event)">
    <div class="flex flex-col gap-4">
      <SelectBox v-model="form.value" :label="fieldLabel" required :options="options" :error="errors.value" />
      <TextArea
        v-model="form.reason"
        label="Reason"
        :required="reasonRequired"
        :error="errors.reason"
        :hint="reasonRequired ? 'Required for this change' : 'Optional'"
        :rows="3"
      />
    </div>

    <template #footer>
      <BaseButton variant="secondary" @click="closeDialog">Cancel</BaseButton>
      <BaseButton :loading="loading" @click="handleConfirm">Confirm</BaseButton>
    </template>
  </BaseDialog>
</template>
