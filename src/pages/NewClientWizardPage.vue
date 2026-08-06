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
import type { ClientDuplicateMatch } from '@/types/Client'
import { createEmptyClientWizardForm } from '@/types/ClientWizard'
import { getClientDisplayName } from '@/utils/clientHelpers'

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

  try {
    const isIndividual = form.value.clientType === 'Individual'
    const primaryContact = form.value.contacts[0]

    // Create the client first -- everything below depends on the real,
    // backend-assigned client id (previously this whole wizard generated
    // a fake id client-side and never called the backend at all, so
    // nothing survived a page refresh).
    const client = await clientStore.createClient({
      clientType: form.value.clientType,
      companyName: isIndividual ? form.value.individualProfile.fullLegalName : form.value.organisationProfile.legalName,
      contactPerson: primaryContact?.name || (isIndividual ? form.value.individualProfile.fullLegalName : form.value.organisationProfile.legalName),
      mobile: form.value.mobile,
      email: form.value.email,
      city: form.value.city,
      individualProfile: isIndividual ? { ...form.value.individualProfile } : undefined,
      organisationProfile: !isIndividual ? { ...form.value.organisationProfile } : undefined,
      communicationPreference: { ...form.value.communicationPreference },
    })

    const subRecordRequests: Promise<unknown>[] = []

    for (const contact of form.value.contacts.filter((c) => c.name.trim().length > 0)) {
      subRecordRequests.push(
        clientStore.createContact(client.id, {
          name: contact.name,
          contactType: contact.contactType,
          mobile: contact.mobile,
          email: contact.email,
          isAuthorisedRepresentative: contact.isAuthorisedRepresentative,
        }),
      )
    }

    if (form.value.address.city.trim().length > 0) {
      subRecordRequests.push(
        clientStore.createAddress(client.id, {
          addressType: form.value.address.addressType,
          country: form.value.address.country,
          state: form.value.address.state,
          city: form.value.address.city,
          area: form.value.address.area || undefined,
          street: form.value.address.street || undefined,
          building: form.value.address.building || undefined,
        }),
      )
    }

    if (form.value.identification.documentNumber.trim().length > 0) {
      subRecordRequests.push(
        clientStore.createIdentification(client.id, {
          documentType: form.value.identification.documentType,
          documentNumber: form.value.identification.documentNumber,
          issueDate: form.value.identification.issueDate,
          expiryDate: form.value.identification.expiryDate,
          issuingCountry: form.value.identification.issuingCountry,
        }),
      )
    }

    if (form.value.hasUploadedFile) {
      subRecordRequests.push(
        clientStore.createDocument(client.id, {
          category: 'Identity Document',
          title: `${form.value.identification.documentType} - ${getClientDisplayName(client)}`,
          issueDate: form.value.identification.issueDate || undefined,
          expiryDate: form.value.identification.expiryDate || undefined,
          issuingAuthority: form.value.identification.issuingCountry,
        }),
      )
    }

    for (const [consentType, granted] of Object.entries(form.value.consents)) {
      if (!granted) continue
      subRecordRequests.push(
        clientStore.createConsent(client.id, {
          consentType: consentType as 'Process Personal Information' | 'Electronic Communication' | 'Receive Notifications' | 'Process Documents',
          version: 'v1.0',
          granted: true,
          method: 'Onboarding wizard',
        }),
      )
    }

    // Sub-records are independent of one another, so run them concurrently
    // once the client itself exists. A failure here is surfaced but
    // doesn't roll back the client -- it already exists in the system and
    // is visible/editable from its workspace page.
    const results = await Promise.allSettled(subRecordRequests)
    const failures = results.filter((result) => result.status === 'rejected').length

    if (failures > 0) {
      toastStore.show(
        'error',
        'Client onboarded with some issues',
        `${getClientDisplayName(client)} was created, but ${failures} supporting record${failures === 1 ? '' : 's'} failed to save. You can add them from the client's workspace.`,
      )
    } else {
      toastStore.show('success', 'Client onboarded', `${getClientDisplayName(client)} was added as a reusable client profile.`)
    }

    await router.push({ name: ROUTE_NAMES.CLIENT_WORKSPACE, params: { clientId: client.id } })
  } catch {
    toastStore.show('error', 'Failed to onboard client', 'Please check the form and try again.')
  } finally {
    isSubmitting.value = false
  }
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
