<script setup lang="ts">
import { reactive, watch } from 'vue'
import { useI18n } from 'vue-i18n'

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

const { t } = useI18n()

const options = (): SelectOption[] =>
  (DOCUMENT_ALLOWED_TRANSITIONS[props.currentStatus] ?? []).map((status) => ({ label: status, value: status }))

const form = reactive({ status: '', reason: '' })
const errors = reactive({ status: '', reason: '' })

function validate(): boolean {
  errors.status = form.status ? '' : 'Please select a status'
  errors.reason = form.status === 'Rejected' && !form.reason.trim() ? 'A reason is required to reject a document' : ''
  return !errors.status && !errors.reason
}

watch(
  () => props.modelValue,
  (open) => {
    if (!open) return
    const available = options()
    form.status = available.length === 1 ? available[0].value : ''
    form.reason = ''
    validate()
  },
)

// Same "highlight empty mandatory fields immediately" fix as
// NewProjectWizardPage.vue (see the comment there) -- validate() was
// previously only run from handleConfirm, so Status (and Reason, once
// Rejected is picked) looked like ordinary optional fields until the
// first failed Confirm click. The modelValue watch above now also
// calls it as soon as the dialog opens; this keeps it live on every
// edit too.
watch(form, validate, { deep: true })

function closeDialog(): void {
  emit('update:modelValue', false)
}

function handleConfirm(): void {
  if (!validate()) return

  emit('confirm', { status: form.status as DocumentStatus, reason: form.reason.trim() || undefined })
}
</script>

<template>
  <BaseDialog :model-value="modelValue" :title="t('document.statusDialog.title')" @update:model-value="emit('update:modelValue', $event)">
    <div class="flex flex-col gap-4">
      <SelectBox v-model="form.status" :label="t('document.statusDialog.newStatus')" required :options="options()" :error="errors.status" />
      <TextArea
        v-model="form.reason"
        :label="t('document.statusDialog.reason')"
        :required="form.status === 'Rejected'"
        :error="errors.reason"
        :hint="form.status === 'Rejected' ? t('document.statusDialog.reasonRequiredHint') : t('common.optional')"
        :rows="3"
      />
    </div>

    <template #footer>
      <BaseButton variant="secondary" @click="closeDialog">{{ t('common.cancel') }}</BaseButton>
      <BaseButton :loading="loading" @click="handleConfirm">{{ t('common.confirm') }}</BaseButton>
    </template>
  </BaseDialog>
</template>
