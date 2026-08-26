<script setup lang="ts">
import { computed, onMounted, reactive, watch } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import DatePicker from '@/components/common/DatePicker.vue'
import FormSection from '@/components/common/FormSection.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextArea from '@/components/common/TextArea.vue'
import TextInput from '@/components/common/TextInput.vue'
import { useUserStore } from '@/stores/userStore'
import type { Client } from '@/types/Client'
import type { SelectOption } from '@/types/Ui'
import type { ClientEditForm, FieldErrors } from '@/utils/clientValidation'
import { hasErrors, todayIso, validateClientEditForm } from '@/utils/clientValidation'

const props = defineProps<{
  modelValue: boolean
  client: Client
  loading?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  confirm: [payload: ClientEditForm]
}>()

const maxDate = todayIso()
const userStore = useUserStore()

onMounted(() => {
  if (userStore.users.length === 0) userStore.loadUsers()
})

// Any active staff member can be assigned as the relationship owner --
// Viewer is excluded since that role is read-only/external-stakeholder
// by design elsewhere in this app, not someone who'd manage a client.
// No "Unassigned" placeholder option: account manager is now a
// required field (see clientValidation.ts's validateClientEditForm) --
// an existing client with none assigned will need one picked the next
// time it's edited, same as any other newly-required field would.
const accountManagerOptions = computed<SelectOption[]>(() =>
  userStore.users
    .filter((user) => user.status === 'Active' && user.role !== 'Viewer')
    .map((user) => ({ label: `${user.name} (${user.role})`, value: user.id })),
)

const LANGUAGE_OPTIONS = [
  { label: 'English', value: 'English' },
  { label: 'Arabic', value: 'Arabic' },
]
const CHANNEL_OPTIONS = [
  { label: 'Email', value: 'Email' },
  { label: 'WhatsApp', value: 'WhatsApp' },
  { label: 'SMS', value: 'SMS' },
  { label: 'Phone', value: 'Phone' },
]

function emptyForm(): ClientEditForm {
  return {
    contactPerson: '',
    mobile: '',
    email: '',
    city: '',
    preferredLanguage: 'English',
    preferredChannel: 'Email',
    accountManagerId: '',
    notes: '',
    individualProfile: { fullLegalName: '', preferredName: '', nationality: '', dateOfBirth: '', countryOfResidence: '' },
    organisationProfile: {
      legalName: '',
      tradeName: '',
      organisationType: '',
      registrationNumber: '',
      tradeLicenceNumber: '',
      taxIdentificationNumber: '',
      countryOfRegistration: '',
      dateOfIncorporation: '',
      website: '',
    },
  }
}

const form = reactive<ClientEditForm>(emptyForm())
const errors = reactive<FieldErrors>({})

// Re-populate from the current client every time the dialog opens, so
// edits from a previous open (cancelled or not) never leak into the next.
watch(
  () => props.modelValue,
  (open) => {
    if (!open) return
    Object.assign(form, emptyForm())
    Object.keys(errors).forEach((key) => delete errors[key])

    form.contactPerson = props.client.contactPerson
    form.mobile = props.client.mobile
    form.email = props.client.email
    form.city = props.client.city
    form.preferredLanguage = props.client.communicationPreference.preferredLanguage
    form.preferredChannel = props.client.communicationPreference.preferredChannel
    form.accountManagerId = props.client.accountManagerId ?? ''
    form.notes = props.client.notes ?? ''

    if (props.client.individualProfile) {
      Object.assign(form.individualProfile, {
        fullLegalName: props.client.individualProfile.fullLegalName,
        preferredName: props.client.individualProfile.preferredName ?? '',
        nationality: props.client.individualProfile.nationality,
        dateOfBirth: props.client.individualProfile.dateOfBirth,
        countryOfResidence: props.client.individualProfile.countryOfResidence,
      })
    }
    if (props.client.organisationProfile) {
      Object.assign(form.organisationProfile, {
        legalName: props.client.organisationProfile.legalName,
        tradeName: props.client.organisationProfile.tradeName ?? '',
        organisationType: props.client.organisationProfile.organisationType,
        registrationNumber: props.client.organisationProfile.registrationNumber,
        tradeLicenceNumber: props.client.organisationProfile.tradeLicenceNumber ?? '',
        taxIdentificationNumber: props.client.organisationProfile.taxIdentificationNumber ?? '',
        countryOfRegistration: props.client.organisationProfile.countryOfRegistration,
        dateOfIncorporation: props.client.organisationProfile.dateOfIncorporation,
        website: props.client.organisationProfile.website ?? '',
      })
    }
  },
)

