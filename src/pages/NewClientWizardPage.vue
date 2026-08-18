<script setup lang="ts">
import { computed, defineAsyncComponent, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import FormActionBar from '@/components/common/FormActionBar.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import Stepper from '@/components/common/Stepper.vue'

// Lazy-loaded: only one wizard step is visible at a time.
const ClientBasicInfoStep = defineAsyncComponent(() => import('@/components/client/ClientBasicInfoStep.vue'))
const ClientConsentStep = defineAsyncComponent(() => import('@/components/client/ClientConsentStep.vue'))
const ClientContactAddressStep = defineAsyncComponent(() => import('@/components/client/ClientContactAddressStep.vue'))
const ClientIdentificationStep = defineAsyncComponent(() => import('@/components/client/ClientIdentificationStep.vue'))
const ClientReviewStep = defineAsyncComponent(() => import('@/components/client/ClientReviewStep.vue'))
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useClientStore } from '@/stores/clientStore'
import { useToastStore } from '@/stores/toastStore'
import type { Client, ClientDuplicateMatch } from '@/types/Client'
import { createEmptyClientWizardForm } from '@/types/ClientWizard'
import { getClientDisplayName } from '@/utils/clientHelpers'
import { hasErrors, validateAddress, validateBasicInfo, validateConsent, validateContacts, validateIdentification } from '@/utils/clientValidation'
import type { FieldErrors } from '@/utils/clientValidation'

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

// Shown after a successful create so the user gets an explicit
// confirmation (with the assigned client code) instead of a toast that
// can be missed while the page is already navigating away.
const showConfirmation = ref(false)
const createdClient = ref<Client | null>(null)
const confirmationNote = ref('')

async function checkForDuplicates(): Promise<void> {
  const name = form.value.clientType === 'Individual' ? form.value.individualProfile.fullLegalName : form.value.organisationProfile.legalName
  const registrationNumber = form.value.clientType === 'Individual' ? undefined : form.value.organisationProfile.registrationNumber
  if (!name && !form.value.mobile && !form.value.email && !registrationNumber) {
    duplicates.value = []
    return
  }
  duplicates.value = await clientStore.findDuplicates(name, form.value.mobile, form.value.email, registrationNumber)
}

watch(
  () => [
    form.value.clientType,
    form.value.mobile,
    form.value.email,
    form.value.individualProfile.fullLegalName,
    form.value.organisationProfile.legalName,
    form.value.organisationProfile.registrationNumber,
  ],
  () => {
    if (duplicateCheckTimeout) clearTimeout(duplicateCheckTimeout)
    duplicateCheckTimeout = setTimeout(checkForDuplicates, 400)
  },
)

function viewDuplicate(clientId: string): void {
  router.push({ name: ROUTE_NAMES.CLIENT_WORKSPACE, params: { clientId } })
}

// Per-step validation, mirroring exactly what the backend requires (see
// src/utils/clientValidation.ts) so the wizard can't be walked to the end,
// or submitted, with a payload the API will reject -- and so problems are
// shown inline on the relevant field rather than only as a toast at the end.
const basicInfoErrors = computed<FieldErrors>(() => validateBasicInfo(form.value))
const contactsValidation = computed(() => validateContacts(form.value.contacts))
const addressErrors = computed<FieldErrors>(() => validateAddress(form.value.address))
const identificationErrors = computed<FieldErrors>(() => validateIdentification(form.value.identification))
const consentErrors = computed<FieldErrors>(() => validateConsent(form.value.consents))

const contactsStepHasErrors = computed(
  () =>
    contactsValidation.value.rowErrors.some((row) => hasErrors(row)) ||
    Boolean(contactsValidation.value.formError) ||
    hasErrors(addressErrors.value),
)

function stepHasErrors(step: number): boolean {
  if (step === 0) return hasErrors(basicInfoErrors.value)
  if (step === 1) return contactsStepHasErrors.value
  if (step === 2) return hasErrors(identificationErrors.value)
  if (step === 3) return hasErrors(consentErrors.value)
  return false
}

const STEP_LABELS = ['Client Type', 'Contacts & Address', 'Identification', 'Consent']

function goNext(): void {
  if (stepHasErrors(currentStep.value)) {
    toastStore.show(
      'error',
      'Please fix the highlighted fields',
      `Some fields under "${STEP_LABELS[currentStep.value]}" need attention before continuing.`,
    )
    return
  }
  currentStep.value = Math.min(currentStep.value + 1, WIZARD_STEPS.length - 1)
}

function goBack(): void {
  currentStep.value = Math.max(currentStep.value - 1, 0)
}

function cancelWizard(): void {
  router.push({ name: ROUTE_NAMES.CLIENTS })
}

