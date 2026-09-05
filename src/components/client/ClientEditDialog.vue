<script setup lang="ts">
import { computed, onMounted, reactive, watch } from 'vue'
import { useI18n } from 'vue-i18n'

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

const { t } = useI18n()
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

const LANGUAGE_OPTIONS: SelectOption[] = [
  { label: 'English', value: 'English', labelKey: 'client.editDialog.languageEnglish' },
  { label: 'Arabic', value: 'Arabic', labelKey: 'client.editDialog.languageArabic' },
]
const CHANNEL_OPTIONS: SelectOption[] = [
  { label: 'Email', value: 'Email', labelKey: 'client.editDialog.channelEmail' },
  { label: 'WhatsApp', value: 'WhatsApp', labelKey: 'client.editDialog.channelWhatsapp' },
  { label: 'SMS', value: 'SMS', labelKey: 'client.editDialog.channelSms' },
  { label: 'Phone', value: 'Phone', labelKey: 'client.editDialog.channelPhone' },
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
  <BaseDialog :model-value="modelValue" :title="t('client.editDialog.title')" size="lg" @update:model-value="emit('update:modelValue', $event)">
    <div class="flex flex-col gap-6">
      <FormSection :title="t('client.editDialog.contactDetails')">
        <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
          <TextInput v-model="form.contactPerson" :label="t('client.editDialog.contactPerson')" required :error="errors.contactPerson" />
          <TextInput v-model="form.mobile" :label="t('client.editDialog.mobileNumber')" required :error="errors.mobile" />
          <TextInput v-model="form.email" :label="t('client.editDialog.emailAddress')" type="email" required :error="errors.email" />
          <TextInput v-model="form.city" :label="t('client.editDialog.city')" required :error="errors.city" />
          <SelectBox v-model="form.preferredLanguage" :label="t('client.editDialog.preferredLanguage')" :options="LANGUAGE_OPTIONS" />
          <SelectBox v-model="form.preferredChannel" :label="t('client.editDialog.preferredChannel')" :options="CHANNEL_OPTIONS" />
        </div>
      </FormSection>

      <FormSection :title="t('client.editDialog.relationship')">
        <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
          <SelectBox v-model="form.accountManagerId" :label="t('client.editDialog.accountManager')" required :options="accountManagerOptions" :error="errors.accountManagerId" />
        </div>
        <TextArea v-model="form.notes" :label="t('client.editDialog.internalNotes')" :hint="t('client.editDialog.internalNotesHint')" :rows="3" />
      </FormSection>

      <FormSection v-if="client.clientType === 'Individual'" :title="t('client.editDialog.personalInformation')">
        <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
          <TextInput v-model="form.individualProfile.fullLegalName" :label="t('client.editDialog.fullLegalName')" required :error="errors.fullLegalName" />
          <TextInput v-model="form.individualProfile.preferredName" :label="t('client.editDialog.preferredName')" />
          <TextInput v-model="form.individualProfile.nationality" :label="t('client.editDialog.nationality')" required :error="errors.nationality" />
          <DatePicker v-model="form.individualProfile.dateOfBirth" :label="t('client.editDialog.dateOfBirth')" required :max="maxDate" :error="errors.dateOfBirth" />
          <TextInput v-model="form.individualProfile.countryOfResidence" :label="t('client.editDialog.countryOfResidence')" required :error="errors.countryOfResidence" />
        </div>
      </FormSection>

      <FormSection v-else :title="t('client.editDialog.organisationInformation')">
        <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
          <TextInput v-model="form.organisationProfile.legalName" :label="t('client.editDialog.legalName')" required :error="errors.legalName" />
          <TextInput v-model="form.organisationProfile.tradeName" :label="t('client.editDialog.tradeName')" />
          <TextInput v-model="form.organisationProfile.organisationType" :label="t('client.editDialog.organisationType')" required :error="errors.organisationType" />
          <TextInput v-model="form.organisationProfile.registrationNumber" :label="t('client.editDialog.registrationNumber')" required :error="errors.registrationNumber" />
          <TextInput v-model="form.organisationProfile.tradeLicenceNumber" :label="t('client.editDialog.tradeLicenceNumber')" />
          <TextInput v-model="form.organisationProfile.countryOfRegistration" :label="t('client.editDialog.countryOfRegistration')" required :error="errors.countryOfRegistration" />
          <DatePicker v-model="form.organisationProfile.dateOfIncorporation" :label="t('client.editDialog.dateOfIncorporation')" required :max="maxDate" :error="errors.dateOfIncorporation" />
          <TextInput v-model="form.organisationProfile.website" :label="t('client.editDialog.website')" placeholder="example.com" :error="errors.website" />
        </div>
      </FormSection>
    </div>

    <template #footer>
      <BaseButton variant="secondary" @click="closeDialog">{{ t('common.cancel') }}</BaseButton>
      <BaseButton :loading="loading" @click="handleConfirm">{{ t('common.saveChanges') }}</BaseButton>
    </template>
  </BaseDialog>
</template>
