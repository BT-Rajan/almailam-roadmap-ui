<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import ClientBasicInfoStep from '@/components/client/ClientBasicInfoStep.vue'
import ClientConsentStep from '@/components/client/ClientConsentStep.vue'
import ClientContactAddressStep from '@/components/client/ClientContactAddressStep.vue'
import ClientIdentificationStep from '@/components/client/ClientIdentificationStep.vue'
import ClientReviewStep from '@/components/client/ClientReviewStep.vue'
import FormActionBar from '@/components/common/FormActionBar.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import Stepper from '@/components/common/Stepper.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useClientStore } from '@/stores/clientStore'
import { useToastStore } from '@/stores/toastStore'
import type {
  Client,
  ClientAddress,
  ClientConsent,
  ClientContact,
  ClientDocument,
  ClientDuplicateMatch,
  ClientIdentification,
} from '@/types/Client'
import { createEmptyClientWizardForm } from '@/types/ClientWizard'
import { calculateOnboardingState, generateClientCode, getClientDisplayName } from '@/utils/clientHelpers'

const router = useRouter()
const clientStore = useClientStore()
const toastStore = useToastStore()

const WIZARD_STEPS = [
  { label: 'Client Type' },
  { label: 'Contacts & Address' },
  { label: 'Identification' },
  { label: 'Consent' },
  { label: 'Review & Confirm' },
]

const currentStep = ref(0)
const isSubmitting = ref(false)
const form = ref(createEmptyClientWizardForm())
const duplicates = ref<ClientDuplicateMatch[]>([])
let duplicateCheckTimeout: ReturnType<typeof setTimeout> | undefined

async function checkForDuplicates(): Promise<void> {
  const name = form.value.clientType === 'Individual' ? form.value.individualProfile.fullLegalName : form.value.organisationProfile.legalName
  if (!name && !form.value.mobile && !form.value.email) {
    duplicates.value = []
    return
  }
  duplicates.value = await clientStore.findDuplicates(name, form.value.mobile, form.value.email)
}

watch(
  () => [form.value.clientType, form.value.mobile, form.value.email, form.value.individualProfile.fullLegalName, form.value.organisationProfile.legalName],
  () => {
    if (duplicateCheckTimeout) clearTimeout(duplicateCheckTimeout)
    duplicateCheckTimeout = setTimeout(checkForDuplicates, 400)
  },
)

function viewDuplicate(clientId: string): void {
  router.push({ name: ROUTE_NAMES.CLIENT_WORKSPACE, params: { clientId } })
}

function goNext(): void {
  currentStep.value = Math.min(currentStep.value + 1, WIZARD_STEPS.length - 1)
}

function goBack(): void {
  currentStep.value = Math.max(currentStep.value - 1, 0)
}

function cancelWizard(): void {
  router.push({ name: ROUTE_NAMES.CLIENTS })
}

