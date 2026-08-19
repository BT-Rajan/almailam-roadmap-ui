<script setup lang="ts">
import { reactive, watch } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextArea from '@/components/common/TextArea.vue'
import type { DocumentStatus } from '@/types/Document'
import type { SelectOption } from '@/types/Ui'

// Mirrors backend/app/core/status_transitions.py's
// DOCUMENT_ALLOWED_TRANSITIONS exactly. The backend re-validates
// independently; this only drives which options the UI offers.
const DOCUMENT_ALLOWED_TRANSITIONS: Record<string, DocumentStatus[]> = {
  Draft: ['Under Review'],
  'Under Review': ['Approved', 'Rejected'],
  Approved: [],
  Rejected: ['Draft'],
}

const props = defineProps<{
  modelValue: boolean
  currentStatus: DocumentStatus
  loading?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  confirm: [payload: { status: DocumentStatus; reason?: string }]
}>()

const options = (): SelectOption[] =>
  (DOCUMENT_ALLOWED_TRANSITIONS[props.currentStatus] ?? []).map((status) => ({ label: status, value: status }))

const form = reactive({ status: '', reason: '' })
const errors = reactive({ status: '', reason: '' })

watch(
  () => props.modelValue,
  (open) => {
    if (!open) return
    const available = options()
    form.status = available.length === 1 ? available[0].value : ''
    form.reason = ''
    errors.status = ''
    errors.reason = ''
  },
)

function closeDialog(): void {
  emit('update:modelValue', false)
}

function handleConfirm(): void {
  errors.status = form.status ? '' : 'Please select a status'
  errors.reason = form.status === 'Rejected' && !form.reason.trim() ? 'A reason is required to reject a document' : ''
  if (errors.status || errors.reason) return

  emit('confirm', { status: form.status as DocumentStatus, reason: form.reason.trim() || undefined })
}
</script>

<template>
  <BaseDialog :model-value="modelValue" title="Change Document Status" @update:model-value="emit('update:modelValue', $event)">
    <div class="flex flex-col gap-4">
      <SelectBox v-model="form.status" label="New Status" required :options="options()" :error="errors.status" />
      <TextArea
        v-model="form.reason"
        label="Reason"
        :required="form.status === 'Rejected'"
        :error="errors.reason"
        :hint="form.status === 'Rejected' ? 'Required when rejecting' : 'Optional'"
        :rows="3"
      />
    </div>

    <template #footer>
      <BaseButton variant="secondary" @click="closeDialog">Cancel</BaseButton>
      <BaseButton :loading="loading" @click="handleConfirm">Confirm</BaseButton>
    </template>
  </BaseDialog>
</template>
