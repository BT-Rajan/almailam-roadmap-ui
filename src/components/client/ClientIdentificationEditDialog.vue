<script setup lang="ts">
import { computed, reactive, watch } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import DatePicker from '@/components/common/DatePicker.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextInput from '@/components/common/TextInput.vue'
import { getDefaultIdentificationTypeForClientType, getIdentificationTypeOptionsForClientType } from '@/constants/clientOptions'
import type { ClientIdentification, ClientIdentificationType, ClientType } from '@/types/Client'
import { todayIso } from '@/utils/clientValidation'

const props = defineProps<{
  modelValue: boolean
  identification?: ClientIdentification
  clientType: ClientType
  loading?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  confirm: [
    payload: {
      documentType: ClientIdentificationType
      documentNumber: string
      issueDate: string
      expiryDate: string
      issuingCountry: string
    },
  ]
}>()

const maxDate = todayIso()

// Individuals identify with Civil ID/Passport; entity clients (Company/
// Organisation/Government Entity) identify with a trade licence instead --
// mirrors the same client-type-aware filtering applied to the onboarding
// wizard's ClientIdentificationStep.vue.
const identificationTypeOptions = computed(() => getIdentificationTypeOptionsForClientType(props.clientType))

function emptyForm() {
  return { documentType: getDefaultIdentificationTypeForClientType(props.clientType), documentNumber: '', issueDate: '', expiryDate: '', issuingCountry: '' }
}

const form = reactive(emptyForm())
const errors = reactive({ documentNumber: '', issueDate: '', expiryDate: '', issuingCountry: '' })

watch(
  () => props.modelValue,
  (open) => {
    if (!open) return
    Object.assign(form, props.identification ? { ...props.identification } : emptyForm())
    errors.documentNumber = ''
    errors.issueDate = ''
    errors.expiryDate = ''
    errors.issuingCountry = ''
  },
)

function closeDialog(): void {
  emit('update:modelValue', false)
}

function handleConfirm(): void {
  errors.documentNumber = form.documentNumber.trim() ? '' : 'Document number is required'
  errors.issueDate = !form.issueDate
    ? 'Issue date is required'
    : form.issueDate > maxDate
      ? 'Issue date cannot be in the future'
      : ''
  errors.expiryDate = !form.expiryDate
    ? 'Expiry date is required'
    : form.issueDate && form.expiryDate <= form.issueDate
      ? 'Expiry date must be after the issue date'
      : ''
  errors.issuingCountry = form.issuingCountry.trim() ? '' : 'Issuing country is required'
  if (errors.documentNumber || errors.issueDate || errors.expiryDate || errors.issuingCountry) return

  emit('confirm', { ...form })
}
</script>

<template>
  <BaseDialog
    :model-value="modelValue"
    :title="identification ? 'Edit Identification' : 'Add Identification'"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <div class="flex flex-col gap-4">
      <SelectBox v-model="form.documentType" label="Document Type" :options="identificationTypeOptions" />
      <TextInput v-model="form.documentNumber" label="Document Number" required :error="errors.documentNumber" />
      <DatePicker v-model="form.issueDate" label="Issue Date" required :max="maxDate" :error="errors.issueDate" />
      <DatePicker v-model="form.expiryDate" label="Expiry Date" required :error="errors.expiryDate" />
      <TextInput v-model="form.issuingCountry" label="Issuing Country" required :error="errors.issuingCountry" />
    </div>

    <template #footer>
      <BaseButton variant="secondary" @click="closeDialog">Cancel</BaseButton>
      <BaseButton :loading="loading" @click="handleConfirm">{{ identification ? 'Save Changes' : 'Add Identification' }}</BaseButton>
    </template>
  </BaseDialog>
</template>