async function submitWizard(): Promise<void> {
  isSubmitting.value = true

  const code = generateClientCode(clientStore.clients.length)
  const isIndividual = form.value.clientType === 'Individual'
  const primaryContact = form.value.contacts[0]

  const client: Client = {
    id: code,
    code,
    clientType: form.value.clientType,
    companyName: isIndividual ? form.value.individualProfile.fullLegalName : form.value.organisationProfile.legalName,
    contactPerson: primaryContact?.name || (isIndividual ? form.value.individualProfile.fullLegalName : form.value.organisationProfile.legalName),
    mobile: form.value.mobile,
    email: form.value.email,
    city: form.value.city,
    status: 'Active',
    onboardingState: 'Under Review',
    createdDate: new Date().toISOString().slice(0, 10),
    individualProfile: isIndividual ? { ...form.value.individualProfile } : undefined,
    organisationProfile: !isIndividual ? { ...form.value.organisationProfile } : undefined,
    communicationPreference: { ...form.value.communicationPreference },
  }

  const documents: ClientDocument[] = form.value.hasUploadedFile
    ? [
        {
          id: `CDOC-${Date.now()}`,
          clientId: client.id,
          category: 'Identity Document',
          title: `${form.value.identification.documentType} - ${getClientDisplayName(client)}`,
          issueDate: form.value.identification.issueDate || undefined,
          expiryDate: form.value.identification.expiryDate || undefined,
          issuingAuthority: form.value.identification.issuingCountry,
          version: 1,
          verificationStatus: 'Pending',
          uploadedBy: 'You',
          uploadDate: new Date().toISOString(),
        },
      ]
    : []

  client.onboardingState = calculateOnboardingState(client, documents, [], Boolean(client.companyName && client.mobile))

  clientStore.addClient(client)

  form.value.contacts
    .filter((contact) => contact.name.trim().length > 0)
    .forEach((contact, index) => {
      const clientContact: ClientContact = {
        id: `CTC-${Date.now()}-${index}`,
        clientId: client.id,
        name: contact.name,
        contactType: contact.contactType,
        mobile: contact.mobile,
        email: contact.email,
        isAuthorisedRepresentative: contact.isAuthorisedRepresentative,
      }
      clientStore.addContact(clientContact)
    })

  if (form.value.address.city.trim().length > 0) {
    const address: ClientAddress = {
      id: `ADR-${Date.now()}`,
      clientId: client.id,
      addressType: form.value.address.addressType,
      country: form.value.address.country,
      state: form.value.address.state,
      city: form.value.address.city,
      area: form.value.address.area || undefined,
      street: form.value.address.street || undefined,
      building: form.value.address.building || undefined,
    }
    clientStore.addAddress(address)
  }

  if (form.value.identification.documentNumber.trim().length > 0) {
    const identification: ClientIdentification = {
      id: `IDN-${Date.now()}`,
      clientId: client.id,
      documentType: form.value.identification.documentType,
      documentNumber: form.value.identification.documentNumber,
      issueDate: form.value.identification.issueDate,
      expiryDate: form.value.identification.expiryDate,
      issuingCountry: form.value.identification.issuingCountry,
    }
    clientStore.addIdentification(identification)
  }

  documents.forEach((document) => clientStore.addDocument(document))

  Object.entries(form.value.consents)
    .filter(([, granted]) => granted)
    .forEach(([consentType]) => {
      const consent: ClientConsent = {
        id: `CNS-${Date.now()}-${consentType}`,
        clientId: client.id,
        consentType: consentType as ClientConsent['consentType'],
        version: 'v1.0',
        granted: true,
        dateTime: new Date().toISOString(),
        method: 'Onboarding wizard',
        recordedBy: 'You',
      }
      clientStore.recordConsent(consent)
    })

  toastStore.show('success', 'Client onboarded', `${getClientDisplayName(client)} was added as a reusable client profile.`)

  await router.push({ name: ROUTE_NAMES.CLIENT_WORKSPACE, params: { clientId: client.id } })
  isSubmitting.value = false
}
</script>

<template>
  <div class="flex flex-col gap-6 p-6">
    <PageHeader title="New Client Onboarding" subtitle="Collect, verify and confirm client information in a few steps." />

    <div class="rounded-xl border border-border-light bg-bg-card p-6">
      <Stepper :steps="WIZARD_STEPS" :current-step="currentStep" />

      <div class="mt-8">
        <ClientBasicInfoStep v-if="currentStep === 0" v-model="form" :duplicates="duplicates" @view-duplicate="viewDuplicate" />
        <ClientContactAddressStep v-else-if="currentStep === 1" v-model="form" />
        <ClientIdentificationStep v-else-if="currentStep === 2" v-model="form" />
        <ClientConsentStep v-else-if="currentStep === 3" v-model="form" />
        <ClientReviewStep v-else v-model="form" />
      </div>

      <div class="mt-8 flex items-center justify-between border-t border-border-light pt-4">
        <FormActionBar
          v-if="currentStep < WIZARD_STEPS.length - 1"
          cancel-label="Cancel"
          submit-label="Next"
          @cancel="currentStep === 0 ? cancelWizard() : goBack()"
          @submit="goNext"
        />
        <FormActionBar
          v-else
          cancel-label="Back"
          submit-label="Complete Onboarding"
          :loading="isSubmitting"
          @cancel="goBack"
          @submit="submitWizard"
        />
      </div>
    </div>
  </div>
</template>
