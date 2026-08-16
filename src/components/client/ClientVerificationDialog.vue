<script setup lang="ts">
import { reactive, ref, watch } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextArea from '@/components/common/TextArea.vue'
import TextInput from '@/components/common/TextInput.vue'
import { useFormValidation } from '@/composables/useFormValidation'
import { CLIENT_VERIFICATION_RESULT_OPTIONS } from '@/constants/clientOptions'
import type { ClientVerificationResult } from '@/types/Client'
import { validators } from '@/utils/validators'

const props = defineProps<{
  modelValue: boolean
  /** Pre-fills the item field and links the record to this document (e.g. opened from a document card). */
  initialItem?: string
  documentId?: string
  loading?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  confirm: [payload: { item: string; result: ClientVerificationResult; notes?: string; documentId?: string }]
}>()

const form = reactive({
  item: '',
  result: 'Verified' as ClientVerificationResult,
  notes: '',
})

const { errors, setRules, validateAll, clearErrors } = useFormValidation()
setRules({ item: [validators.required('Please describe what was checked')] })

// documentId is fixed to the document that opened the dialog (if any) --
// not user-editable, so it isn't part of the reactive form.
const activeDocumentId = ref<string | undefined>(undefined)

watch(
  () => props.modelValue,
  (open) => {
    if (!open) return
    form.item = props.initialItem ?? ''
    form.result = 'Verified'
    form.notes = ''
    activeDocumentId.value = props.documentId
    clearErrors()
  },
)

function closeDialog(): void {
  emit('update:modelValue', false)
}

function handleConfirm(): void {
  if (!validateAll({ item: form.item })) return

  emit('confirm', {
    item: form.item.trim(),
    result: form.result,
    notes: form.notes.trim() || undefined,
    documentId: activeDocumentId.value,
  })
}
</script>

<template>
  <BaseDialog :model-value="modelValue" title="Record Verification" @update:model-value="emit('update:modelValue', $event)">
    <div class="flex flex-col gap-4">
      <TextInput
        v-model="form.item"
        label="What was checked"
        placeholder="e.g. Trade Licence, Registration Number"
        required
        :disabled="Boolean(documentId)"
        :error="errors.item"
      />
      <SelectBox v-model="form.result" label="Result" required :options="CLIENT_VERIFICATION_RESULT_OPTIONS" />
      <TextArea v-model="form.notes" label="Notes" hint="Optional" :rows="3" />
    </div>

    <template #footer>
      <BaseButton variant="secondary" @click="closeDialog">Cancel</BaseButton>
      <BaseButton :loading="loading" @click="handleConfirm">Save Verification</BaseButton>
    </template>
  </BaseDialog>
</template>