function closeDialog(): void {
  emit('update:modelValue', false)
}

function handleConfirm(): void {
  const result = validateClientEditForm(form, props.client.clientType)
  Object.keys(errors).forEach((key) => delete errors[key])
  Object.assign(errors, result)
  if (hasErrors(result)) return

  emit('confirm', form)
}
</script>

<template>
  <BaseDialog :model-value="modelValue" title="Edit Client" size="lg" @update:model-value="emit('update:modelValue', $event)">
    <div class="flex flex-col gap-6">
      <FormSection title="Contact Details">
        <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
          <TextInput v-model="form.contactPerson" label="Contact Person" required :error="errors.contactPerson" />
          <TextInput v-model="form.mobile" label="Mobile Number" required :error="errors.mobile" />
          <TextInput v-model="form.email" label="Email Address" type="email" required :error="errors.email" />
          <TextInput v-model="form.city" label="City" required :error="errors.city" />
          <SelectBox v-model="form.preferredLanguage" label="Preferred Language" :options="LANGUAGE_OPTIONS" />
          <SelectBox v-model="form.preferredChannel" label="Preferred Contact Channel" :options="CHANNEL_OPTIONS" />
        </div>
      </FormSection>

      <FormSection title="Relationship">
        <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
          <SelectBox v-model="form.accountManagerId" label="Account Manager" required :options="accountManagerOptions" :error="errors.accountManagerId" />
        </div>
        <TextArea v-model="form.notes" label="Internal Notes" hint="Preferences, risk flags, or handling instructions -- visible to staff only." :rows="3" />
      </FormSection>

      <FormSection v-if="client.clientType === 'Individual'" title="Personal Information">
        <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
          <TextInput v-model="form.individualProfile.fullLegalName" label="Full Legal Name" required :error="errors.fullLegalName" />
          <TextInput v-model="form.individualProfile.preferredName" label="Preferred Name" />
          <TextInput v-model="form.individualProfile.nationality" label="Nationality" required :error="errors.nationality" />
          <DatePicker v-model="form.individualProfile.dateOfBirth" label="Date of Birth" required :max="maxDate" :error="errors.dateOfBirth" />
          <TextInput v-model="form.individualProfile.countryOfResidence" label="Country of Residence" required :error="errors.countryOfResidence" />
        </div>
      </FormSection>

      <FormSection v-else title="Organisation Information">
        <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
          <TextInput v-model="form.organisationProfile.legalName" label="Legal Name" required :error="errors.legalName" />
          <TextInput v-model="form.organisationProfile.tradeName" label="Trade Name" />
          <TextInput v-model="form.organisationProfile.organisationType" label="Organisation Type" required :error="errors.organisationType" />
          <TextInput v-model="form.organisationProfile.registrationNumber" label="Registration Number" required :error="errors.registrationNumber" />
          <TextInput v-model="form.organisationProfile.tradeLicenceNumber" label="Trade Licence Number" />
          <TextInput v-model="form.organisationProfile.countryOfRegistration" label="Country of Registration" required :error="errors.countryOfRegistration" />
          <DatePicker v-model="form.organisationProfile.dateOfIncorporation" label="Date of Incorporation" required :max="maxDate" :error="errors.dateOfIncorporation" />
          <TextInput v-model="form.organisationProfile.website" label="Website" placeholder="example.com" :error="errors.website" />
        </div>
      </FormSection>
    </div>

    <template #footer>
      <BaseButton variant="secondary" @click="closeDialog">Cancel</BaseButton>
      <BaseButton :loading="loading" @click="handleConfirm">Save Changes</BaseButton>
    </template>
  </BaseDialog>
</template>
