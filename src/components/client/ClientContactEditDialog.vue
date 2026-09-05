<script setup lang="ts">
import { reactive, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextInput from '@/components/common/TextInput.vue'
import ToggleSwitch from '@/components/common/ToggleSwitch.vue'
import { CLIENT_CONTACT_TYPE_OPTIONS } from '@/constants/clientOptions'
import type { ClientContact, ClientContactType } from '@/types/Client'

const props = defineProps<{
  modelValue: boolean
  /** Present when editing an existing contact; absent when adding a new one. */
  contact?: ClientContact
  loading?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  confirm: [payload: { name: string; contactType: ClientContactType; mobile: string; email: string; isAuthorisedRepresentative: boolean }]
}>()

const { t } = useI18n()

function emptyForm() {
  return { name: '', contactType: 'Other' as ClientContactType, mobile: '', email: '', isAuthorisedRepresentative: false }
}

const form = reactive(emptyForm())
const errors = reactive({ name: '', mobile: '', email: '' })

watch(
  () => props.modelValue,
  (open) => {
    if (!open) return
    Object.assign(form, props.contact ? { ...props.contact } : emptyForm())
    errors.name = ''
    errors.mobile = ''
    errors.email = ''
  },
)

// Selecting the "Authorised Representative" contact type and the
// "authorised to act on the client's behalf" toggle used to be two
// completely independent fields with the same-sounding label -- easy to
// set inconsistently (a contact typed as the authorised representative
// but with the flag left off). One-directional: explicitly typing
// someone as the authorised representative always implies the flag;
// the reverse isn't forced, since e.g. a Billing Contact can
// independently be authorised to act without being *the* designated
// representative contact.
watch(
  () => form.contactType,
  (type) => {
    if (type === 'Authorised Representative') form.isAuthorisedRepresentative = true
  },
)

function closeDialog(): void {
  emit('update:modelValue', false)
}

function isValidPhone(value: string): boolean {
  return /^[\d\s\-+()]+$/.test(value) && value.replace(/\D/g, '').length >= 7
}

function handleConfirm(): void {
  errors.name = form.name.trim() ? '' : 'Name is required'
  errors.mobile = !form.mobile.trim() ? 'Mobile number is required' : !isValidPhone(form.mobile) ? 'Enter a valid phone number' : ''
  errors.email = !form.email.trim()
    ? 'Email address is required'
    : /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)
      ? ''
      : 'Enter a valid email address'
  if (errors.name || errors.mobile || errors.email) return

  emit('confirm', { ...form })
}
</script>

<template>
  <BaseDialog
    :model-value="modelValue"
    :title="contact ? t('client.contactEditDialog.editTitle') : t('client.contactEditDialog.addTitle')"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <div class="flex flex-col gap-4">
      <TextInput v-model="form.name" :label="t('client.contactEditDialog.name')" required :error="errors.name" />
      <SelectBox v-model="form.contactType" :label="t('client.contactEditDialog.contactType')" :options="CLIENT_CONTACT_TYPE_OPTIONS" />
      <TextInput v-model="form.mobile" :label="t('client.contactEditDialog.mobileNumber')" required :error="errors.mobile" />
      <TextInput v-model="form.email" :label="t('client.contactEditDialog.emailAddress')" type="email" required :error="errors.email" />
      <ToggleSwitch v-model="form.isAuthorisedRepresentative" :label="t('client.contactEditDialog.authorisedToggle')" />
    </div>

    <template #footer>
      <BaseButton variant="secondary" @click="closeDialog">{{ t('common.cancel') }}</BaseButton>
      <BaseButton :loading="loading" @click="handleConfirm">{{ contact ? t('common.saveChanges') : t('client.contactEditDialog.addContact') }}</BaseButton>
    </template>
  </BaseDialog>
</template>