// Contacts touched enough to be submitted -- must match
// validateContacts()'s definition of "touched" exactly, or a row could
// pass validation as blank/skippable but still get submitted (or vice
// versa).
function isContactTouched(contact: (typeof form.value.contacts)[number]): boolean {
  return Boolean(contact.name.trim() || contact.mobile.trim() || contact.email.trim())
}

async function submitWizard(): Promise<void> {
  // Re-validate every step, not just the current one -- someone could
  // have gone back and broken an earlier step, or jumped here via the
  // stepper. This is the final gate before anything reaches the backend.
  const invalidStep = [0, 1, 2, 3].find((step) => stepHasErrors(step))
  if (invalidStep !== undefined) {
    toastStore.show(
      'error',
      'Please fix the highlighted fields',
      `Some fields under "${STEP_LABELS[invalidStep]}" need attention before this client can be onboarded.`,
    )
    currentStep.value = invalidStep
    return
  }

  isSubmitting.value = true

  try {
    const isIndividual = form.value.clientType === 'Individual'
    const primaryContact = form.value.contacts.find(isContactTouched)

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
      accountManagerId: form.value.accountManagerId || undefined,
    })

    const subRecordRequests: Promise<unknown>[] = []

    for (const contact of form.value.contacts.filter(isContactTouched)) {
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

    if (form.value.identificationFile) {
      subRecordRequests.push(
        clientStore.createDocument(client.id, {
          category: 'Identity Document',
          title: `${form.value.identification.documentType} - ${getClientDisplayName(client)}`,
          issueDate: form.value.identification.issueDate || undefined,
          expiryDate: form.value.identification.expiryDate || undefined,
          issuingAuthority: form.value.identification.issuingCountry,
          file: form.value.identificationFile,
        }),
      )
    }

    // Every consent type gets an explicit recorded decision -- granted or
    // declined -- rather than only recording the ones the client agreed
    // to. A missing record and a recorded "no" mean different things for
    // compliance purposes, so silently skipping declines was a real gap.
    for (const [consentType, granted] of Object.entries(form.value.consents)) {
      subRecordRequests.push(
        clientStore.createConsent(client.id, {
          consentType: consentType as 'Process Personal Information' | 'Electronic Communication' | 'Receive Notifications' | 'Process Documents',
          version: 'v1.0',
          granted,
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
      confirmationNote.value = `but ${failures} supporting record${failures === 1 ? '' : 's'} failed to save. You can add them from the client's workspace.`
      toastStore.show(
        'error',
        'Client onboarded with some issues',
        `${getClientDisplayName(client)} was created, but ${failures} supporting record${failures === 1 ? '' : 's'} failed to save. You can add them from the client's workspace.`,
      )
    } else {
      confirmationNote.value = ''
      toastStore.show('success', 'Client onboarded', `${getClientDisplayName(client)} was added as a reusable client profile.`)
    }

    createdClient.value = client
    showConfirmation.value = true
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please check the form and try again.'
    toastStore.show('error', 'Failed to onboard client', detail)
  } finally {
    isSubmitting.value = false
  }
}

function goToCreatedClient(): void {
  if (!createdClient.value) return
  showConfirmation.value = false
  router.push({ name: ROUTE_NAMES.CLIENT_WORKSPACE, params: { clientId: createdClient.value.id } })
}
</script>

<template>
  <div class="flex flex-col gap-6 p-6">
    <PageHeader title="New Client Onboarding" subtitle="Collect, verify and confirm client information in a few steps." />

    <div class="rounded-xl border border-border-light bg-bg-card p-6">
      <Stepper :steps="WIZARD_STEPS" :current-step="currentStep" />

      <div class="mt-8">
        <ClientBasicInfoStep v-if="currentStep === 0" v-model="form" :duplicates="duplicates" :errors="basicInfoErrors" @view-duplicate="viewDuplicate" />
        <ClientContactAddressStep
          v-else-if="currentStep === 1"
          v-model="form"
          :contact-errors="contactsValidation.rowErrors"
          :contacts-form-error="contactsValidation.formError"
          :address-errors="addressErrors"
        />
        <ClientIdentificationStep v-else-if="currentStep === 2" v-model="form" :errors="identificationErrors" />
        <ClientConsentStep v-else-if="currentStep === 3" v-model="form" :errors="consentErrors" />
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

    <BaseDialog :model-value="showConfirmation" title="Client Onboarded" size="sm" :closable="false">
      <p class="text-sm text-neutral-600">
        <strong>{{ createdClient ? getClientDisplayName(createdClient) : '' }}</strong>
        was successfully created as client
        <strong>{{ createdClient?.code }}</strong>.
        <span v-if="confirmationNote"> {{ confirmationNote }}</span>
      </p>

      <template #footer>
        <BaseButton variant="primary" @click="goToCreatedClient">View Client Workspace</BaseButton>
      </template>
    </BaseDialog>
  </div>
</template>
