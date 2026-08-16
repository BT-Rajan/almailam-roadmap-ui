<script setup lang="ts">
import { computed } from 'vue'

import DuplicateClientAlert from '@/components/client/DuplicateClientAlert.vue'
import DatePicker from '@/components/common/DatePicker.vue'
import FormSection from '@/components/common/FormSection.vue'
import RadioGroup from '@/components/common/RadioGroup.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextInput from '@/components/common/TextInput.vue'
import { CLIENT_TYPE_OPTIONS } from '@/constants/clientOptions'
import type { ClientDuplicateMatch } from '@/types/Client'
import type { ClientWizardForm } from '@/types/ClientWizard'
import type { FieldErrors } from '@/utils/clientValidation'
import { todayIso } from '@/utils/clientValidation'

defineProps<{
  duplicates: ClientDuplicateMatch[]
  errors: FieldErrors
}>()

defineEmits<{
  viewDuplicate: [clientId: string]
}>()

const form = defineModel<ClientWizardForm>({ required: true })

const isIndividual = computed(() => form.value.clientType === 'Individual')
const maxDate = todayIso()
</script>

<template>
  <div class="flex flex-col gap-6">
    <FormSection title="Client Type" description="Select the type of client being onboarded.">
      <RadioGroup v-model="form.clientType" :options="CLIENT_TYPE_OPTIONS" :vertical="false" />
    </FormSection>

    <DuplicateClientAlert :matches="duplicates" @view="$emit('viewDuplicate', $event)" />

    <FormSection v-if="isIndividual" title="Personal Information">
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

    <FormSection title="Contact Details">
      <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
        <TextInput v-model="form.mobile" label="Mobile Number" placeholder="+971 5X XXX XXXX" required :error="errors.mobile" />
        <TextInput v-model="form.email" label="Email Address" type="email" required :error="errors.email" />
        <SelectBox
          v-model="form.communicationPreference.preferredLanguage"
          label="Preferred Language"
          :options="[
            { label: 'English', value: 'English' },
            { label: 'Arabic', value: 'Arabic' },
          ]"
        />
        <TextInput v-model="form.city" label="City" required :error="errors.city" />
      </div>
    </FormSection>
  </div>
</template>
