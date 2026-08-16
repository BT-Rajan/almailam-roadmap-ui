<script setup lang="ts">
import { reactive, watch } from 'vue'

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
    :title="contact ? 'Edit Contact' : 'Add Contact'"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <div class="flex flex-col gap-4">
      <TextInput v-model="form.name" label="Name" required :error="errors.name" />
      <SelectBox v-model="form.contactType" label="Contact Type" :options="CLIENT_CONTACT_TYPE_OPTIONS" />
      <TextInput v-model="form.mobile" label="Mobile Number" required :error="errors.mobile" />
      <TextInput v-model="form.email" label="Email Address" type="email" required :error="errors.email" />
      <ToggleSwitch v-model="form.isAuthorisedRepresentative" label="Authorised Representative" />
    </div>

    <template #footer>
      <BaseButton variant="secondary" @click="closeDialog">Cancel</BaseButton>
      <BaseButton :loading="loading" @click="handleConfirm">{{ contact ? 'Save Changes' : 'Add Contact' }}</BaseButton>
    </template>
  </BaseDialog>
</template>
