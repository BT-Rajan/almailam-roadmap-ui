<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'

import DuplicateClientAlert from '@/components/client/DuplicateClientAlert.vue'
import DatePicker from '@/components/common/DatePicker.vue'
import FormSection from '@/components/common/FormSection.vue'
import RadioGroup from '@/components/common/RadioGroup.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextInput from '@/components/common/TextInput.vue'
import { CLIENT_TYPE_OPTIONS } from '@/constants/clientOptions'
import { useUserStore } from '@/stores/userStore'
import type { ClientDuplicateMatch } from '@/types/Client'
import type { ClientWizardForm } from '@/types/ClientWizard'
import type { SelectOption } from '@/types/Ui'
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

const { t } = useI18n()

const isIndividual = computed(() => form.value.clientType === 'Individual')
const maxDate = todayIso()

const userStore = useUserStore()
onMounted(() => {
  if (userStore.users.length === 0) userStore.loadUsers()
})
const accountManagerOptions = computed<SelectOption[]>(() =>
  userStore.users
    .filter((user) => user.status === 'Active' && user.role !== 'Viewer')
    .map((user) => ({ label: `${user.name} (${user.role})`, value: user.id })),
)

const languageOptions = computed<SelectOption[]>(() => [
  { label: t('governmentFormOptions.language.english'), value: 'English' },
  { label: t('governmentFormOptions.language.arabic'), value: 'Arabic' },
])
</script>

<template>
  <div class="flex flex-col gap-6">
    <FormSection :title="t('client.basicInfoStep.clientTypeTitle')" :description="t('client.basicInfoStep.clientTypeDescription')">
      <RadioGroup v-model="form.clientType" :options="CLIENT_TYPE_OPTIONS" :vertical="false" />
    </FormSection>

    <DuplicateClientAlert :matches="duplicates" @view="$emit('viewDuplicate', $event)" />

    <FormSection v-if="isIndividual" :title="t('client.basicInfoStep.personalInformation')">
      <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
        <TextInput v-model="form.individualProfile.fullLegalName" :label="t('client.basicInfoStep.fullLegalName')" required :error="errors.fullLegalName" />
        <TextInput v-model="form.individualProfile.preferredName" :label="t('client.basicInfoStep.preferredName')" />
        <TextInput v-model="form.individualProfile.nationality" :label="t('client.basicInfoStep.nationality')" required :error="errors.nationality" />
        <DatePicker v-model="form.individualProfile.dateOfBirth" :label="t('client.basicInfoStep.dateOfBirth')" required :max="maxDate" :error="errors.dateOfBirth" />
      </div>
    </FormSection>

    <FormSection v-else :title="t('client.basicInfoStep.organisationInformation')">
      <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
        <TextInput v-model="form.organisationProfile.legalName" :label="t('client.basicInfoStep.legalName')" required :error="errors.legalName" />
        <TextInput v-model="form.organisationProfile.tradeName" :label="t('client.basicInfoStep.tradeName')" />
        <TextInput v-model="form.organisationProfile.organisationType" :label="t('client.basicInfoStep.organisationType')" required :error="errors.organisationType" />
        <TextInput v-model="form.organisationProfile.registrationNumber" :label="t('client.basicInfoStep.registrationNumber')" required :error="errors.registrationNumber" />
        <TextInput v-model="form.organisationProfile.tradeLicenceNumber" :label="t('client.basicInfoStep.tradeLicenceNumber')" />
        <TextInput v-model="form.organisationProfile.countryOfRegistration" :label="t('client.basicInfoStep.countryOfRegistration')" required :error="errors.countryOfRegistration" />
        <DatePicker v-model="form.organisationProfile.dateOfIncorporation" :label="t('client.basicInfoStep.dateOfIncorporation')" required :max="maxDate" :error="errors.dateOfIncorporation" />
        <TextInput v-model="form.organisationProfile.website" :label="t('client.basicInfoStep.website')" placeholder="example.com" :error="errors.website" />
      </div>
    </FormSection>

    <FormSection :title="t('client.basicInfoStep.contactDetails')">
      <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
        <TextInput
          v-model="form.mobile"
          :label="t('client.basicInfoStep.mobileNumber')"
          placeholder="+965 5XXX XXXX"
          required
          maxlength="13"
          :error="errors.mobile"
        />
        <TextInput v-model="form.email" :label="t('client.basicInfoStep.emailAddress')" type="email" required :error="errors.email" />
        <SelectBox
          v-model="form.communicationPreference.preferredLanguage"
          :label="t('client.basicInfoStep.preferredLanguage')"
          :options="languageOptions"
        />
      </div>
    </FormSection>

    <FormSection :title="t('client.basicInfoStep.assignment')" :description="t('client.basicInfoStep.assignmentDescription')">
      <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
        <SelectBox v-model="form.accountManagerId" :label="t('client.basicInfoStep.accountManager')" required :options="accountManagerOptions" :error="errors.accountManagerId" />
      </div>
    </FormSection>
  </div>
</template>
